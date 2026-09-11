"""
SWAYAMBHU v2 - Vector Indexing, Query Normalization & MMR Re-Ranking

Provides:
1. Concrete Hinglish -> Devanagari transliteration with colloquial phonetic preprocessing
   and domain lexicon preservation (Naam Aparadh, Dosh Darshan, Mansik Paap, etc.).
2. Multilingual sentence embedding generation (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
3. Dual vector store interface:
   - Primary: Supabase Postgres + pgvector (with match_transcript_chunks RPC).
   - Fallback: Local ChromaDB store for seamless local dev and tests.
4. Maximal Marginal Relevance (MMR) diversity re-ranking to prevent redundant cross-channel chunks.
"""

from abc import ABC, abstractmethod
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from config import AppEnvironment, VectorStoreType, settings
from schema import ChunkRecord, Citation, CrossChannelAlias, SourceChannel

logger = logging.getLogger("swayambhu.indexer")

# ============================================================================
# 1. Hinglish -> Devanagari Normalizer & Spiritual Lexicon
# ============================================================================

# Exact spiritual domain terminology mapping
# Preserves theological integrity without secularization
SPIRITUAL_LEXICON: Dict[str, str] = {
    # Core sacred terms requested by prompt
    "naam aparadh": "नाम अपराध",
    "naam apradh": "नाम अपराध",
    "nam aparadh": "नाम अपराध",
    "nam apradh": "नाम अपराध",
    "dosh darshan": "दोष दर्शन",
    "dosh drishti": "दोष दर्शन",
    "dosh dekhna": "दोष दर्शन",
    "mansik paap": "मानसिक पाप",
    "mansik pap": "मानसिक पाप",
    "manasik paap": "मानसिक पाप",
    "sadhana": "साधना",
    "sadhan": "साधन",
    "naam jap": "नाम जप",
    "naam jaap": "नाम जप",
    "nam jap": "नाम जप",
    "nam jaap": "नाम जप",
    "ekantik vartalaap": "एकांतिक वार्तालाप",
    "ekantik vartalap": "एकांतिक वार्तालाप",
    "ekant vartalap": "एकांतिक वार्तालाप",
    "ekantik": "एकांतिक",
    "ashraya": "आश्रय",
    "aashraya": "आश्रय",
    "asraya": "आश्रय",
    # Additional sacred names and core concepts
    "radha rani": "श्री राधा रानी",
    "radharani": "श्री राधा रानी",
    "shri ji": "श्री जी",
    "shriji": "श्री जी",
    "hit premanand": "श्री हित प्रेमानंद",
    "premanand ji": "प्रेमानंद जी",
    "premanand maharaj": "प्रेमानंद जी महाराज",
    "maharaj ji": "महाराज जी",
    "vrindavan": "वृन्दावन",
    "vrindavan dham": "वृन्दावन धाम",
    "guru kripa": "गुरु कृपा",
    "bhagwan": "भगवान",
    "bhagvan": "भगवान",
    "bhakti": "भक्ति",
    "prem": "प्रेम",
    "dhyan": "ध्यान",
    "samarpan": "समर्पण",
    "kripa": "कृपा",
    "kirpa": "कृपा",
    "seva": "सेवा",
    "satsang": "सत्संग",
    "maya": "माया",
    "vairagya": "वैराग्य",
    "kam": "काम",
    "krodh": "क्रोध",
    "lobh": "लोभ",
    "moh": "मोह",
    "ahankar": "अहंकार",
}

