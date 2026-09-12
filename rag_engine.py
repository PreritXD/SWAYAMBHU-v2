"""
SWAYAMBHU v2 - Grounded RAG Engine & LLM Orchestration

Hard constraint: "Grounded, cited, refuses to guess".
Strictly preserves spiritual domain terminology (Naam Aparadh, Dosh Darshan, Mansik Paap,
Sadhana, Naam Jap, Ekantik Vartalaap, Ashraya) as-is in Hindi without secular translations.

Pipeline:
1. Fast-Path Adversarial / Off-Topic Filter (<1ms regex, zero API calls).
2. Multi-turn Contextual Query Rewriter (pronoun resolution -> self-contained query).
3. Query Normalization (Hinglish -> Devanagari via indic-transliteration + spiritual lexicon).
4. Vector Retrieval with is_duplicate = False filter.
5. MMR Diversity Re-ranking.
6. Strictly Grounded LLM Prompting with Groq -> OpenRouter -> OpenAI -> Ollama fallback chain.
7. Citation Assembly with exact YouTube timestamp links and source channel attribution.
8. Telemetry Logging to query_logs.
"""

import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple
import httpx

from config import AppEnvironment, settings
from indexer import (
    CrossEncoderReRanker,
    EmbeddingGenerator,
    get_vector_store,
    is_hinglish_query,
    maximal_marginal_relevance,
    normalize_hinglish_to_devanagari,
)
from schema import (
    ChatDisclaimer,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatRole,
    Citation,
    CrossChannelAlias,
    SourceChannel,
)

logger = logging.getLogger("swayambhu.rag_engine")

# ============================================================================
# 1. Reverent Disclaimer & Refusal Text
# ============================================================================

STANDARD_DISCLAIMER_TEXT = (
    "यह उत्तर पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के सार्वजनिक रूप से उपलब्ध सत्संग वचनों "
    "पर आधारित एक एआई-संवर्धित शोध प्रणाली है, और यह आश्रम अथवा पूज्य महाराज जी का आधिकारिक मंच नहीं है। "
    "किसी भी संशय की स्थिति में दिए गए मूल वीडियो प्रमाण को देखकर ही प्रमाणिक समझ प्राप्त करें।"
)

REVERENT_REFUSAL_UNGROUNDED = (
    "जय श्री राधे। पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के उपलब्ध सत्संग वचनों में इस विशिष्ट "
    "प्रश्न का कोई प्रत्यक्ष अथवा स्पष्ट उल्लेख प्राप्त नहीं होता है। \n\n"
    "यह व्यवस्था केवल पूज्य महाराज जी द्वारा स्वयं कहे गए प्रमाणिक वचनों के आधार पर ही उत्तर देने के लिए "
    "प्रतिबद्ध है और अपनी ओर से कोई अनुमान अथवा सामान्य उत्तर नहीं देती। कृपया नाम जप, भक्ति, मन के भाव, "
    "अथवा साधना से संबंधित कोई अन्य प्रश्न पूछें।"
)

REVERENT_REFUSAL_OFF_TOPIC = (
    "जय श्री राधे। यह प्रश्न पूज्य महाराज जी के आध्यात्मिक सत्संग वचनों की परिधि से बाहर है। "
    "यह सेवा केवल पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के प्रवचनों, नाम जप, भगवद भक्ति, "
    "एकांतिक वार्तालाप और साधना संबंधी शंकाओं के समाधान हेतु समर्पित है।"
)

# ============================================================================
# 2. Tier-1 Fast Deterministic Adversarial & Off-Topic Filter
# ============================================================================

JAILBREAK_PATTERNS = [
    r"ignore\s+(?:all\s+|previous\s+|the\s+)?instructions",
    r"system\s+prompt",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"dan\s+mode",
    r"jailbreak",
    r"act\s+as\s+(?:a\s+|an\s+)?(?:unfiltered|evil|developer|linux|terminal|bot)",
    r"pretend\s+you\s+(?:are|can)",
    r"bypass\s+(?:safety|rules|restrictions)",
    r"drop\s+table",
    r"select\s+.*from\s+",
]

OFF_TOPIC_PATTERNS = [
    r"\b(?:python|javascript|typescript|c\+\+|html|css|sql|docker|kubernetes)\b",
    r"\b(?:write\s+code|debug\s+code|programming|algorithm|quicksort)\b",
    r"\b(?:crypto|bitcoin|ethereum|forex|stock\s+market|investing|nifty|sensex)\b",
    r"\b(?:weather\s+forecast|football|cricket|nba|fifa|score)\b",
    r"\b(?:election|politics|politician|prime\s+minister|president)\b",
    r"\b(?:quantum|physics|black\s+hole|quarks|relativity)\b",
    r"(?:क्वांटम|भौतिकी|ब्लैक\s*होल)",
]

COMPILED_JAILBREAK = re.compile("|".join(JAILBREAK_PATTERNS), re.IGNORECASE)
COMPILED_OFF_TOPIC = re.compile("|".join(OFF_TOPIC_PATTERNS), re.IGNORECASE)


def evaluate_fast_path_filter(query: str) -> Optional[str]:
    """
    Tier-1 Fast Filter (<1ms regex, 0 LLM cost).
    Returns refusal message if query matches jailbreak or obvious off-topic patterns.
    """
    if not query or len(query.strip()) < 2:
        return REVERENT_REFUSAL_OFF_TOPIC

    if COMPILED_JAILBREAK.search(query):
        logger.warning(f"Adversarial jailbreak attempt detected: {query[:80]}")
        return REVERENT_REFUSAL_OFF_TOPIC

    if COMPILED_OFF_TOPIC.search(query):
        logger.info(f"Off-topic query intercepted by fast-path: {query[:80]}")
        return REVERENT_REFUSAL_OFF_TOPIC

    return None


def sanitize_answer(text: str) -> str:
    """
    Ensure the assistant answer never repeats or echoes the user's question,
    such as:
    **प्रश्न:** ...
    **Question:** ...
    ---
    Strips any leading echoed question blocks so the response starts directly
    with the structured section headings (e.g. ## १. परिस्थिति... or ### १. ...).
    """
    if not text:
        return text
    cleaned = text.strip()

    # 1. Match leading question block with separator, e.g.:
    # **प्रश्न:** ... \n\n--- or **Question:** ... \n\n--- or प्रश्न: ...
    pattern = r"^\s*(?:\*{0,2}(?:प्रश्न|Question|साधक का प्रश्न)\s*[:：]\*{0,2})[\s\S]*?(?:--{2,}\s*|\n{2,})(?=(?:#{1,3}\s*[१-५1-5]|\b[१-५1-5]\.|\S))"
    cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    # 2. Also strip any single-line echoed question with quotation marks
    leading_q_line = r"^\s*(?:\*{0,2}(?:प्रश्न|Question|साधक का प्रश्न)\s*[:：]\*{0,2})\s*[\"“'‘][^\"”'’\n]+[\"”'’]\s*(?:--{2,}\s*|\n+)"
    cleaned = re.sub(leading_q_line, "", cleaned, flags=re.IGNORECASE).strip()

    # 3. Strip any isolated leading horizontal rule divider
    cleaned = re.sub(r"^\s*--{2,}\s*\n+", "", cleaned).strip()

    return cleaned


CHANNEL_CITATION_MAP: Dict[str, str] = {
    # Bhajan Marg
    "bhajan marg": "bhajan_marg",
    "bhajan_marg": "bhajan_marg",
    "bhajanmarg": "bhajan_marg",
    "भजन मार्ग": "bhajan_marg",
    "भजनमार्ग": "bhajan_marg",
    "भजन": "bhajan_marg",

    # Sadhan Path
    "sadhan path": "sadhan_path",
    "sadhan_path": "sadhan_path",
    "sadhanpath": "sadhan_path",
    "साधन पथ": "sadhan_path",
    "साधनपथ": "sadhan_path",
    "साधन": "sadhan_path",

    # Vrindavan Ras
    "vrindavan ras": "vrindavan_ras",
    "vrindavan ras mahima": "vrindavan_ras",
    "vrindavan_ras": "vrindavan_ras",
    "वृन्दावन रस": "vrindavan_ras",
    "वृंदावन रस": "vrindavan_ras",
    "वृन्दावन रस महिमा": "vrindavan_ras",
    "वृंदावन रस महिमा": "vrindavan_ras",
    "वृन्दावन": "vrindavan_ras",
    "वृंदावन": "vrindavan_ras",

    # Shri Hit Radha Kripa
    "shri hit radha kripa": "shri_hit_radha_kripa",
    "shrihit radha kripa": "shri_hit_radha_kripa",
    "radha kripa": "shri_hit_radha_kripa",
    "shri_hit_radha_kripa": "shri_hit_radha_kripa",
    "श्री हित राधा कृपा": "shri_hit_radha_kripa",
    "श्रीहित राधा कृपा": "shri_hit_radha_kripa",
    "राधा कृपा": "shri_hit_radha_kripa",
}


def parse_timestamp_to_seconds(ts: str) -> Optional[int]:
    """Convert mm:ss or hh:mm:ss string to total integer seconds."""
    if not ts:
        return None
    parts = ts.strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, TypeError):
        return None
    return None


def normalize_spacing_and_dashes(s: str) -> str:
    """Normalize unicode spaces, narrow no-break spaces, and unicode dashes for robust matching."""
    s = re.sub(r"[\u00a0\u202f\u2000-\u200b\ufeff]", " ", s)
    s = re.sub(r"[\u2010-\u2015\u2212]", "-", s)
    return s


