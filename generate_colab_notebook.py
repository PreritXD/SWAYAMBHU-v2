import json
import base64

with open("swayambhu_colab_package.zip", "rb") as f:
    zip_b64 = base64.b64encode(f.read()).decode("utf-8")

notebook = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "colab": {
            "name": "SWAYAMBHU_v2_Colab_GPU_Ingestion.ipynb",
            "provenance": [],
            "gpuType": "T4"
        },
        "accelerator": "GPU",
        "kernelspec": {
            "name": "python3",
            "display_name": "Python 3"
        },
        "language_info": {
            "name": "python"
        }
    },
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🕉️ SWAYAMBHU v2 — High-Speed GPU Ingestion on Google Colab\n",
                "\n",
                "This notebook runs the **SWAYAMBHU v2 Discourse Ingestion Pipeline** on Google Colab with **GPU Acceleration**.\n",
                "\n",
                "### ⚡ Why run on Google Colab GPU?\n",
                "- **20x - 50x Faster**: Uses NVIDIA CUDA (Tesla T4) for `faster-whisper` (large-v3) speech-to-text and `sentence-transformers` batch embeddings.\n",
                "- **Gigabit Bandwidth**: YouTube video metadata & audio downloads happen at 100+ MB/s on Google's backbone.\n",
                "- **Direct Cloud Sync**: Vector embeddings and sliding-window timestamp chunks are saved directly into your cloud **Supabase pgvector** database.\n",
                "- **Automatic Resume**: Already-indexed discourses are automatically skipped; only new discourses are processed."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 1: Verify GPU & Hardware\n",
                "Make sure Colab is set to GPU: **Runtime > Change runtime type > T4 GPU**."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Check NVIDIA GPU availability\n",
                "!nvidia-smi\n",
                "\n",
                "import torch\n",
                "print(f\"PyTorch Version: {torch.__version__}\")\n",
                "print(f\"CUDA Available: {torch.cuda.is_available()}\")\n",
                "if torch.cuda.is_available():\n",
                "    print(f\"GPU Device: {torch.cuda.get_device_name(0)}\")\n",
                "else:\n",
                "    print(\"⚠️ WARNING: GPU not detected! Go to Runtime > Change runtime type > Select T4 GPU.\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 2: Install Ingestion Dependencies\n",
                "Installs `yt-dlp`, `youtube-transcript-api`, `faster-whisper`, `sentence-transformers`, `supabase`, `pydantic-settings`, and `groq`.\n",
                "*(FFmpeg and PyTorch CUDA are already pre-installed on Google Colab)*."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Clean install without conflicting with Colab's pre-installed packages\n",
                "!pip install -q yt-dlp youtube-transcript-api faster-whisper sentence-transformers supabase pydantic-settings groq\n",
                "print('✅ Dependencies installed successfully!')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 3: Unpack SWAYAMBHU v2 Pipeline Code\n",
                "The pipeline source files are bundled below and unpacked automatically."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "import base64\n",
                "import os\n",
                "import zipfile\n",
                "\n",
                f'ZIP_B64 = """{zip_b64}"""\n',
                "\n",
                "with open('swayambhu_package.zip', 'wb') as f:\n",
                "    f.write(base64.b64decode(ZIP_B64))\n",
                "\n",
                "with zipfile.ZipFile('swayambhu_package.zip', 'r') as zip_ref:\n",
                "    zip_ref.extractall('.')\n",
                "\n",
                "print('✅ Unpacked SWAYAMBHU v2 pipeline files:')\n",
                "!ls -lh *.py"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 4: Configure Supabase & API Credentials\n",
                "These credentials connect directly to your Supabase pgvector database."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "import os\n",
                "\n",
                "# Supabase & Cloud API Settings (Replace with your actual keys)\n",
                "os.environ['APP_ENV'] = 'production'\n",
                "os.environ['VECTOR_STORE_BACKEND'] = 'supabase'\n",
                "os.environ['SUPABASE_URL'] = os.environ.get('SUPABASE_URL', 'https://your-project.supabase.co')\n",
                "os.environ['SUPABASE_KEY'] = os.environ.get('SUPABASE_KEY', 'your-supabase-anon-key')\n",
                "os.environ['SUPABASE_SERVICE_ROLE_KEY'] = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'your-supabase-service-role-key')\n",
                "os.environ['GROQ_API_KEY'] = os.environ.get('GROQ_API_KEY', 'your-groq-api-key')\n",
                "\n",
                "# Embedding & Device Configuration\n",
                "os.environ['EMBEDDING_MODEL_NAME'] = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'\n",
                "os.environ['EMBEDDING_DIM'] = '384'\n",
                "os.environ['LOCAL_WHISPER_GPU_MODEL'] = 'large-v3'\n",
                "\n",
                "print('✅ Environment credentials configured successfully!')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 5: Check Current Database Stats Before Ingesting"
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "from supabase import create_client\n",
                "\n",
                "client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])\n",
                "count_res = client.table('transcript_chunks').select('id', count='exact').limit(1).execute()\n",
                "total_chunks = count_res.count if hasattr(count_res, 'count') else 'Unknown'\n",
                "\n",
                "print(f'📊 Current Total Indexed Chunks in Supabase: {total_chunks}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 6: Launch GPU-Accelerated Ingestion\n",
                "\n",
                "Choose the command that fits your goal:\n",
                "\n",
                "- **Option A (The Other 3 Channels — Sadhan Path, Vrindavan Ras, Shri Hit Radha Kripa)**:\n",
                "  `!python ingest.py --channel sadhan_path,vrindavan_ras,shri_hit_radha_kripa --max-videos 0`\n",
                "\n",
                "- **Option B (All 4 Channels in Interleaved Round-Robin)**:\n",
                "  `!python ingest.py --channel all --max-videos 0 --batch-size 10`\n",
                "\n",
                "- **Option C (Sadhan Path Only)**:\n",
                "  `!python ingest.py --channel sadhan_path --max-videos 50`\n",
                "\n",
                "- **Option D (Vrindavan Ras Mahima Only)**:\n",
                "  `!python ingest.py --channel vrindavan_ras --max-videos 50`\n",
                "\n",
                "*(Videos already in Supabase are automatically skipped with `⏩ [SKIP]`)*"
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Run ingestion for the other 3 channels (or change --channel as needed):\n",
                "!python ingest.py --channel sadhan_path,vrindavan_ras,shri_hit_radha_kripa --max-videos 0"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 7: Verify Indexed Chunks After Ingestion"
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "count_res = client.table('transcript_chunks').select('id', count='exact').limit(1).execute()\n",
                "print(f'🎉 Updated Total Indexed Chunks in Supabase: {count_res.count}')"
            ]
        }
    ]
}

with open("SWAYAMBHU_v2_Colab_GPU_Ingestion.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print("Created SWAYAMBHU_v2_Colab_GPU_Ingestion.ipynb successfully!")