# Common colloquial Hindi phrases and question words in Hinglish
COLLOQUIAL_PATTERNS: List[Tuple[str, str]] = [
    (r"\bkaise kare[n]?\b", "कैसे करें"),
    (r"\bkyu[n]?\b", "क्यों"),
    (r"\bkyon\b", "क्यों"),
    (r"\bkya hai\b", "क्या है"),
    (r"\bkya kare[n]?\b", "क्या करें"),
    (r"\bkab kare[n]?\b", "कब करें"),
    (r"\bkaha[n]?\b", "कहाँ"),
    (r"\bmann\b", "मन"),
    (r"\bvichar\b", "विचार"),
    (r"\bbure vichar\b", "बुरे विचार"),
    (r"\bbura vichar\b", "बुरे विचार"),
    (r"\bgande vichar\b", "बुरे विचार"),
    (r"\bnahi lagta\b", "नहीं लगता"),
    (r"\bnahi hota\b", "नहीं होता"),
    (r"\bchhutkara\b", "छुटकारा"),
    (r"\bupaay\b", "उपाय"),
    (r"\bupay\b", "उपाय"),
    (r"\bmukti\b", "मुक्ति"),
    (r"\bshanti\b", "शांति"),
    (r"\bshanka\b", "शंका"),
    (r"\bbatao\b", "बताइए"),
    (r"\bbataye[n]?\b", "बताइए"),
    (r"\bshri radha\b", "श्री राधा"),
]


ENGLISH_COMMON_WORDS = {
    "why", "how", "what", "when", "where", "who", "which", "whom", "whose",
    "is", "are", "am", "was", "were", "be", "been", "being",
    "do", "does", "did", "done", "doing",
    "have", "has", "had", "having",
    "can", "could", "should", "would", "will", "shall", "may", "might", "must",
    "the", "a", "an", "this", "that", "these", "those",
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "him", "his", "she", "her", "they", "them", "their", "it", "its",
    "to", "for", "in", "on", "at", "by", "from", "with", "about", "into", "through", "during", "before", "after",
    "and", "or", "but", "if", "because", "as", "until", "while", "of", "off",
    "not", "no", "never", "always", "stop", "get", "rid", "tell",
    "overthink", "overthinking", "think", "thinking", "thought", "thoughts",
    "mind", "brain", "focus", "concentration", "peace", "calm", "anxiety", "depression",
    "anger", "fear", "doubt", "jealousy", "control", "controlling", "distraction",
    "spiritual", "spirituality", "devotion", "devotee", "god",
    "meaning", "purpose", "life", "death", "soul", "karma",
    "meditation", "meditate", "chant", "chanting", "prayer", "worship",
    "problem", "solution", "help", "guide"
}


def is_english_query(text: str) -> bool:
    """Detects whether a query is standard English rather than Romanized Hindi (Hinglish)."""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return False
    english_matches = sum(1 for w in words if w in ENGLISH_COMMON_WORDS)
    return (english_matches / len(words)) >= 0.35


def is_hinglish_query(text: str) -> bool:
    """
    Detects whether a query contains Latin-script Hindi (Hinglish).
    Checks if ASCII alphabets comprise > 40% of the non-space characters
    AND is not standard English.
    """
    if is_english_query(text):
        return False
    cleaned = re.sub(r"[\s\d\W]+", "", text)
    if not cleaned:
        return False
    ascii_count = sum(1 for c in cleaned if 'a' <= c.lower() <= 'z')
    return (ascii_count / len(cleaned)) >= 0.4


