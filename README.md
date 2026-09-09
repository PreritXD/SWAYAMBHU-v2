# SWAYAMBHU v2

Zero-Hallucination Grounded Satsang Q&A Engine & Digital Darshan Platform for Param Pujya Shri Hit Premanand Govind Sharan Ji Maharaj.

---

## Overview

**SWAYAMBHU v2** is a production-grade spiritual Q&A and archival research system grounded strictly in the recorded discourses (*satsangs*) of **Param Pujya Shri Hit Premanand Govind Sharan Ji Maharaj** (Vrindavan). Maharaj Ji's teachings focus on **Naam Jap** (chanting of the Divine Name), **Bhakti** (pure devotional surrender), **Nishkam Seva** (selfless service), and inner purification.

The platform enforces a core operational principle: **"Grounded, cited, refuses to guess"**. It answers queries strictly using verified words spoken by Maharaj Ji across indexed YouTube channels. Every statement is attributed to its source with exact, clickable YouTube video timestamp hyperlinks (`https://youtu.be/<VIDEO_ID>?t=<SECONDS>`). If a question is not directly addressed in recorded discourses, the system explicitly acknowledges the absence of discourse records rather than generating ungrounded advice.

---

## Key Features

- **Multi-Channel Discourse Coverage**: Indexes long-form discourses, intimate dialogues (*Ekantik Vartalaap*), and daily question-and-answer recordings across official channels including **Bhajan Marg**, **Sadhan Path**, **Vrindavan Ras**, and **Shri Hit Radha Kripa**.
- **5-Tier Transcript Extraction Pipeline**: Cascading transcription combining YouTube Captions API, cloud Whisper models (`whisper-large-v3`, `whisper-large-v3-turbo` via Groq), and local/Colab GPU `faster-whisper` models.
- **2-Tier Cross-Channel Deduplication**: Video-level shingle Jaccard indexing (>= 0.85) and chunk-level embedding cosine similarity (>= 0.92) with canonical tie-breaking to avoid redundant cross-channel postings.
- **Timestamped Sliding-Window Chunking**: Splits discourses into ~50-second (~400 token) windows with 15-second overlap, stripping Hindi verbal fillers while preserving exact second offsets.
- **Vector Search & Semantic Retrieval**: Generates 384-dimensional dense embeddings using `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` stored in Supabase PostgreSQL (`pgvector` HNSW index) with local ChromaDB support for offline development.
- **Zero-Hallucination RAG Orchestration**:
  - Tier-1 fast regex filter (<1ms) intercepts off-topic and adversarial queries.
  - Multi-turn pronoun resolution and query rewriting.
  - Hinglish-to-Devanagari normalization preserving sacred spiritual terms.
  - MMR diversity re-ranking and cross-encoder precision scoring (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
  - Automatic conversion of plain citations into clickable YouTube timestamp hyperlinks.
- **Free-Tier LLM Provider Fallback Chain**: High-availability inference prioritizing Groq, Google AI Studio Gemma, OpenRouter, and local Ollama.
- **Modern Digital Darshan Frontend**: Responsive web interface with real-time streaming, interactive clickable discourse badges, and an integrated Q&A sanctuary.

---

## Theological & Domain Terminology Integrity

Spiritual terms are preserved in Hindi and Devanagari to maintain doctrinal precision:

- **नाम अपराध (Naam Aparadh)**: Offense against the Holy Name.
- **दोष दर्शन (Dosh Darshan)**: Finding faults in others (strictly discouraged spiritual obstacle).
- **मानसिक पाप (Mansik Paap)**: Unwanted, intrusive thoughts arising during meditation (to be observed without attachment, not feared).
- **साधना (Sadhana)**: Disciplined spiritual contemplation and daily devotional practice.
- **नाम जप (Naam Jap)**: Continuous repetition of the Divine Name (*Shri Radha* or the devotee's chosen *Ishta*).
- **एकांतिक वार्तालाप (Ekantik Vartalaap)**: Intimate, solitary spiritual dialogues addressing deep seeker inquiries.
- **आश्रय (Ashraya)**: Complete, unconditional spiritual refuge at the lotus feet of Shri Radha Rani.

---

## Ingested Channels

| Channel Key | Channel Title | Primary Content |
| :--- | :--- | :--- |
| `bhajan_marg` | Bhajan Marg | Curated playlists, archival discourses, and Ekantik Vartalaap sessions. |
| `sadhan_path` | Sadhan Path | Daily satsang sessions, seeker Q&A, and practical guidance. |
| `vrindavan_ras` | Vrindavan Ras | Devotional discourses celebrating the glory and leelas of Vrindavan. |
| `shri_hit_radha_kripa` | Shri Hit Radha Kripa | Core philosophical guidance and devotional grace discourses. |

---

## Architecture & Pipeline

```
[ YouTube Video Feeds: Bhajan Marg, Sadhan Path, Vrindavan Ras, Shri Hit Radha Kripa ]
                                       |
                                       v
                   [ Discovery: ingest.py / sync_new_videos.py ]
                                       |
                                       v
                     [ 5-Tier Transcript Extraction Pipeline ]
          1. YouTube Captions API (youtube-transcript-api)
          2. Groq Cloud whisper-large-v3
          3. Groq Cloud whisper-large-v3-turbo
          4. Local / Colab GPU faster-whisper (large-v3)
          5. Local CPU faster-whisper (medium)
                                       |
                                       v
                    [ 2-Tier Cross-Channel Deduplication ]
          - Video-level shingle Jaccard matching (threshold: 0.85)
          - Chunk-level embedding cosine similarity (threshold: 0.92)
          - Canonical tie-breaking & cross-channel alias storage
                                       |
                                       v
                  [ Sliding-Window Normalization & Chunking ]
          - Unicode NFC normalization & Hindi verbal filler removal
          - ~50s windows / 15s overlap with exact millisecond timestamps
                                       |
                                       v
                   [ Dense Embeddings & Vector Storage ]
          - Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384-dim)
          - Primary: Supabase pgvector (HNSW Index: m=16, ef_construction=64)
          - Dev Fallback: Local ChromaDB
                                       |
                                       v
                  [ Grounded RAG Engine (rag_engine.py) ]
          - Tier-1 fast adversarial filter (<1ms)
          - Multi-turn query rewriting & Hinglish-to-Devanagari transliteration
          - pgvector retrieval & Cross-Encoder re-ranking
          - Strict five-part structured Devanagari answer blueprint
          - Hyperlink resolution: [Channel * MM:SS] -> https://youtu.be/VID?t=SEC
          - LLM fallback chain: Groq -> Google AI Studio -> OpenRouter -> Ollama
                                       |
                                       v
                    [ FastAPI Server & React Web Client ]
          - Endpoints: /api/chat, /api/feedback, /api/stats, /api/health
          - Responsive web application with interactive video badges
```

---

## Installation

### Prerequisites

- Python 3.10 or higher (tested on Python 3.11 and 3.12)
- Node.js 18+ and pnpm (for the frontend web application)
- `ffmpeg` installed and added to your system PATH
- Supabase account with `pgvector` enabled (or local ChromaDB for development)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/swayambhu-v2.git
cd swayambhu-v2
```

### 2. Set Up Python Environment

```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Set Up Frontend Dependencies

```bash
cd premanand-ji-website
pnpm install
cd ..
```

---

## Configuration

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```ini
# Environment: 'development', 'staging', or 'production'
APP_ENV=development

# Vector Store: 'supabase' (production) or 'chroma' (local dev)
VECTOR_STORE_BACKEND=supabase
CHROMA_PERSIST_DIR=./data/chroma_db

# Supabase Credentials (Required for Supabase backend)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Free LLM Fallback Hierarchy
LLM_PROVIDER_CHAIN=["groq", "google_gemma", "openrouter_llama", "openrouter_gemma", "ollama"]

# Free Cloud API Credentials
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-google-ai-studio-key
OPENROUTER_API_KEY=your-openrouter-api-key
OLLAMA_BASE_URL=http://localhost:11434

# Embedding & Re-Ranking Models
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIM=384
RERANK_MODEL_NAME=cross-encoder/ms-marco-MiniLM-L-6-v2
```

### Database Schema Migration

For Supabase deployments, execute the contents of `schema.sql` inside your Supabase SQL Editor:
- Enables the `vector` and `pgcrypto` PostgreSQL extensions.
- Creates `channels`, `videos`, `transcript_chunks`, `query_logs`, `feedback`, and `sync_status` tables.
- Creates HNSW index on `transcript_chunks.embedding` using cosine distance.
- Configures Row Level Security (RLS) policies.

---

## Usage

### 1. Ingestion Commands

Ingest video discourses into the database:

```bash
# Ingest up to 10 videos across all configured channels
python ingest.py --channel all --max-videos 10

# Ingest from a specific channel
python ingest.py --channel bhajan_marg --max-videos 20

# Ingest a single video by ID or YouTube URL
python ingest.py --video-id dQw4w9WgXcQ
```

Run automated incremental sync for newly published videos:

```bash
python sync_new_videos.py
```

Retry previously failed transcript extractions:

```bash
python retry_ingest.py --max-retries 3
```

### 2. Terminal CLI (`rag_cli.py`)

Test queries directly in the terminal:

```bash
# Ask a single question
python rag_cli.py ask "नाम जप करते समय बुरे विचार आएं तो क्या करें?"

# Launch an interactive multi-turn session
python rag_cli.py chat

# Test Hinglish-to-Devanagari transliteration
python rag_cli.py transliterate "dosh darshan aur mansik paap se kaise bache"
```

### 3. Starting the Backend API Server

Start the production FastAPI server:

```bash
python server.py
# Or run with uvicorn directly:
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

### 4. Running the Frontend Web Application

To run the web interface in development mode:

```bash
cd premanand-ji-website
pnpm dev
```

Visit `http://localhost:3000` in your browser.

To compile the production frontend build:

```bash
cd premanand-ji-website
pnpm build
```

The compiled assets will be placed in `premanand-ji-website/dist/public` and automatically served by FastAPI on port 8000.

---

## API Specification

### `POST /api/chat`

Submits a spiritual query and returns a grounded response with YouTube timestamp hyperlinks.

**Request Body (`application/json`)**:

```json
{
  "message": "प्रारब्ध और बुरे संग का क्या संबंध है?",
  "history": [],
  "session_id": "session_101",
  "channel_filter": null
}
```

**Response Body (`200 OK`)**:

```json
{
  "answer": "पूज्य महाराज जी समझाते हैं कि प्रतिकूल परिस्थितियां और बुरा संग पूर्व जन्मों के कर्मों और प्रारब्ध के कारण ही प्राप्त होता है...\n\n[Bhajan Marg • 04:44](https://youtu.be/393M9Lm9Rc4?t=284)",
  "is_grounded": true,
  "refusal_reason": "Query answered from grounded recordings.",
  "citations": [
    {
      "video_id": "393M9Lm9Rc4",
      "title": "पूज्य महाराज जी सत्संग (393M9Lm9Rc4)",
      "channel": "bhajan_marg",
      "start_sec": 284,
      "end_sec": 334,
      "timestamp_start": "04:44",
      "timestamp_end": "05:34",
      "url": "https://youtu.be/393M9Lm9Rc4?t=284",
      "relevance_score": 0.585
    }
  ],
  "disclaimer": {
    "text": "यह शोध प्रणाली पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के सार्वजनिक सत्संग वचनों पर आधारित है...",
    "is_official_channel": false
  },
  "latency_ms": 1120,
  "model_used": "Groq/groq/compound"
}
```

### `POST /api/feedback`

Submits user ratings or flags inaccurate answers.

```json
{
  "query": "दोष दर्शन से कैसे बचें?",
  "answer": "पूज्य महाराज जी के अनुसार...",
  "flagged": false,
  "note": "Accurate transcription and helpful answer."
}
```

### `GET /api/stats`

Returns chunk counts, video counts, and query volume metrics across channels.

### `GET /api/health`

Returns operational status, active vector store, and primary LLM provider.

---

## Running Tests & Evaluation

### Automated Test Suite

Run unit and integration tests using pytest:

```bash
pytest tests/ -v
```

Test coverage includes:
- `tests/test_config.py`: Fail-fast environment configuration and credential safety.
- `tests/test_normalizer.py`: Hinglish detection, transliteration, and spiritual terminology preservation.
- `tests/test_chunking.py`: Window sizing, overlap calculations, and filler word stripping.
- `tests/test_dedup.py`: Cross-channel deduplication algorithms and canonical tie-breaking.
- `tests/test_adversarial.py`: Fast-path filter against out-of-domain queries and prompt injections.
- `tests/test_rag_engine.py`: Grounded response generation, zero-hallucination refusals, and YouTube URL linking.
- `tests/test_server.py`: FastAPI endpoint responses, rate limiting, and error handling.

### Regression Benchmark (`eval_rag.py`)

Run benchmark evaluation against curated questions:

```bash
python eval_rag.py --dataset eval/golden_qa.json --output eval_report.json
```

---

## Contributing

Contributions to SWAYAMBHU v2 are welcome. Please follow these guidelines:

1. **Fork the Repository**: Create your own branch from `main` (`git checkout -b feature/your-feature-name`).
2. **Preserve Theological Integrity**: Ensure sacred terminology (such as *Naam Jap*, *Mansik Paap*, *Dosh Darshan*) remains unaltered in Hindi/Devanagari.
3. **Grounding Guarantee**: Features touching retrieval or generation must strictly adhere to the zero-hallucination constraint and refuse to answer if discourse evidence is missing.
4. **Run Tests**: Verify all tests pass (`pytest tests/ -v`) before opening a pull request.
5. **Commit Message Standards**: Write clear, descriptive commit messages describing the changes made.
6. **Open a Pull Request**: Submit your pull request to the `main` branch with an explanation of your modifications.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
