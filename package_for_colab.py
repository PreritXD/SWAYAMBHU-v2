"""
Prepares a clean, minimal ZIP package for Google Colab GPU Ingestion.
Packages only the source code and configuration required for indexing discourses.
"""

import os
import zipfile

FILES_TO_PACKAGE = [
    "config.py",
    "schema.py",
    "chunking.py",
    "dedup.py",
    "indexer.py",
    "ingest.py",
    "colab_ingest.py",
    "requirements.txt"
]

OUTPUT_ZIP = "swayambhu_colab_package.zip"

def create_package():
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename in FILES_TO_PACKAGE:
            if os.path.exists(filename):
                zipf.write(filename, arcname=filename)
                print(f"Added {filename} ({os.path.getsize(filename)} bytes)")
            else:
                print(f"Warning: {filename} not found!")
    
    print(f"\nSuccessfully created {OUTPUT_ZIP} ({os.path.getsize(OUTPUT_ZIP)} bytes)")

if __name__ == "__main__":
    create_package()