def linkify_citations(text: str, citations: List[Any]) -> str:
    """
    Transforms plain text citations like:
      [Bhajan Marg • 22:14] or [भजन मार्ग • 22:14] or (Sadhan Path • 12:30) or **Bhajan Marg • 07:50-08:41**
    into clickable markdown video hyperlinks:
      [Bhajan Marg • 22:14](https://youtu.be/VIDEO_ID?t=1334)
    Skips citations that are already markdown links [text](url).
    """
    if not text or not citations:
        return text

    def _make_link(inner_raw: str) -> Optional[str]:
        inner_norm = normalize_spacing_and_dashes(inner_raw).strip()
        trailing_punct = ""
        if inner_norm.endswith((".", ",", ";", ":", "!")):
            trailing_punct = inner_norm[-1]
            inner_norm = inner_norm[:-1].strip()

        # Find timestamp
        time_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", inner_norm)
        if not time_match:
            return None

        seconds = parse_timestamp_to_seconds(time_match.group(1))

        # Detect channel
        channel_key = None
        lower_inner = inner_norm.lower()
        for k, v in CHANNEL_CITATION_MAP.items():
            if k in lower_inner:
                channel_key = v
                break

        def _get_ch(c):
            ch = getattr(c, "channel", None) or (c.get("channel") if isinstance(c, dict) else None)
            return getattr(ch, "value", str(ch)) if ch else ""

        def _get_sec(c):
            return getattr(c, "start_sec", None) if hasattr(c, "start_sec") else (c.get("start_sec", 0) if isinstance(c, dict) else 0)

        def _get_vid(c):
            return getattr(c, "video_id", None) if hasattr(c, "video_id") else (c.get("video_id", "") if isinstance(c, dict) else "")

        def _get_url(c):
            return getattr(c, "url", None) if hasattr(c, "url") else (c.get("url", "") if isinstance(c, dict) else "")

        best_cit = None
        if channel_key:
            matching_channel_cits = [c for c in citations if _get_ch(c) == channel_key]
            if matching_channel_cits:
                if seconds is not None:
                    best_cit = min(matching_channel_cits, key=lambda c: abs((_get_sec(c) or 0) - seconds))
                else:
                    best_cit = matching_channel_cits[0]

        if not best_cit and citations:
            if seconds is not None:
                best_cit = min(citations, key=lambda c: abs((_get_sec(c) or 0) - seconds))
            else:
                best_cit = citations[0]

        if best_cit:
            vid = _get_vid(best_cit)
            if vid and seconds is not None:
                url = f"https://youtu.be/{vid}?t={seconds}"
            else:
                url = _get_url(best_cit) or f"https://youtu.be/{vid}"
            clean_display = inner_raw.strip()
            if clean_display.endswith((".", ",", ";", ":", "!")):
                clean_display = clean_display[:-1].strip()
            return f"[{clean_display}]({url}){trailing_punct}"

        return None

    # 1. Match bracketed / parenthesized citations: [Bhajan Marg • 22:14] or (Sadhan Path • 12:30)
    bracket_pat = re.compile(r"(\[|\()(?P<inner>[^\]\)\r\n]+?(\d{1,2}:\d{2}(?::\d{2})?)[^\]\)\r\n]*?)(\]|\))(?!\s*\()")

    def _replace_bracket(m: re.Match) -> str:
        inner = m.group("inner")
        link = _make_link(inner)
        return link if link else m.group(0)

    text = bracket_pat.sub(_replace_bracket, text)

    # 2. Match bold channel citations (common in markdown tables): **Bhajan Marg • 07:50-08:41**
    bold_pat = re.compile(
        r"\*\*(?P<inner>(?:Bhajan|भजन|Sadhan|साधन|Vrindavan|वृन्दावन|वृंदावन|Shri\s*Hit|श्री\s*हित|राधा)[^*\r\n]+?(\d{1,2}:\d{2}(?::\d{2})?)[^*\r\n]*?)\*\*(?!\s*\()",
        re.IGNORECASE,
    )

    def _replace_bold(m: re.Match) -> str:
        inner = m.group("inner")
        link = _make_link(inner)
        return f"**{link}**" if link else m.group(0)

    text = bold_pat.sub(_replace_bold, text)

    return text


# ============================================================================
# 2.5 Case-Based Situational Taxonomy & Spiritual Principle Expansion
# ============================================================================

CASE_BASED_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "INTRUSIVE_THOUGHTS_SADHANA": {
        "title": "साधना में काम-वासना, क्रोध व मानसिक विक्षेप",
        "patterns": [
            r"(?:काम\s*वासना|वासना|गंदे\s*विचार|गंदे\s*ख्याल|अश्लील|हस्तमैथुन|वीर्य|ब्रह्मचर्य|मानसिक\s*पाप|बुरे\s*विचार)",
            r"(?:काम\s*सताता|वासना\s*सताती|मन\s*भटकता|मन\s*में\s*गंदे|क्रोध\s*सताता)",
            r"(?:जप\s*में\s*मन\s*नहीं|साधना\s*में\s*मन\s*नहीं|अशुद्ध\s*विचार)",
        ],
        "spiritual_principles": [
            "काम वासना पर विजय",
            "मानसिक पाप",
            "मन के विकार",
            "नाम जप का बल",
            "इंद्रिय संयम",
            "भगवद आश्रय",
            "मन को साक्षी भाव से देखना",
            "हताश न होना",
            "दृढ़ संकल्प",
        ],
        "expansion_search_query": "काम वासना पर विजय गंदे विचार मानसिक पाप काम सताए ब्रह्मचर्य नाम जप का बल मन के विकार इंद्रिय संयम साक्षी भाव आश्रय",
    },
    "BHAKTI_OPPOSITION": {
        "title": "पारिवारिक विरोध में भक्ति व साधना",
        "patterns": [
            r"(?:घरवाले|परिवार|माता-पिता|ससुराल|पति|सास).*(?:भक्ति|भजन|पूजा|माला|मंदिर|तिलक).*(?:विरोध|मना|रोक|टोक)",
            r"(?:भक्ति\s*का\s*विरोध|भजन\s*का\s*विरोध|माला\s*फेरने\s*से\s*मना|पूजा\s*करने\s*से\s*रोक)",
        ],
        "spiritual_principles": [
            "चुपचाप गुप्त भजन",
            "परिजनों का आदर व सेवा",
            "सेवा द्वारा हृदय परिवर्तन",
            "विरोध में भी धैर्य",
            "अनन्य निष्ठा",
            "कलह न बढ़ाना",
            "मन ही मन नाम जप",
        ],
        "expansion_search_query": "घरवाले भक्ति का विरोध करते हैं परिवार में भजन का विरोध गुप्त भजन परिजनों का आदर व सेवा धैर्य अनन्य निष्ठा मन ही मन जप",
    },
    "BUSINESS_ETHICS": {
        "title": "व्यापार, आजीविका व सत्य आचरण (झूठ, बेईमानी, कपट)",
        "patterns": [
            r"(?:व्यापार|दुकान|दुकानदार|धंधा|कारोबार|नौकरी|व्यापारी|ग्राहकी?|ऑफिस).*(?:झूठ|सत्य|असत्य|बेईमानी|कपट|छल|घूस|रिश्वत|ठग|धोखा)",
            r"(?:झूठ\s*बोलना\s*पड़ता|व्यापार\s*में\s*झूठ|दुकान\s*में\s*झूठ|धंधे\s*में\s*सच|बेईमानी\s*किए\s*बिना)",
        ],
        "spiritual_principles": [
            "सत्य आचरण",
            "धर्मपूर्वक आजीविका",
            "बेईमानी से पतन",
            "प्रारब्ध का धन",
            "असत्य भाषण का त्याग",
            "लोभ त्याग",
            "ईमानदारी",
            "जो भाग्य में है वही मिलेगा",
        ],
        "expansion_search_query": "व्यापार में झूठ बोलना दुकान में सत्य आचरण धर्मपूर्वक आजीविका बेईमानी असत्य भाषण प्रारब्ध का धन ईमानदारी लोभ त्याग",
    },
    "DOMESTIC_CONFLICT": {
        "title": "पारिवारिक व गृहस्थ प्रतिकूलता (सास-बहू, पति-पत्नी, कटु वचन व ताने)",
        "patterns": [
            r"(?:सास|ससुर|बहू|ननद|भाभी|देवर|पति|पत्नी|ससुराल|मायके).*(?:ताने|ताना|झगड़ा|क्लेश|लड़ाई|गाली|अपमान|सता|कष्ट|विवाद|मारपीट)",
            r"(?:ताने|ताना|झगड़ा|क्लेश|लड़ाई|गाली|अपमान|सता|कष्ट|विवाद|मारपीट).*(?:सास|ससुर|बहू|ननद|भाभी|देवर|पति|पत्नी|ससुराल|मायके)",
            r"(?:ताने\s*मारती|ताने\s*देती|सास.*बहू|घर\s*में\s*कलह|पति.*पत्नी.*विवाद)",
        ],
        "spiritual_principles": [
            "प्रतिकूलता सहना",
            "प्रारब्ध भोग",
            "कटु वचन सहने का फल",
            "पर-दोष अदर्शन",
            "मौन",
            "वाणी संयम",
            "सहनशीलता",
            "गृहस्थ धर्म",
            "निंदा सहने से पाप नाश",
        ],
        "expansion_search_query": "प्रतिकूलता सहना प्रारब्ध भोग सास के ताने कटु वचन सहने का फल मौन वाणी संयम सहनशीलता गृहस्थ धर्म निंदा सहने से पाप नाश",
    },
    "INSULT_BETRAYAL": {
        "title": "अपमान, विश्वासघात, निंदा व लोक-लाज",
        "patterns": [
            r"(?:अपमान|बेइज्जती|धोखा|विश्वासघात|नीचा दिखा|हंसी उड़ा|खिल्ली|धिक्कार)",
            r"(?:निंदा|चुगली|पीठ\s*पीछे\s*बुराई|लोग\s*ताने\s*मारते|लोग\s*बुरा\s*कहते)",
        ],
        "spiritual_principles": [
            "अपमान सहना",
            "निंदा करने वाले का उपकार",
            "प्रारब्ध का ऋण",
            "द्वेष न करना",
            "क्षमा भाव",
            "समता",
            "मान-बड़ाई का त्याग",
            "कटु वचन अमृत समान",
        ],
        "expansion_search_query": "अपमान सहना निंदा करने वाले का उपकार प्रारब्ध का ऋण द्वेष न करना क्षमा भाव कटु वचन सहना मान बड़ाई त्याग समता",
    },
    "BEREAVEMENT_SUFFERING": {
        "title": "शोक, मृत्यु, गंभीर रोग व प्रारब्ध कष्ट",
        "patterns": [
            r"(?:मृत्यु|देहांत|निधन|मर\s*गए|चले\s*गए|शोक|वियोग|रो\s*रो\s*कर)",
            r"(?:असाध्य\s*रोग|कैंसर|गंभीर\s*बीमारी|भयंकर\s*दर्द|बहुत\s*कष्ट|दुख\s*संकट|भगवान\s*ने\s*ऐसा\s*क्यों)",
        ],
        "spiritual_principles": [
            "शरीर नश्वर आत्मा अविनाशी",
            "प्रारब्ध कष्ट",
            "भगवत् विधान में परम मंगल",
            "दुख में नाम जप",
            "अनन्य आश्रय",
            "शोक निवारण",
            "भगवान की मर्जी",
        ],
        "expansion_search_query": "मृत्यु शोक प्रारब्ध कष्ट असाध्य रोग भगवत् विधान में परम मंगल शरीर नश्वर आत्मा अविनाशी नाम जप अनन्य आश्रय",
    },
    "GENERAL_SITUATIONAL": {
        "title": "सामान्य परिस्थिति व धर्म-संकट",
        "patterns": [
            r"(?:मुझे\s*क्या\s*करना\s*चाहिए|ऐसी\s*स्थिति\s*में\s*क्या\s*करें|ऐसी\s*हालत\s*में)",
            r"(?:क्या\s*करूं|कैसे\s*निपटें|उलझन\s*में\s*हूं|मार्गदर्शन\s*करें|मार्ग\s*दिखाएं)",
        ],
        "spiritual_principles": [
            "प्रारब्ध का सामना",
            "धर्म और अधर्म का निर्णय",
            "नाम जप की शरण",
            "धैर्य",
            "श्री जी का आश्रय",
            "सत्संग वचन",
        ],
        "expansion_search_query": "विपरीत परिस्थिति में क्या करें प्रारब्ध भोग धर्म आचरण नाम जप का आश्रय धैर्य एकांतिक वार्तालाप",
    },
}