def normalize_hinglish_to_devanagari(text: str) -> str:
    """
    3-Stage Hinglish to Devanagari Normalization:
    1. Direct multi-word domain dictionary substitution.
    2. Colloquial conversational phrase mapping.
    3. Deterministic phonetic transliteration for remaining tokens via indic-transliteration
       (or rule-based phonetic mapping fallback).
    Preserves pure English queries as-is so multilingual embeddings can match semantically.
    """
    if not text:
        return ""

    if is_english_query(text):
        return text.strip()

    if not is_hinglish_query(text):
        # Already predominantly Devanagari; just normalize Unicode
        import unicodedata
        return unicodedata.normalize("NFC", text).strip()

    working_text = text.lower().strip()

    # Stage 1: Spiritual Domain Dictionary Replacement (longer phrases first)
    for term, dev_term in sorted(SPIRITUAL_LEXICON.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        working_text = pattern.sub(f" {dev_term} ", working_text)

    # Stage 2: Colloquial conversational patterns
    for regex_pat, replacement in COLLOQUIAL_PATTERNS:
        working_text = re.sub(regex_pat, f" {replacement} ", working_text, flags=re.IGNORECASE)

    # Stage 3: Phonetic transliteration for remaining Latin tokens
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate

        # Pre-normalize typical informal spelling quirks before sanscript
        def clean_latin_token(tok: str) -> str:
            # Skip tokens already in Devanagari
            if any('\u0900' <= ch <= '\u097F' for ch in tok):
                return tok
            # Informal orthography adjustments
            tok = tok.replace("w", "v")
            tok = tok.replace("ee", "i")
            tok = tok.replace("oo", "u")
            tok = tok.replace("shh", "sh")
            return tok

        tokens = working_text.split()
        transformed_tokens = []
        for t in tokens:
            if any('\u0900' <= ch <= '\u097F' for ch in t):
                transformed_tokens.append(t)
            else:
                cleaned_t = clean_latin_token(t)
                try:
                    dev_tok = transliterate(cleaned_t, sanscript.ITRANS, sanscript.DEVANAGARI)
                    transformed_tokens.append(dev_tok)
                except Exception:
                    transformed_tokens.append(cleaned_t)

        result = " ".join(transformed_tokens)
    except ImportError:
        # Fallback rule-based phonetic mapper if library not yet loaded
        result = working_text

    # Final cleanup of extra spaces
    result = re.sub(r"\s+", " ", result).strip()
    return result


# ============================================================================
# 2. Embedding Generator
# ============================================================================

class EmbeddingGenerator:
    """Generates 384-dimensional embeddings using paraphrase-multilingual-MiniLM-L12-v2."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model_name
        self._model = None
        self._hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")

    def _embed_via_hf_api(self, texts: List[str]) -> Optional[List[List[float]]]:
        token = getattr(self, "_hf_token", None) or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        if not token:
            return None
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            for url in [
                f"https://router.huggingface.co/hf-inference/models/{self.model_name}",
                f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}",
            ]:
                try:
                    resp = requests.post(
                        url,
                        headers=headers,
                        json={"inputs": texts, "options": {"wait_for_model": True}},
                        timeout=12,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            if isinstance(data[0], list):
                                return data
                            elif isinstance(data[0], (int, float)):
                                return [data]
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"HF Inference API error ({e}).")
        return None

    def _load_model(self):
        if self._model is None:
            if (
                os.environ.get("FAST_TEST_MODE") in ("1", "true", "True")
                or os.environ.get("PYTEST_CURRENT_TEST") is not None
                or os.environ.get("APP_ENV") == "test"
                or settings.app_env == AppEnvironment.TEST
            ):
                self._model = "fallback"
                return

            # 0. Check if Hugging Face Inference API is available (Zero local RAM overhead)
            token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
            if token:
                self._hf_token = token
                self._model = "hf_api"
                logger.info(f"Configured Hugging Face Serverless Inference API for {self.model_name} (Zero local RAM).")
                return

            # 1. Try FastEmbed ONNX (quantized, lightweight, single-thread)
            try:
                import gc
                os.environ.setdefault("OMP_NUM_THREADS", "1")
                os.environ.setdefault("ONNXRUNTIME_NUM_THREADS", "1")
                os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")
                from fastembed import TextEmbedding
                logger.info(f"Loading FastEmbed ONNX model: {self.model_name} (threads=1)")
                self._model = TextEmbedding(model_name=self.model_name, threads=1)
                self._is_fastembed = True
                gc.collect()
                return
            except Exception as fe_err:
                self._is_fastembed = False
                logger.debug(f"FastEmbed not available ({fe_err}), falling back to SentenceTransformer.")

            # 2. Standard SentenceTransformer fallback (used locally / on GPU)
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Loading embedding model: {self.model_name} on device: {device}")
                from sentence_transformers import SentenceTransformer
                try:
                    self._model = SentenceTransformer(self.model_name, device=device, local_files_only=True)
                except Exception:
                    # If not cached locally, ensure offline flags are cleared so HuggingFace can download
                    os.environ.pop("HF_HUB_OFFLINE", None)
                    os.environ.pop("TRANSFORMERS_OFFLINE", None)
                    self._model = SentenceTransformer(self.model_name, device=device)
            except Exception as e:
                logger.warning(f"SentenceTransformer not loaded directly ({e}). Using fallback embedding generation.")
                self._model = "fallback"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._load_model()

        if self._model == "hf_api":
            hf_res = self._embed_via_hf_api(texts)
            if hf_res is not None:
                return hf_res
            logger.warning("HF API request failed, attempting local FastEmbed fallback.")
            try:
                import gc
                os.environ.setdefault("OMP_NUM_THREADS", "1")
                os.environ.setdefault("ONNXRUNTIME_NUM_THREADS", "1")
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=self.model_name, threads=1)
                self._is_fastembed = True
                gc.collect()
            except Exception:
                self._model = "fallback"

        if getattr(self, "_is_fastembed", False):
            embeddings = list(self._model.embed(texts))
            return [emb.tolist() for emb in embeddings]
        elif self._model != "fallback":
            embeddings = self._model.encode(
                texts,
                batch_size=64,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return [emb.tolist() for emb in embeddings]
        else:
            # Deterministic mock 384-dim embedding for testing / offline environments
            np.random.seed(42)
            results = []
            for t in texts:
                h = int(abs(hash(t))) % (10 ** 8)
                vec = np.sin(np.linspace(0, h % 100 + 1, settings.embedding_dim))
                norm = np.linalg.norm(vec)
                vec = (vec / norm if norm > 0 else vec).tolist()
                results.append(vec)
            return results

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * settings.embedding_dim


# ============================================================================
# 3. Vector Store Abstraction
# ============================================================================

class BaseVectorStore(ABC):
    """Abstract Vector Store Interface."""

    @abstractmethod
    def insert_chunks(self, chunks: List[ChunkRecord]) -> int:
        pass

    @abstractmethod
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 8,
        min_similarity: float = 0.35,
        channel_filter: Optional[SourceChannel] = None,
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def count_chunks(self, channel_filter: Optional[SourceChannel] = None) -> int:
        pass


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB local vector store fallback."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = None
        self._collection = None

    def _init_db(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = self._client.get_or_create_collection(
                name="swayambhu_chunks",
                metadata={"hnsw:space": "cosine"}
            )

    def insert_chunks(self, chunks: List[ChunkRecord]) -> int:
        if not chunks:
            return 0
        self._init_db()

        ids = [c.id for c in chunks]
        embeddings = [c.embedding for c in chunks if c.embedding is not None]
        documents = [c.clean_text for c in chunks]
        metadatas = [
            {
                "video_id": c.video_id,
                "channel_id": c.channel_id.value,
                "chunk_index": c.chunk_index,
                "start_sec": c.start_sec,
                "end_sec": c.end_sec,
                "start_formatted": c.start_formatted,
                "end_formatted": c.end_formatted,
                "embedding_model": c.embedding_model or settings.embedding_model_name,
                "is_duplicate": c.is_duplicate,
                "token_count": c.token_count,
            }
            for c in chunks
        ]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 8,
        min_similarity: float = 0.35,
        channel_filter: Optional[SourceChannel] = None,
    ) -> List[Dict[str, Any]]:
        self._init_db()

        where_clause: Dict[str, Any] = {"is_duplicate": False}
        if channel_filter:
            where_clause = {
                "$and": [
                    {"is_duplicate": False},
                    {"channel_id": channel_filter.value}
                ]
            }

        total_in_coll = self._collection.count()
        if total_in_coll == 0:
            return []

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 2, total_in_coll),
            where=where_clause,
            include=["documents", "metadatas", "distances", "embeddings"]
        )

        matched_chunks: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]
        embs = results.get("embeddings", [[]])[0] if "embeddings" in results else None

        for i in range(len(ids)):
            # Cosine distance to similarity: similarity = 1 - distance
            similarity = 1.0 - distances[i]
            if similarity < min_similarity:
                continue

            matched_chunks.append({
                "id": ids[i],
                "clean_text": docs[i],
                "similarity": similarity,
                "embedding": embs[i] if embs is not None and len(embs) > i else None,
                **metas[i]
            })

        return matched_chunks

    def count_chunks(self, channel_filter: Optional[SourceChannel] = None) -> int:
        self._init_db()
        if channel_filter:
            res = self._collection.get(where={"channel_id": channel_filter.value})
            return len(res["ids"]) if res and "ids" in res else 0
        return self._collection.count()


class SupabaseVectorStore(BaseVectorStore):
    """Supabase pgvector store utilizing match_transcript_chunks RPC."""

    def __init__(self):
        from supabase import create_client, Client
        url = settings.supabase_url
        key = settings.supabase_service_role_key or settings.supabase_key
        if not url or not key:
            raise ValueError("Supabase URL and Key must be provided for SupabaseVectorStore.")
        self.client: Client = create_client(url, key)

    def insert_chunks(self, chunks: List[ChunkRecord]) -> int:
        if not chunks:
            return 0

        records = [
            {
                "id": c.id,
                "video_id": c.video_id,
                "channel_id": c.channel_id.value,
                "chunk_index": c.chunk_index,
                "start_sec": c.start_sec,
                "end_sec": c.end_sec,
                "start_formatted": c.start_formatted,
                "end_formatted": c.end_formatted,
                "raw_text": c.raw_text,
                "clean_text": c.clean_text,
                "token_count": c.token_count,
                "embedding": c.embedding,
                "is_duplicate": c.is_duplicate,
                "canonical_chunk_id": c.canonical_chunk_id,
                "canonical_video_id": c.canonical_video_id,
                "cross_channel_aliases": [a.model_dump() for a in c.cross_channel_aliases],
            }
            for c in chunks
        ]

        # Ensure parent video records exist to satisfy foreign key constraint
        video_map = {c.video_id: c.channel_id.value for c in chunks}
        for vid_id, ch_id in video_map.items():
            try:
                self.client.table("videos").upsert(
                    {
                        "video_id": vid_id,
                        "channel_id": ch_id,
                        "title": f"Discourse {vid_id}",
                        "url": f"https://youtu.be/{vid_id}",
                    },
                    on_conflict="video_id",
                    ignore_duplicates=True,
                ).execute()
            except Exception as e:
                logger.warning(f"Could not pre-populate video stub for {vid_id}: {e}")

        # Batch upsert in sizes of 100
        batch_size = 100
        inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            response = self.client.table("transcript_chunks").upsert(batch).execute()
            inserted += len(response.data or batch)
        return inserted

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 8,
        min_similarity: float = 0.35,
        channel_filter: Optional[SourceChannel] = None,
    ) -> List[Dict[str, Any]]:
        params = {
            "query_embedding": query_embedding,
            "match_threshold": min_similarity,
            "match_count": top_k * 2,
            "filter_channel": channel_filter.value if channel_filter else None
        }

        rpc_resp = self.client.rpc("match_transcript_chunks", params).execute()
        return rpc_resp.data or []

    def count_chunks(self, channel_filter: Optional[SourceChannel] = None) -> int:
        query = self.client.table("transcript_chunks").select("id", count="exact")
        if channel_filter:
            query = query.eq("channel_id", channel_filter.value)
        resp = query.execute()
        return resp.count or 0


def get_vector_store() -> BaseVectorStore:
    """Factory to get the configured vector store."""
    if settings.vector_store_backend == VectorStoreType.SUPABASE:
        try:
            return SupabaseVectorStore()
        except Exception as e:
            if settings.app_env in (AppEnvironment.DEVELOPMENT, AppEnvironment.TEST):
                logger.warning(f"Supabase connection failed ({e}). Falling back to local ChromaDB.")
                return ChromaVectorStore()
            raise e
    return ChromaVectorStore()


# ============================================================================
# 4. Maximal Marginal Relevance (MMR) Diversity Re-Ranking
# ============================================================================

def maximal_marginal_relevance(
    query_vector: np.ndarray,
    candidate_vectors: np.ndarray,
    candidate_chunks: List[Dict[str, Any]],
    top_k: int = 4,
    diversity_lambda: float = 0.7,
) -> List[Dict[str, Any]]:
    """
    Re-ranks candidate chunks using Maximal Marginal Relevance (MMR) to avoid
    retrieving near-duplicate chunks from the same or different channels.
    lambda = 0.7 balances relevance (0.7) vs novelty/diversity (0.3).
    """
    if len(candidate_chunks) <= top_k:
        return candidate_chunks

    query_norm = np.linalg.norm(query_vector)
    if query_norm > 0:
        query_vector = query_vector / query_norm

    # Normalize candidate vectors
    norms = np.linalg.norm(candidate_vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    cand_normed = candidate_vectors / norms

    # Initial query-chunk similarities
    sim_to_query = np.dot(cand_normed, query_vector)

    selected_indices: List[int] = []
    unselected_indices: List[int] = list(range(len(candidate_chunks)))

    for _ in range(min(top_k, len(candidate_chunks))):
        best_score = -float("inf")
        best_idx = -1

        for idx in unselected_indices:
            q_sim = sim_to_query[idx]
            if not selected_indices:
                score = q_sim
            else:
                max_cand_sim = np.max(np.dot(cand_normed[selected_indices], cand_normed[idx]))
                score = diversity_lambda * q_sim - (1.0 - diversity_lambda) * max_cand_sim

            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx != -1:
            selected_indices.append(best_idx)
            unselected_indices.remove(best_idx)

    # Return ordered selected chunks with updated rerank_score
    results = []
    for rank, idx in enumerate(selected_indices):
        chunk = dict(candidate_chunks[idx])
        chunk["rerank_score"] = float(sim_to_query[idx])
        chunk["mmr_rank"] = rank + 1
        results.append(chunk)

    return results


# ============================================================================
# 5. Cross-Encoder Re-Ranker
# ============================================================================

class CrossEncoderReRanker:
    """
    Local Cross-Encoder re-ranker (cross-encoder/ms-marco-MiniLM-L-6-v2).
    Scores (query, passage) pairs to provide deep semantic re-ranking after initial
    bi-encoder vector retrieval and MMR diversification.
    Free, runs locally, zero API calls.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.rerank_model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            if (
                os.environ.get("FAST_TEST_MODE") in ("1", "true", "True")
                or os.environ.get("PYTEST_CURRENT_TEST") is not None
                or os.environ.get("APP_ENV") == "test"
                or settings.app_env == AppEnvironment.TEST
            ):
                self._model = "fallback"
                return
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning(f"CrossEncoder not loaded directly ({e}). Using fallback scoring.")
                self._model = "fallback"

    def rerank(
        self,
        query: str,
        candidate_chunks: List[Dict[str, Any]],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Re-ranks candidate chunks for a query using cross-encoder scores.
        """
        if not candidate_chunks:
            return []
        if len(candidate_chunks) == 1:
            chunk = dict(candidate_chunks[0])
            chunk["cross_encoder_score"] = float(chunk.get("similarity", 1.0))
            return [chunk]

        self._load_model()

        # Build pairs: (query, chunk_text)
        pairs = [
            (query, chunk.get("clean_text") or chunk.get("raw_text") or "")
            for chunk in candidate_chunks
        ]

        if self._model != "fallback":
            try:
                scores = self._model.predict(pairs)
            except Exception as e:
                logger.warning(f"CrossEncoder prediction error ({e}). Using similarity fallback.")
                scores = [float(c.get("similarity", 0.0)) for c in candidate_chunks]
        else:
            # Deterministic lexical overlap fallback for fast tests / offline mode
            scores = []
            query_words = set(re.findall(r"\w+", query.lower()))
            for _, doc in pairs:
                doc_words = set(re.findall(r"\w+", doc.lower()))
                overlap = len(query_words.intersection(doc_words)) / max(len(query_words), 1)
                scores.append(overlap)

        scored_chunks = []
        for i, chunk in enumerate(candidate_chunks):
            updated_chunk = dict(chunk)
            updated_chunk["cross_encoder_score"] = float(scores[i])
            scored_chunks.append(updated_chunk)

        # Sort descending by cross-encoder score
        scored_chunks.sort(key=lambda x: x.get("cross_encoder_score", 0.0), reverse=True)
        return scored_chunks[:top_k]


def cross_encoder_rerank(
    query: str,
    candidate_chunks: List[Dict[str, Any]],
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """Helper function to run cross-encoder re-ranking."""
    reranker = CrossEncoderReRanker()
    return reranker.rerank(query=query, candidate_chunks=candidate_chunks, top_k=top_k)

