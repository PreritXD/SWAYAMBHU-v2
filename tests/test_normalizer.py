"""
Tests for Hinglish Detection, Transliteration, and Spiritual Domain Lexicon Preservation
"""

from indexer import is_hinglish_query, normalize_hinglish_to_devanagari


def test_is_hinglish_detection():
    """Verifies identification of Latin-script Hindi vs Devanagari."""
    assert is_hinglish_query("naam jaap kaise kare") is True
    assert is_hinglish_query("kisi me dosh darshan ho jaye to kya kare") is True
    assert is_hinglish_query("नाम जप कैसे करें") is False
    assert is_hinglish_query("पूज्य महाराज जी के वचन") is False


def test_spiritual_domain_lexicon_preservation():
    """Verifies that sacred terms are mapped to correct Devanagari forms."""
    # 1. Naam Aparadh
    res1 = normalize_hinglish_to_devanagari("naam aparadh se kaise bache")
    assert "नाम अपराध" in res1

    # 2. Dosh Darshan
    res2 = normalize_hinglish_to_devanagari("dosh darshan nahi karna chahiye")
    assert "दोष दर्शन" in res2

    # 3. Mansik Paap
    res3 = normalize_hinglish_to_devanagari("kya ye mansik paap hai")
    assert "मानसिक पाप" in res3

    # 4. Ekantik Vartalaap
    res4 = normalize_hinglish_to_devanagari("ekantik vartalaap me maharaj ji ne kya bataya")
    assert "एकांतिक वार्तालाप" in res4

    # 5. Ashraya
    res5 = normalize_hinglish_to_devanagari("shri ji ka aashraya kaise le")
    assert "आश्रय" in res5

    # 6. Sadhana
    res6 = normalize_hinglish_to_devanagari("sadhana me man nahi lagta")
    assert "साधना" in res6

    # 7. Naam Jap
    res7 = normalize_hinglish_to_devanagari("naam jap karne ka niyam")
    assert "नाम जप" in res7


def test_colloquial_variations():
    """Tests informal spelling variations typed by users."""
    # 'w' vs 'v', 'bure vichar'
    res = normalize_hinglish_to_devanagari("bhagwan ka naam jap karte samay bure vichar kyu aate hain")
    assert "भगवान" in res or "नाम जप" in res
    assert "बुरे विचार" in res
    assert "क्यों" in res


def test_devanagari_query_preserved():
    """Pure Devanagari query should remain intact."""
    dev_query = "पूज्य महाराज जी ने नाम जप की क्या महिमा बताई है?"
    normalized = normalize_hinglish_to_devanagari(dev_query)
    assert normalized == dev_query


def test_english_query_preserved():
    """Standard English queries should not be transliterated into phonetic Sanskrit/Devanagari."""
    eng_query = "Why do we overthink?"
    assert is_hinglish_query(eng_query) is False
    assert normalize_hinglish_to_devanagari(eng_query) == "Why do we overthink?"

    eng_query2 = "How to control negative thoughts and anger?"
    assert is_hinglish_query(eng_query2) is False
    assert normalize_hinglish_to_devanagari(eng_query2) == "How to control negative thoughts and anger?"