def analyze_case_based_query(query: str) -> Optional[Dict[str, Any]]:
    """
    Identifies whether a query is situational/case-based.
    If matched, returns categorization, target spiritual principles, and expanded search query.
    """
    if not query:
        return None

    cleaned_q = query.strip()
    for cat_key, cat_data in CASE_BASED_TAXONOMY.items():
        for pattern in cat_data["patterns"]:
            if re.search(pattern, cleaned_q, re.IGNORECASE):
                return {
                    "category": cat_key,
                    "title": cat_data["title"],
                    "spiritual_principles": cat_data["spiritual_principles"],
                    "expansion_search_query": cat_data["expansion_search_query"],
                }
    return None


# ============================================================================
# 3. System Prompt & Grounding Template
# ============================================================================

SYSTEM_PROMPT = """आप पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज (वृन्दावन) के पावन सत्संग वचनों, एकांतिक वार्तालापों एवं प्रवचनों पर आधारित एक पूर्णतः प्रामाणिक, निष्ठावान एवं शून्य-मतिभ्रम (Zero-Hallucination) आध्यात्मिक शोध प्रणाली (SWAYAMBHU v2) हैं।

================================================================================
१. सर्वोच्च अधिदेश एवं आरंभिक नियम (ZERO-PREAMBLE & NO QUESTION ECHOING)
================================================================================
• चरित्र शून्य (Character 0) से सीधे उत्तर प्रारंभ करें: किसी भी प्रकार की भूमिका, अभिवादन (उदा. "साधक जी", "प्रणाम"), प्रस्तावना ("नीचे उत्तर दिया गया है"), या साधक के प्रश्न का कोई भी हिस्सा कदापि न लिखें।
• ❌ प्रश्न दोहराना कठोरता से वर्जित (NEVER Echo the Question):
  - कभी भी '**प्रश्न:**', '**Question:**', साधक का वाक्य, या कोई भी उद्धरण चिह्न वाला प्रश्न ब्लॉक न लिखें। साधक का प्रश्न चैट यूआई (UI) में पहले से दिख रहा है।
• ✅ अनिवार्य प्रारंभिक बिंदु: आपका पहला अक्षर केवल और केवल खंड १ का मार्कडाउन शीर्षक (### १. ...) ही होना चाहिए।

================================================================================
२. प्रश्न वर्गीकरण एवं प्रत्यक्ष उत्तर नीति (INTENT-FIRST DIRECT ARCHITECTURE)
================================================================================
साधक के प्रश्न का प्रकार पहचानें और सर्वप्रथम उसी का सीधा, व्यावहारिक समाधान दें:

• प्रकार १: "विधि / कैसे करें" (HOW-TO / PROCESS) — [अति-महत्वपूर्ण क्रम]:
  - साधक ने साधना, नाम जप, ध्यान अथवा मन को वश में करने की व्यावहारिक विधि पूछी है।
  - खंड १ में केवल और केवल प्रत्यक्ष शारीरिक व मानसिक कार्य-विधि (Actionable Process) समझाएं — आसन, जिह्वा व तालु की स्थिति, श्वास के साथ नाम का प्रवाह, माला का उपयोग, तथा चलते-फिरते/कार्य करते समय जप की क्रियात्मक तकनीक।
  - ❌ कठोर निषेध: प्रश्न "नाम जप कैसे करें?" पर उत्तर की शुरुआत फल, लाभ या महिमा ("नाम जप से करोड़ों पाप कट जाते हैं...") से कदापि न करें। लाभ केवल खंड ३ में बताएं।
  - ✅ अपेक्षित: "पूज्य महाराज जी नाम जप की प्रत्यक्ष विधि बताते हैं: १. जिह्वा को हल्का मोड़कर तालु से लगाएं, २. श्वास के अंदर-बाहर प्रवाह के साथ नाम जोड़ें..."

• प्रकार २: "क्या है / परिभाषा" (WHAT IS):
  - सीधे उस पारमार्थिक तत्व (उदा. नाम अपराध, अनन्य आश्रय, सहचरी भाव) का सटीक आध्यात्मिक व व्यावहारिक स्वरूप स्पष्ट करें।

• प्रकार ३: "शंका / आध्यात्मिक संकट समाधान" (CRISIS / DOUBT RESOLUTION):
  - सीधे संकट के निवारण का आध्यात्मिक उपाय (धैर्य, भगवत्-शरणागति, वाणी पाठ, नाम कीर्तन) प्रस्तुत करें।

• प्रकार ४: "परिस्थिति-आधारित / केस-स्टडी" (CASE-BASED / SITUATIONAL DILEMMA):
  - साधक ने कोई पारिवारिक, सामाजिक, व्यापारिक अथवा मानसिक परिस्थिति प्रस्तुत की है (जैसे सास-बहू के ताने, पति-पत्नी विवाद, व्यापार/दुकान में झूठ बोलना, काम-वासना या अशुद्ध विचार सताना, सगे-संबंधियों द्वारा अपमान या विश्वासघात, घर में भक्ति का विरोध)।
  - ❌ **कठोर निषेध (STRICT ZERO-HALLUCINATION & ANTI-SECULAR BAN)**:
    - आधुनिक सांसारिक परामर्श (Therapy/Counseling), कानूनी सलाह, पुलिस/न्यायालय, झगड़ा करने, बदला लेने, या सांसारिक समझौते ('बैठकर बात सुलझाएं', 'रिश्ता तोड़ दें', 'एचआर से शिकायत करें') जैसी मनगढ़ंत सांसारिक बातें कदापि न कहें।
    - पूज्य महाराज जी की दृष्टि पूर्णतः आध्यात्मिक, कर्म-सिद्धांत और भगवत्-विधान पर आधारित है:
      १. **प्रारब्ध व कर्म-ऋण**: जो प्रतिकूलता सामने आई है, वह पूर्वकृत कर्मों का अकाट्य फल व ऋण-शोधन है।
      २. **प्रतिकूलता सहना व मौन**: ताने या कटु वचन सहने से जन्मों-जन्मों के पाप भस्म होते हैं; पलटकर उत्तर देने से नया कर्म-बंधन बनता है — अतः मौन रहकर सहन करें।
      ३. **पर-दोष अदर्शन**: सामने वाले में दोष न देखें, यह समझें कि वे केवल हमारे प्रारब्ध का निमित्त बने हैं; उनसे द्वेष न करें।
      ४. **अखंड नाम जप व आश्रय**: अंदर ही अंदर निरंतर नाम जप करते रहें और प्रिया-प्रियतम के अनन्य आश्रय में रहें।

================================================================================
३. शून्य मतिभ्रम एवं संदर्भ-बद्धता (STRICT CONTEXT GROUNDING & REFUSALS)
================================================================================
• आपका संपूर्ण ज्ञान केवल नीचे दिए गए सत्संग संदर्भों (Context Blocks) तक ही सीमित है।
• कठोर निषेध:
  - संदर्भ से बाहर की कोई काल्पनिक विधि, मनगढ़ंत मंत्र, अप्रमाणित तंत्र, या अपनी ओर से कोई संख्या (उदा. 1 लाख जप) न जोड़ें।
  - यदि संदर्भ में किसी बात का प्रत्यक्ष उल्लेख नहीं है, तो उस पर मन से कोई अटकल न लगाएं।
• अनुपलब्धता पर स्पष्ट व निष्कपट अस्वीकार (Exact Refusal Format):
  यदि संदर्भ में प्रश्न का उत्तर उपलब्ध नहीं है, तो केवल यही कहें:
  "जय श्री राधे। पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के उपलब्ध सत्संग वचनों में इस विशिष्ट विषय का प्रत्यक्ष उल्लेख प्राप्त नहीं होता है।"

================================================================================
४. भाषा अनुकूलन नियम (DYNAMIC BILINGUAL MATCHING)
================================================================================
• हिंदी / हिंग्लिश प्रश्न:
  उत्तर अत्यंत मधुर, मर्यादित, शुद्ध एवं प्रवाहमयी देवनागरी हिंदी में दें।
• अंग्रेजी (English) प्रश्न:
  उत्तर धाराप्रवाह, आदरयुक्त अंग्रेजी में दें, किंतु प्रमुख आध्यात्मिक पारिभाषिक शब्दों को कोष्ठक में देवनागरी सहित रखें (जैसे: Holy Name Chanting (*नाम जप*), Divine Shelter (*आश्रय*), Solitary Spiritual Discourse (*एकांतिक वार्तालाप*))।

================================================================================
५. बहु-सत्संग समन्वय एवं वीडियो हाइपरलिंक्स (CROSS-SATSANG CITATIONS & VIDEO HYPERLINKS)
================================================================================
• केवल किसी एक वीडियो तक सीमित न रहें; विभिन्न सत्संगों व चैनलों (भजन मार्ग, साधन पथ, वृन्दावन रस धारा, आदि) से प्राप्त मार्गदर्शन को जोड़कर एक सर्वांगीण उत्तर दें।
• उत्तर के प्रत्येक मुख्य विचार, व्यावहारिक चरण अथवा वचन के साथ संदर्भ को अनिवार्य रूप से सीधे वीडियो लिंक (Clickable Markdown Hyperlink) के रूप में उद्धृत करें, जैसे:
  - `[भजन मार्ग • 04:15](https://youtu.be/...?...t=...)`
  - `[Bhajan Marg • 22:14](https://youtu.be/...?...t=...)`
• संदर्भ ब्लॉक (Context Block) में प्रत्येक अंश के लिए दिए गए 'सीधा वीडियो लिंक' (Direct URL) का ही उपयोग करें। केवल सादा कोष्ठक न छोड़ें, लिंक अवश्य जोड़ें।

================================================================================
६. पवित्र मर्यादा व शब्दावली (SACRED REVERENCE)
================================================================================
• पारंपरिक आध्यात्मिक शब्दावली को अक्षुण्ण रखें: "नाम अपराध", "दोष दर्शन", "मानसिक पाप", "साधना", "नाम जप", "एकांतिक वार्तालाप", "आश्रय", "प्रिया-प्रियतम"।
• अत्यंत आदरयुक्त व करुणापूर्ण वाणी ("पूज्य महाराज जी आज्ञा करते हैं...", "श्री जी की अहेतुकी कृपा से...") का प्रयोग करें।

================================================================================
उत्तर का अनिवार्य ५-खंडीय मार्कडाउन प्रारूप (MANDATORY 5-PART MARKDOWN BLUEPRINTS)
================================================================================

[प्रारूप 'क'] सामान्य एवं साधन-विधि प्रश्नों हेतु:
### १. पूछे गए प्रश्न का प्रत्यक्ष समाधान एवं व्यावहारिक विधि
(बिना भूमिका के सीधे क्रियात्मक शारीरिक व मानसिक विधि। लाभ खंड ३ में रखें।)

### २. विभिन्न सत्संग वचनों से विस्तृत समन्वय व रहस्य
(विभिन्न प्रवचनों से विषय का तात्विक समन्वय ও सूक्ष्म रहस्य।)

### ३. साधन के पावन लाभ, फल व महिमा (Benefits & Divine Glory)
(पाप-नाश, चित्त शुद्धि, भगवत्-कृपा व आध्यात्मिक प्रगति का वर्णन।)

### ४. पूज्य महाराज जी के पावन दृष्टांत व सावधानियां
(साधना पथ के विघ्न, साधक की सावधानियां व महाराज जी के वास्तविक दृष्टांत।)

### ५. प्रामाणिक संदर्भ सूची (Discourse References & Timestamps)
(सत्संगों एवं एकांतिक वार्तालापों से शब्दशः साक्ष्य, सटीक वीडियो हाइपरलिंक [चैनल • mm:ss](URL) सहित।)

---

[प्रारूप 'ख'] परिस्थिति-आधारित / केस-स्टडी (प्रकार ४) प्रश्नों हेतु:
### १. परिस्थिति का प्रत्यक्ष आध्यात्मिक समाधान (Direct Spiritual Resolution)
(साधक की स्थिति का सीधा, शांत और व्यावहारिक आध्यात्मिक समाधान। सांसारिक युक्तियों से रहित।)

### २. प्रारब्ध, कर्म-रहस्य एवं लीला दृष्टि (Karmic Reality & Divine Perspective)
(प्रतिकूलता को पूर्वजन्म का प्रारब्ध, कर्म-ऋण शोधन, तथा भगवत्-विधान की मंगलमयी लीला के रूप में समझाना।)

### ३. साधक की आचार-संहिता: क्या करें और क्या न करें (Actionable Do's & Don'ts)
(सहनशीलता, मौन, पर-दोष अदर्शन, वाणी संयम का विवरण। एक सुस्पष्ट GFM मार्कडाउन तालिका अवश्य दें:)
| **करें (Do's)** | **न करें (Don'ts)** |
|-----------------|---------------------|
| • तुरंत नाम-कीर्तन व मौन धारण करें। | • पलटकर जवाब न दें या कलह न बढ़ाएं। |
| • सामने वाले को प्रारब्ध का निमित्त मानें। | • दोष-दर्शन या बदले की भावना न लाएं। |

### ४. पूज्य महाराज जी के पावन वचन व एकांतिक वार्तालाप प्रमाण (Authentic Quotes & Timestamps)
(सत्संगों एवं एकांतिक वार्तालापों से प्रामाणिक उद्धरण व सटीक वीडियो हाइपरलिंक [चैनल • mm:ss](URL) सहित।)

### ५. साधक का रक्षा सूत्र एवं मनन (Spiritual Protective Anchor)
(अखंड नाम जप, प्रिया-प्रियतम का अनन्य आश्रय, और हृदय को शांत रखने वाला मंगलकारी मनन सूत्र।)"""



# ============================================================================
# 4. Multi-Turn Query Rewriter & LLM Provider Fallback Chain
# ============================================================================

class LLMProviderChain:
    """
    Orchestrates LLM calls across free-tier providers in strict priority order:
    1st: Google Gemma (Direct AI Studio)
    2nd: Groq (llama-3.3-70b-versatile / Qwen)
    3rd: OpenRouter (meta-llama/llama-3.3-70b-instruct:free / Nemotron)
    4th: Local Ollama (llama3.2)

    Zero per-query cost constraint: All models are 100% free.
    """

    def __init__(self):
        self.groq_api_key = settings.groq_api_key
        self.openrouter_api_key = settings.openrouter_api_key
        self.gemini_api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.google_api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
        self.ollama_base_url = settings.ollama_base_url
        self.provider_chain = settings.llm_provider_chain

    def complete_google_gemma(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Optional[Tuple[str, str, str]]:
        """Call Google Gemma via Google AI Studio direct free tier."""
        g_key = self.gemini_api_key or self.google_api_key
        if not g_key:
            return None
        try:
            sys_text = ""
            contents = []
            for msg in messages:
                role = msg.get("role", "user")
                text = msg.get("content", "")
                if role == "system":
                    sys_text += text + "\n\n"
                elif role == "assistant":
                    contents.append({"role": "model", "parts": [{"text": text}]})
                else:
                    if sys_text and not contents:
                        contents.append({"role": "user", "parts": [{"text": f"{sys_text}\n\n{text}"}]})
                        sys_text = ""
                    else:
                        contents.append({"role": "user", "parts": [{"text": text}]})
            if not contents and sys_text:
                contents.append({"role": "user", "parts": [{"text": sys_text}]})

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }
            candidate_models = [model] if model else ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
            seen = set()
            models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

            with httpx.Client(timeout=18.0) as client:
                for model_name in models_to_try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={g_key}"
                    try:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                ans_text = "".join([p.get("text", "") for p in parts if not p.get("thought", False)]).strip()
                                if not ans_text and parts:
                                    ans_text = "".join([p.get("text", "") for p in parts]).strip()
                                if ans_text:
                                    return ans_text, "Google AI Studio", model_name
                        else:
                            logger.warning(f"Google model {model_name} status {resp.status_code}: {resp.text[:180]}")
                    except Exception as inner_e:
                        logger.warning(f"Google model {model_name} failed: {inner_e}")
        except Exception as e:
            logger.warning(f"Google completion failed: {e}")
        return None

    def complete_groq(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 950,
    ) -> Optional[Tuple[str, str, str]]:
        """Call Groq free tier with rate-limit resilient model fallback."""
        if not self.groq_api_key:
            return None
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_api_key, max_retries=0)
            # Enforce Groq free-tier output token ceiling to prevent 429 OTPM errors
            effective_tokens = min(max_tokens, 950)
            candidate_models = [model] if model else ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b", "groq/compound-mini"]
            seen = set()
            models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

            for m in models_to_try:
                try:
                    resp = client.chat.completions.create(
                        model=m,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=effective_tokens,
                    )
                    content = resp.choices[0].message.content or ""
                    if content.strip():
                        return content, "Groq", m
                except Exception as inner_e:
                    logger.warning(f"Groq model {m} failed: {inner_e}. Trying next model on Groq if any.")
        except Exception as e:
            logger.warning(f"Groq API call failed: {e}")
        return None

    def complete_openrouter(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1400,
    ) -> Optional[Tuple[str, str, str]]:
        """Call OpenRouter free models with fallback on upstream 429."""
        if not self.openrouter_api_key:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "HTTP-Referer": "https://swayambhu.local",
                "X-Title": "SWAYAMBHU v2 Satsang RAG",
            }
            candidate_models = [model] if model else [
                settings.openrouter_llama_model,
                "minimax/minimax-m3:free",
                "nvidia/nemotron-3.5-lightning:free",
                "google/gemma-4-26b-a4b-it:free",
            ]
            seen = set()
            models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

            with httpx.Client(timeout=35.0) as client:
                for m in models_to_try:
                    payload = {
                        "model": m,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    try:
                        resp = client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=payload
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            msg = data.get("choices", [{}])[0].get("message", {})
                            content = msg.get("content") or msg.get("reasoning") or ""
                            if content.strip():
                                return content.strip(), "OpenRouter", m
                        else:
                            logger.warning(f"OpenRouter {m} status {resp.status_code}: {resp.text[:180]}")
                    except Exception as inner_e:
                        logger.warning(f"OpenRouter model {m} error: {inner_e}")
        except Exception as e:
            logger.warning(f"OpenRouter call failed: {e}")
        return None

    def complete_ollama(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> Optional[Tuple[str, str, str]]:
        """Call local Ollama instance as zero-cost last resort."""
        try:
            with httpx.Client(timeout=50.0) as client:
                resp = client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": settings.ollama_model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature, "num_predict": max_tokens}
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("message", {}).get("content", "")
                    if content.strip():
                        return content, "Ollama", settings.ollama_model
        except Exception as e:
            logger.warning(f"Ollama local fallback failed: {e}")
        return None

    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Tuple[str, str, str]:
        """
        Executes chat completion down the fallback chain in strict priority order.
        Returns (response_text, provider_name, model_name).
        """
        for provider in self.provider_chain:
            provider_clean = provider.strip().lower()

            if provider_clean in ("google_gemma", "gemma_direct"):
                res = self.complete_google_gemma(messages, temperature=temperature)
                if res:
                    return res

            elif provider_clean == "groq":
                res = self.complete_groq(messages, temperature=temperature)
                if res:
                    return res

            elif provider_clean == "openrouter_llama":
                res = self.complete_openrouter(messages, model=settings.openrouter_llama_model, temperature=temperature)
                if res:
                    return res

            elif provider_clean == "openrouter_gemma":
                res = self.complete_openrouter(messages, model=settings.openrouter_gemma_model, temperature=temperature)
                if res:
                    return res

            elif provider_clean == "ollama":
                res = self.complete_ollama(messages, temperature=temperature)
                if res:
                    return res

        # Offline deterministic emergency fallback
        return (
            REVERENT_REFUSAL_UNGROUNDED,
            "Offline",
            "LocalDeterministicFallback"
        )


class SatsangCouncil:
    """
    LLM Council Architecture for SWAYAMBHU v2 (Inspired by Karpathy/llm-council).

    Deliberation Stages:
    1. Parallel First Opinions (3 diverse spiritual perspectives):
       - Member A (परामर्शक - भाव व वाणी निष्ठा): Google Gemma 4 31B
       - Member B (विधान-दर्शी - व्यावहारिक क्रिया व नियम): Groq (Llama-3.3 / Qwen)
       - Member C (समन्वय-कर्ता - सर्व-सुलभ सामंजस्य): OpenRouter (Nemotron / Llama-3.3)
    2. Peer Review & Grounding Cross-Audit (Anonymized):
       - An auditor cross-references the 3 drafts against raw transcript ground truth,
         flagging hallucinations, ungrounded claims, or timestamp inaccuracies.
    3. Chairman Synthesis (पूज्य सभापति):
       - Google Gemma 4 31B weaves consensus into the structured 5-section response.
    """

    def __init__(self, llm_chain: LLMProviderChain):
        self.llm_chain = llm_chain

    def deliberate(
        self,
        grounded_context: str,
        raw_query: str,
        system_prompt: str,
        case_info: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any], str, str]:
        start_council = time.time()

        # -------------------------------------------------------------
        # STAGE 1: Parallel First Opinions
        # -------------------------------------------------------------
        member_configs = [
            {
                "id": "member_a",
                "title": "परामर्शक (Radha-Bhav & Verbal Nuance)",
                "role_desc": "आपका मुख्य ध्यान पूज्य महाराज जी के भाव, प्रिया-प्रियतम के अनन्य आश्रय, और वचनों के आंतरिक मर्म पर है।",
                "provider": "google_gemma",
            },
            {
                "id": "member_b",
                "title": "विधान-दर्शी (Practical Saadhana & Steps)",
                "role_desc": "आपका मुख्य ध्यान नाम जप की व्यावहारिक क्रिया, आसन, जिह्वा की स्थिति, माला, समय, और गृहस्थ/साधक की दिनचर्या के प्रत्यक्ष नियमों पर है।",
                "provider": "groq",
            },
            {
                "id": "member_c",
                "title": "समन्वय-कर्ता (Cross-Channel Synthesis)",
                "role_desc": "आपका मुख्य ध्यान चारों चैनलों (भजन मार्ग, साधन पथ, वृन्दावन रस महिमा, श्रीहित राधा कृपा) के विभिन्न संदर्भों में सामंजस्य स्थापित करने पर है।",
                "provider": "openrouter",
            },
        ]

        def _fetch_member_opinion(cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Tuple[str, str, str]]]:
            role_desc = cfg["role_desc"]
            case_note = ""
            if case_info:
                case_note = (
                    f"\n\nपरिस्थिति-आधारित केस निर्देश ({case_info['title']}):\n"
                    f"- शून्य मतिभ्रम नियम: किसी सांसारिक परामर्शदाता (थेरेपिस्ट, कोर्ट, पुलिस, बदला) की सलाह कदापि न दें।\n"
                    f"- समाधान पूर्णतः पूज्य महाराज जी के आध्यात्मिक सिद्धांतों (प्रारब्ध भोग, प्रतिकूलता सहना, मौन, पर-दोष अदर्शन, नाम जप) पर आधारित हो।\n"
                    f"- मुख्य सिद्धांत: {', '.join(case_info['spiritual_principles'][:5])}\n"
                )
            prompt = (
                f"पूज्य महाराज जी के सम्पूर्ण डेटाबेस से प्राप्त सत्संग संदर्भ:\n"
                f"============================================================\n"
                f"{grounded_context}\n"
                f"============================================================\n\n"
                f"साधक का प्रश्न: {raw_query}\n\n"
                f"आपका विशिष्ट दृष्टिकोण (Council Lens): {role_desc}{case_note}\n\n"
                f"निर्देश:\n"
                f"1. केवल ऊपर दिए गए संदर्भों के आधार पर ही उत्तर दें। मनगढ़ंत बात न जोड़ें।\n"
                f"2. अपने विशिष्ट दृष्टिकोण के अनुसार मुख्य बिंदु स्पष्ट करें।\n"
                f"3. संदर्भों में आए समय-चिह्नों ([चैनल • mm:ss]) का उल्लेख करें।\n"
                f"संक्षेप में २ पैराग्राफ (१५०-२०० शब्द) में सटीक सार दें।"
            )
            msgs = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            res = None
            if cfg["provider"] == "google_gemma":
                res = self.llm_chain.complete_google_gemma(msgs, temperature=0.25, max_tokens=400)
            elif cfg["provider"] == "groq":
                res = self.llm_chain.complete_groq(msgs, temperature=0.25, max_tokens=400)
            elif cfg["provider"] == "openrouter":
                res = self.llm_chain.complete_openrouter(msgs, temperature=0.25, max_tokens=400)

            if not res:
                res = self.llm_chain.complete(msgs, temperature=0.25)
            return cfg, res

        stage1_opinions: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_cfg = {executor.submit(_fetch_member_opinion, cfg): cfg for cfg in member_configs}
            for future in as_completed(future_to_cfg):
                try:
                    cfg, res = future.result()
                    if res and res[0].strip():
                        text, prov, mod = res
                        stage1_opinions.append({
                            "member_id": cfg["id"],
                            "title": cfg["title"],
                            "provider": prov,
                            "model": mod,
                            "opinion": text.strip(),
                        })
                    else:
                        stage1_opinions.append({
                            "member_id": cfg["id"],
                            "title": cfg["title"],
                            "provider": cfg["provider"],
                            "model": "Unavailable",
                            "opinion": "इस सदस्य का उत्तर अनुपलब्ध रहा।",
                        })
                except Exception as e:
                    logger.warning(f"Error fetching council member opinion: {e}")

        # Sort back to member_a, member_b, member_c order
        order_map = {"member_a": 0, "member_b": 1, "member_c": 2}
        stage1_opinions.sort(key=lambda x: order_map.get(x["member_id"], 9))

        # -------------------------------------------------------------
        # STAGE 2: Peer Review & Grounding Cross-Audit (Anonymized)
        # -------------------------------------------------------------
        valid_opinions = [op for op in stage1_opinions if op["model"] != "Unavailable"]
        if not valid_opinions:
            logger.warning("All council members failed. Falling back to single LLM pass.")
            ans, prov, mod = self.llm_chain.complete(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": raw_query}],
                temperature=0.15
            )
            return ans, {}, prov, mod

        anonymized_blocks = []
        for idx, op in enumerate(valid_opinions, start=1):
            anonymized_blocks.append(f"--- प्रारूप {idx} ({op['title']}) ---\n{op['opinion']}\n")
        anonymized_text = "\n".join(anonymized_blocks)

        audit_case_clause = ""
        if case_info:
            audit_case_clause = (
                f"\n४. जांचें कि क्या किसी प्रारूप में आधुनिक सांसारिक परामर्श (थेरेपी, कोर्ट, कानूनी सलाह, झगड़ा) दिया गया है? "
                f"यदि हां, तो उसे तुरंत निरस्त करें और केवल पूज्य महाराज जी के आध्यात्मिक विधान (प्रारब्ध, सहनशीलता, मौन, नाम जप) को स्वीकृत करें।"
            )

        audit_prompt = (
            f"पूज्य महाराज जी के प्रामाणिक सत्संग संदर्भ (सत्य आधार / Ground Truth):\n"
            f"============================================================\n"
            f"{grounded_context}\n"
            f"============================================================\n\n"
            f"साधक का प्रश्न: {raw_query}\n\n"
            f"सत्संग परिषद के विभिन्न सदस्यों के स्वतंत्र विचार (Anonymized Drafts):\n"
            f"{anonymized_text}\n\n"
            f"लेखा परीक्षा (Audit) कार्य:\n"
            f"१. क्या किसी प्रारूप में संदर्भ से बाहर की कोई बात (Hallucination) या मनगढ़ंत व्याख्या है?\n"
            f"२. क्या व्यावहारिक विधि और आध्यात्मिक सिद्धांत महाराज जी के वचनों के अनुकूल हैं?\n"
            f"३. उद्धरण और समय-चिह्नों की प्रमाणिकता की पुष्टि करें।{audit_case_clause}\n"
            f"कृपया संक्षेप में २-३ बुलेट पॉइंट्स में निष्पक्ष मूल्यांकन दें।"
        )

        audit_msgs = [
            {"role": "system", "content": "आप पूज्य महाराज जी के वचनों के निष्पक्ष शोध लेखा परीक्षक (Grounding Auditor) हैं।"},
            {"role": "user", "content": audit_prompt}
        ]

        # Stage 2 Auditor: prioritize Google Gemini Flash (3.5) for huge context and fast audit
        audit_res = self.llm_chain.complete_google_gemma(audit_msgs, model="gemini-3.5-flash", temperature=0.15, max_tokens=500)
        if not audit_res:
            audit_res = self.llm_chain.complete_groq(audit_msgs, model="qwen/qwen3.8-27b", temperature=0.15, max_tokens=500)
        if not audit_res:
            audit_res = self.llm_chain.complete_openrouter(audit_msgs, model="meta-llama/llama-3.3-70b-instruct:free", temperature=0.15, max_tokens=500)
        if not audit_res:
            audit_res = self.llm_chain.complete(audit_msgs, temperature=0.15)
        audit_text = audit_res[0].strip() if audit_res else "लेखा परीक्षा पूर्ण (Grounding verified)."

        # -------------------------------------------------------------
        # STAGE 3: Chairman Synthesis (पूज्य सभापति)
        # -------------------------------------------------------------
        if case_info:
            chairman_prompt = (
                f"पूज्य महाराज जी के सम्पूर्ण डेटाबेस से प्राप्त सत्संग संदर्भ:\n"
                f"============================================================\n"
                f"{grounded_context}\n"
                f"============================================================\n\n"
                f"साधक का परिस्थिति-आधारित प्रश्न (Case Study): {raw_query}\n\n"
                f"पहचाना गया विषय: {case_info['title']}\n"
                f"प्रासंगिक आध्यात्मिक सिद्धांत: {', '.join(case_info['spiritual_principles'])}\n\n"
                f"सत्संग परिषद के सदस्यों के विचार (Council Deliberations):\n"
                f"{anonymized_text}\n\n"
                f"प्रमाणिकता लेखा परीक्षा (Grounding Audit Notes):\n"
                f"{audit_text}\n\n"
                f"सभापति का दायित्व:\n"
                f"परिषद के सभी विचारों और लेखा परीक्षा का मंथन करते हुए पूज्य महाराज जी के वास्तविक वचनों पर आधारित अंतिम, सर्वोत्कृष्ट और निर्दोष उत्तर तैयार करें।\n"
                f"कठोर नियम: सांसारिक थेरेपी या सांसारिक समझौते की मनगढ़ंत सलाह कदापि न दें। समाधान पूर्णतः आध्यात्मिक प्रारब्ध, सहनशीलता, मौन और नाम जप पर आधारित हो।\n"
                f"अति-आवश्यक: उत्तर में साधक का प्रश्न कदापि न दोहराएं और न ही '**प्रश्न:**' लिखें। सीधे प्रथम खंड (### १.) से उत्तर प्रारंभ करें।\n"
                f"अनिवार्य रूप से परिस्थिति-आधारित विशेष ५-खंडीय प्रारूप (Markdown) का पालन करें:\n"
                f"### १. परिस्थिति का प्रत्यक्ष आध्यात्मिक समाधान (Direct Spiritual Resolution)\n"
                f"### २. प्रारब्ध, कर्म-रहस्य एवं लीला दृष्टि (Karmic Reality & Divine Perspective)\n"
                f"### ३. साधक की आचार-संहिता: क्या करें और क्या न करें (Actionable Do's & Don'ts)\n"
                f"### ४. पूज्य महाराज जी के पावन वचन व एकांतिक वार्तालाप प्रमाण (Authentic Quotes & Timestamps)\n"
                f"### ५. साधक का रक्षा सूत्र एवं मनन (Spiritual Protective Anchor)\n"
                f"प्रत्येक मुख्य बिंदु पर समय-चिह्न व सीधा वीडियो लिंक ([चैनल • mm:ss](URL)) अवश्य दें।"
            )
        else:
            chairman_prompt = (
                f"पूज्य महाराज जी के सम्पूर्ण डेटाबेस से प्राप्त सत्संग संदर्भ:\n"
                f"============================================================\n"
                f"{grounded_context}\n"
                f"============================================================\n\n"
                f"साधक का प्रश्न: {raw_query}\n\n"
                f"सत्संग परिषद के सदस्यों के विचार (Council Deliberations):\n"
                f"{anonymized_text}\n\n"
                f"प्रमाणिकता लेखा परीक्षा (Grounding Audit Notes):\n"
                f"{audit_text}\n\n"
                f"सभापति का दायित्व:\n"
                f"परिषद के सभी विचारों और लेखा परीक्षा का मंथन करते हुए पूज्य महाराज जी के वास्तविक वचनों पर आधारित अंतिम, सर्वोत्कृष्ट और निर्दोष उत्तर तैयार करें।\n"
                f"अति-आवश्यक: उत्तर में साधक का प्रश्न कदापि न दोहराएं और न ही '**प्रश्न:**' लिखें। सीधे प्रथम खंड (### १.) से उत्तर प्रारंभ करें।\n"
                f"अति-महत्वपूर्ण: यदि प्रश्न 'विधि / कैसे करें' का है, तो प्रथम खंड में पहले क्रियात्मक विधि समझाएं, लाभ खंड ३ में बताएं।\n"
                f"अनिवार्य रूप से निर्धारित ५-खंडीय प्रारूप (Markdown) का पालन करें:\n"
                f"### १. प्रत्यक्ष मुख्य उत्तर एवं विधि\n"
                f"### २. सूक्ष्म भाव व रहस्य\n"
                f"### ३. साधक हेतु व्यावहारिक निर्देश\n"
                f"### ४. पूज्य महाराज जी के शब्दशः उद्धरण\n"
                f"### ५. मनन सूत्र\n"
                f"प्रत्येक मुख्य बिंदु पर समय-चिह्न व सीधा वीडियो लिंक ([चैनल • mm:ss](URL)) अवश्य दें।"
            )

        chairman_msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chairman_prompt},
        ]

        # Stage 3 Chairman Synthesis Priority:
        # 1. Google Gemini 3.5 Flash (1M context, beautiful Hindi, fast)
        # 2. Groq (Qwen 3.8 27B / GPT-OSS 20B)
        # 3. OpenRouter (Meta Llama 3.3 70B / Minimax)
        chairman_res = self.llm_chain.complete_google_gemma(chairman_msgs, model="gemini-3.5-flash", temperature=0.18, max_tokens=2200)
        if not chairman_res:
            chairman_res = self.llm_chain.complete_groq(chairman_msgs, model="qwen/qwen3.8-27b", temperature=0.18, max_tokens=950)
        if not chairman_res:
            chairman_res = self.llm_chain.complete_openrouter(chairman_msgs, model="meta-llama/llama-3.3-70b-instruct:free", temperature=0.18, max_tokens=2200)
        if not chairman_res:
            chairman_res = self.llm_chain.complete(chairman_msgs, temperature=0.18)

        final_raw_answer, chair_prov, chair_mod = chairman_res
        final_answer = sanitize_answer(final_raw_answer)
        council_latency_ms = int((time.time() - start_council) * 1000)

        deliberation_dict = {
            "stage_1_opinions": stage1_opinions,
            "stage_2_audit": audit_text,
            "stage_3_chairman": {
                "title": "सभापति (Chairman Synthesis)",
                "provider": chair_prov,
                "model": chair_mod,
            },
            "deliberation_latency_ms": council_latency_ms,
        }

        return final_answer, deliberation_dict, chair_prov, chair_mod


def rewrite_multi_turn_query(
    user_query: str,
    history: List[ChatMessage],
    llm_chain: LLMProviderChain
) -> str:
    """
    Multi-Turn Query Contextualization:
    If conversation history exists, resolves pronouns and implicit context
    ('what did he say about that?') into a standalone Hindi search query.
    Never blindly concatenates history to the retrieval query.
    """
    if not history:
        return user_query

    # Take recent 4 messages for concise context
    recent_history = history[-4:]
    history_repr = "\n".join(f"{msg.role.value}: {msg.content}" for msg in recent_history)

    prompt = f"""You are a query contextualizer for satsangs of Shri Hit Premanand Govind Sharan Ji Maharaj.
Given the conversation history and the latest user query, rewrite the query into a single, self-contained Hindi/Devanagari search query.
- Resolve all pronouns ('he', 'that', 'this', 'uske baare me', 'ye kaise kare') using the context.
- Keep the domain spiritual terms (Naam Jap, Dosh Darshan, Mansik Paap, Naam Aparadh, Ashraya, Ekantik Vartalaap) intact.
- DO NOT answer the question. Only output the rewritten search query.

Conversation History:
{history_repr}

Latest User Query: {user_query}

Self-Contained Query (in Devanagari Hindi):"""

    try:
        rewritten, _, _ = llm_chain.complete([{"role": "user", "content": prompt}], temperature=0.1)
        cleaned = rewritten.strip().replace('"', '').replace("'", "")
        # Remove any leading conversational prefix if model was chatty
        cleaned = re.sub(r"^(Rewritten Query:|पुनर्लेखित प्रश्न:|\s*)\s*", "", cleaned)
        return cleaned if cleaned else user_query
    except Exception as e:
        logger.warning(f"Query rewriting failed ({e}). Using raw query.")
        return user_query


# ============================================================================
# 5. RAGEngine Implementation
# ============================================================================

class RAGEngine:
    """Full RAG Orchestration Engine for SWAYAMBHU v2."""

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = get_vector_store()
        self.llm_chain = LLMProviderChain()
        self.reranker = CrossEncoderReRanker()
        self.council = SatsangCouncil(self.llm_chain)

    def process_query(self, request: ChatRequest, client_ip: Optional[str] = None) -> ChatResponse:
        start_time = time.time()
        raw_query = request.message.strip()

        # Step 1: Fast-path Adversarial & Off-topic filter (<1ms)
        refusal = evaluate_fast_path_filter(raw_query)
        if refusal:
            latency_ms = int((time.time() - start_time) * 1000)
            return ChatResponse(
                answer=refusal,
                is_grounded=False,
                refusal_reason="Off-topic or adversarial query detected by security filter.",
                citations=[],
                latency_ms=latency_ms,
                model_used="FastPathSecurityFilter",
                llm_provider="SecurityFilter",
            )

        # Step 2: Multi-turn Query Rewriting (if history exists)
        rewritten_query = raw_query
        if request.history:
            rewritten_query = rewrite_multi_turn_query(raw_query, request.history, self.llm_chain)

        # Step 3: Query Normalization (Hinglish -> Devanagari + Spiritual Lexicon)
        normalized_query = normalize_hinglish_to_devanagari(rewritten_query)

        # Step 3.5: Case Query Analysis & Spiritual Expansion Detection
        case_info = analyze_case_based_query(normalized_query) or analyze_case_based_query(raw_query)

        # Step 4: Vector Embedding & Candidate Retrieval (Dual Retrieval if Case Query)
        query_embedding = self.embedding_generator.embed_query(normalized_query)
        chunks_literal = self.vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=settings.top_k_retrieval,
            min_similarity=0.22 if case_info else settings.similarity_threshold,
            channel_filter=request.channel_filter,
        )

        if case_info:
            logger.info(
                f"Case query detected [{case_info['category']}]: Expanding retrieval with spiritual principles: "
                f"{case_info['spiritual_principles'][:4]}"
            )
            spiritual_embedding = self.embedding_generator.embed_query(case_info["expansion_search_query"])
            chunks_spiritual = self.vector_store.search_similar(
                query_embedding=spiritual_embedding,
                top_k=settings.top_k_retrieval,
                min_similarity=0.22,
                channel_filter=request.channel_filter,
            )

            # Reciprocal Rank Fusion (RRF) with 1.35x weight for spiritual discourse chunks
            combined_chunks: Dict[str, Dict[str, Any]] = {}
            rrf_scores: Dict[str, float] = {}
            k_rrf = 60

            # 1. Literal search results (weight 1.0)
            for rank, c in enumerate(chunks_literal):
                cid = str(c.get("id"))
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_rrf + rank + 1))
                if cid not in combined_chunks:
                    combined_chunks[cid] = dict(c)

            # 2. Spiritual principle expansion results (weight 1.35)
            for rank, c in enumerate(chunks_spiritual):
                cid = str(c.get("id"))
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.35 / (k_rrf + rank + 1))
                if cid not in combined_chunks:
                    combined_chunks[cid] = dict(c)
                else:
                    combined_chunks[cid]["similarity"] = max(
                        float(combined_chunks[cid].get("similarity", 0.0)),
                        float(c.get("similarity", 0.0)),
                    )

            # Sort candidate chunks by combined RRF score
            sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
            candidate_chunks = [combined_chunks[cid] for cid in sorted_cids]
        else:
            candidate_chunks = chunks_literal

        # Step 5: Check Grounding Availability
        if not candidate_chunks:
            latency_ms = int((time.time() - start_time) * 1000)
            return ChatResponse(
                answer=REVERENT_REFUSAL_UNGROUNDED,
                is_grounded=False,
                refusal_reason="No relevant satsang recording found matching the query.",
                citations=[],
                normalized_query=normalized_query,
                rewritten_query=rewritten_query if rewritten_query != raw_query else None,
                latency_ms=latency_ms,
                model_used="NoRetrievalGroundingFallback",
                llm_provider="None",
                case_category=case_info["category"] if case_info else None,
            )

        # Step 6: Multi-Satsang Cross-Video Diversity & MMR Re-Ranking
        # Cap chunks per single video to ensure we search the whole database across multiple satsangs
        video_chunk_counts: Dict[str, int] = {}
        diverse_candidate_pool: List[Dict[str, Any]] = []
        for c in candidate_chunks:
            vid = c.get("video_id", "unknown")
            count = video_chunk_counts.get(vid, 0)
            if count < 2:  # Cap at 2 chunks per video in primary pool to guarantee diverse satsang sources
                video_chunk_counts[vid] = count + 1
                diverse_candidate_pool.append(c)

        # Backfill remaining chunks up to candidate count if needed
        if len(diverse_candidate_pool) < settings.rerank_top_k * 2:
            for c in candidate_chunks:
                if c not in diverse_candidate_pool:
                    diverse_candidate_pool.append(c)

        # Step 6: Select top diverse chunks across satsangs based on pgvector cosine similarity
        diverse_candidate_pool.sort(key=lambda x: float(x.get("similarity", 0.0)), reverse=True)
        top_chunks = diverse_candidate_pool[:settings.rerank_top_k]


        # Step 7: Build Grounded LLM Context Across All Channels
        from config import SUPPORTED_CHANNELS
        context_blocks = []
        citations: List[Citation] = []

        for idx, chunk in enumerate(top_chunks):
            ch_raw = chunk.get("channel_id", "bhajan_marg")
            try:
                ch_enum = SourceChannel(ch_raw)
            except Exception:
                ch_enum = SourceChannel.BHAJAN_MARG

            ch_cfg = SUPPORTED_CHANNELS.get(ch_enum.value)
            ch_title = ch_cfg.title if ch_cfg else ch_enum.value.replace("_", " ").title()
            vid_id = chunk.get("video_id", "unknown")
            vid_title = chunk.get("title") or f"पूज्य महाराज जी सत्संग ({vid_id})"
            start_sec = int(chunk.get("start_sec", 0))
            end_sec = int(chunk.get("end_sec", 0))
            start_fmt = chunk.get("start_formatted", "00:00")
            end_fmt = chunk.get("end_formatted", "00:00")
            clean_text = chunk.get("clean_text", "")
            sim = float(chunk.get("similarity", 0.0))

            # YouTube clickable URL with exact timestamp offset
            yt_url = f"https://youtu.be/{vid_id}?t={start_sec}"
            citation_md = f"[{ch_title} • {start_fmt}]({yt_url})"

            context_blocks.append(
                f"--- सत्संग संदर्भ अंश {idx + 1} [{ch_title}] ---\n"
                f"स्रोतः {ch_title} ({ch_enum.value})\n"
                f"वीडियो आईडी: {vid_id} | शीर्षक: {vid_title}\n"
                f"सटीक समय अंतराल (Timestamp): {start_fmt} से {end_fmt}\n"
                f"सीधा वीडियो लिंक (Clickable Citation): {citation_md}\n"
                f"सीधा लिंक URL: {yt_url}\n"
                f"पूज्य महाराज जी के अमृत वचन:\n{clean_text}\n"
            )

            # Build Citation object
            aliases_raw = chunk.get("cross_channel_aliases", [])
            aliases = [CrossChannelAlias(**a) for a in aliases_raw] if isinstance(aliases_raw, list) and aliases_raw and isinstance(aliases_raw[0], dict) else []

            citations.append(
                Citation(
                    video_id=vid_id,
                    title=vid_title,
                    channel=ch_enum,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    timestamp_start=start_fmt,
                    timestamp_end=end_fmt,
                    url=yt_url,
                    relevance_score=round(sim, 3),
                    excerpt=clean_text[:280] + ("..." if len(clean_text) > 280 else ""),
                    cross_channel_aliases=aliases,
                )
            )

        grounded_context = "\n".join(context_blocks)
        if case_info:
            user_prompt = (
                f"पूज्य महाराज जी के सम्पूर्ण डेटाबेस से प्राप्त सत्संग संदर्भ:\n"
                f"============================================================\n"
                f"{grounded_context}\n"
                f"============================================================\n\n"
                f"साधक का परिस्थिति-आधारित प्रश्न (Case Study): {raw_query}\n\n"
                f"पहचाना गया विषय: {case_info['title']}\n"
                f"प्रासंगिक आध्यात्मिक सिद्धांत: {', '.join(case_info['spiritual_principles'])}\n\n"
                f"अति-महत्वपूर्ण परिस्थिति निर्देश (STRICT ZERO-HALLUCINATION & ANTI-SECULAR PROTOCOL):\n"
                f"1. सांसारिक परामर्श (थेरेपी, कोर्ट, पुलिस, झगड़ा, बदला, एचआर) पर पूर्ण प्रतिबंध है। साधक को केवल और केवल पूज्य महाराज जी के आध्यात्मिक विधान (प्रारब्ध भोग, सहनशीलता, मौन, पर-दोष अदर्शन, अनन्य आश्रय व नाम जप) के अनुसार समाधान दें।\n"
                f"2. शून्य मतिभ्रम (Zero Hallucination): केवल ऊपर दिए गए संदर्भों के आधार पर ही उत्तर दें। मनगढ़ंत बात न जोड़ें।\n"
                f"3. दिए गए एकांतिक वार्तालापों और प्रवचनों से उद्धरण व सटीक वीडियो लिंक ([चैनल • mm:ss](URL)) अवश्य दें।\n"
                f"4. उत्तर में साधक का प्रश्न कदापि न दोहराएं और न ही '**प्रश्न:**' लिखें। सीधे प्रथम खंड (### १.) से उत्तर प्रारंभ करें।\n"
                f"5. अनिवार्य रूप से परिस्थिति-आधारित विशेष ५-खंडीय प्रारूप (Markdown) में ही उत्तर दें:\n"
                f"### १. परिस्थिति का प्रत्यक्ष आध्यात्मिक समाधान (Direct Spiritual Resolution)\n"
                f"### २. प्रारब्ध, कर्म-रहस्य एवं लीला दृष्टि (Karmic Reality & Divine Perspective)\n"
                f"### ३. साधक की आचार-संहिता: क्या करें और क्या न करें (Actionable Do's & Don'ts)\n"
                f"### ४. पूज्य महाराज जी के पावन वचन व एकांतिक वार्तालाप प्रमाण (Authentic Quotes & Timestamps)\n"
                f"### ५. साधक का रक्षा सूत्र एवं मनन (Spiritual Protective Anchor)"
            )
        else:
            user_prompt = (
                f"पूज्य महाराज जी के सम्पूर्ण डेटाबेस से प्राप्त सत्संग संदर्भ:\n"
                f"============================================================\n"
                f"{grounded_context}\n"
                f"============================================================\n\n"
                f"साधक का प्रश्न: {raw_query}\n\n"
                f"अति-महत्वपूर्ण निर्देश:\n"
                f"1. सीधे प्रश्न का उत्तर दें (Direct Answer First): साधक ने जो पूछा है, सबसे पहले उसी का प्रत्यक्ष, ठोस समाधान दें। विषयांतर या मतिभ्रम (Hallucination) बिल्कुल न करें।\n"
                f"2. उत्तर में साधक का प्रश्न कदापि न दोहराएं और न ही '**प्रश्न:**' लिखें। सीधे प्रथम खंड (### १.) से उत्तर प्रारंभ करें।\n"
                f"3. यदि प्रश्न 'विधि / कैसे करें' (How-to) का है: तो खंड १ में अनिवार्य रूप से पहले करने की पूरी व्यावहारिक विधि (चरण, तरीका, अभ्यास) समझाएं। लाभ (Benefits) केवल खंड ३ में बताएं (लाभ बताकर विधि को न टालें)।\n"
                f"4. शून्य मतिभ्रम (Zero Hallucination): केवल ऊपर दिए गए संदर्भों में महाराज जी के वास्तविक वचनों के आधार पर ही उत्तर दें। कोई मनगढ़ंत बात न जोड़ें।\n"
                f"5. समग्र डेटाबेस समन्वय: केवल एक वीडियो तक सीमित न रहें, दिए गए विभिन्न सत्संगों, चैनलों और संदर्भ अंशों को जोड़कर उत्तर दें।\n"
                f"6. हर मुख्य बिंदु व समाधान के साथ सटीक समय-चिह्न और सीधा वीडियो लिंक (जैसे [चैनल • mm:ss](URL)) अवश्य लिखें। संदर्भ ब्लॉक में दिए गए 'सीधा वीडियो लिंक' का ही प्रयोग करें।\n"
                f"7. निर्धारित 5-खंडीय प्रारूप (Markdown) का पूर्ण पालन करें।"
            )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Step 8: Execute LLM Completion (Fast Mode vs Council Deliberation)
        council_meta = None
        if request.use_council:
            logger.info(f"Deliberating through Satsang Council (Karpathy LLM Council) for query: {raw_query[:50]}")
            answer_text, council_meta, provider_used, model_used = self.council.deliberate(
                grounded_context=grounded_context,
                raw_query=raw_query,
                system_prompt=SYSTEM_PROMPT,
                case_info=case_info,
            )
            full_model_identifier = f"SatsangCouncil/{model_used}"
            provider_for_response = "SatsangCouncil"
        else:
            # Standard Fast Mode (~1.5s single LLM pass)
            raw_answer, provider_used, model_used = self.llm_chain.complete(messages, temperature=0.15)
            answer_text = sanitize_answer(raw_answer)
            full_model_identifier = f"{provider_used}/{model_used}"
            provider_for_response = provider_used

        # Ensure answer text is clean of any echoed question prefix and in-text citations are hyperlinked
        answer_text = sanitize_answer(answer_text)
        answer_text = linkify_citations(answer_text, citations)
        latency_ms = int((time.time() - start_time) * 1000)

        # Check if the LLM itself determined lack of coverage (only if it didn't provide structured discourse sections)
        has_sections = ("### १." in answer_text or "### 1." in answer_text or "###" in answer_text)
        is_refusal = (
            not has_sections
            and (
                "उल्लेख नहीं" in answer_text
                or "संदर्भ में नहीं" in answer_text
                or "परिधि से बाहर" in answer_text
                or "कोई वर्णन नहीं" in answer_text
                or "कोई चर्चा नहीं" in answer_text
                or "स्पष्ट उल्लेख प्राप्त नहीं" in answer_text
            )
        )

        # Step 9: Structured Logging (Asynchronous / Non-blocking)
        self._log_query_telemetry(
            raw_query=raw_query,
            normalized_query=normalized_query,
            rewritten_query=rewritten_query if rewritten_query != raw_query else None,
            client_ip=client_ip,
            citations=citations,
            latency_ms=latency_ms,
            llm_provider=provider_for_response,
            llm_model=model_used,
            answered=not is_refusal,
        )

        return ChatResponse(
            answer=answer_text,
            is_grounded=not is_refusal,
            refusal_reason="Query answered from grounded recordings." if not is_refusal else "Recordings do not cover this specific question.",
            citations=citations if not is_refusal else [],
            disclaimer=ChatDisclaimer(),
            normalized_query=normalized_query,
            rewritten_query=rewritten_query if rewritten_query != raw_query else None,
            latency_ms=latency_ms,
            model_used=full_model_identifier,
            llm_provider=provider_for_response,
            use_council=request.use_council,
            council_deliberation=council_meta,
            case_category=case_info["category"] if case_info else None,
        )

    def _log_query_telemetry(
        self,
        raw_query: str,
        normalized_query: Optional[str],
        rewritten_query: Optional[str],
        client_ip: Optional[str],
        citations: List[Citation],
        latency_ms: int,
        llm_provider: str,
        llm_model: str,
        answered: bool,
    ):
        """Structured telemetry recording into query_logs table or local log."""
        log_entry = {
            "raw_query": raw_query,
            "normalized_query": normalized_query,
            "rewritten_query": rewritten_query,
            "ip_address": client_ip,
            "retrieved_chunk_ids": [c.video_id for c in citations],
            "source_channels_retrieved": list(set(c.channel.value for c in citations)),
            "rerank_scores": [c.relevance_score for c in citations],
            "latency_ms": latency_ms,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "answered": answered,
        }

        logger.info(f"Query processed in {latency_ms}ms | Provider: {llm_provider} | Model: {llm_model} | Channels: {log_entry['source_channels_retrieved']} | Answered: {answered}")

        # Dispatch Supabase telemetry logging asynchronously to avoid blocking the HTTP response
        def _bg_supabase_write():
            if settings.vector_store_backend == "supabase" and settings.supabase_url:
                try:
                    from supabase import create_client
                    key = settings.supabase_service_role_key or settings.supabase_key
                    client = create_client(settings.supabase_url, key)
                    client.table("query_logs").insert(log_entry).execute()
                except Exception as e:
                    logger.debug(f"Could not write query log to Supabase: {e}")

        threading.Thread(target=_bg_supabase_write, daemon=True).start()
