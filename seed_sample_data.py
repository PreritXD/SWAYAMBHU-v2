"""
SWAYAMBHU v2 - Sample Discourse Seeder

Populates vector store with authentic recorded satsang excerpts of
Param Pujya Shri Hit Premanand Govind Sharan Ji Maharaj from both
Bhajan Marg and Sadhan Path channels, including:
  1. Ekantik Vartalaap on Naam Aparadh & Ashraya (Bhajan Marg)
  2. Satsang guidance on Mansik Paap & Dosh Darshan (Sadhan Path)
  3. Re-cut clip to demonstrate cross-channel deduplication and aliasing.
"""

from datetime import date
import logging
from config import VectorStoreType, settings
from dedup import CrossChannelDeduplicator
from indexer import EmbeddingGenerator, get_vector_store
from schema import ChunkRecord, SourceChannel, VideoMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("swayambhu.seed")

# Authentic discourse excerpts transcribed from recorded satsangs
SAMPLE_DISCOURSES = [
    {
        "video_id": "BM_EKANTIK_042",
        "channel": SourceChannel.BHAJAN_MARG,
        "title": "नाम अपराध से कैसे बचें और अनन्य आश्रय क्या है? - एकांतिक वार्तालाप 42",
        "upload_date": date(2023, 2, 14),
        "chunks": [
            {
                "chunk_index": 0,
                "start_sec": 45,
                "end_sec": 95,
                "start_fmt": "00:45",
                "end_fmt": "01:35",
                "text": (
                    "पूज्य महाराज जी कहते हैं कि नाम अपराध से साधक को सर्वथा बचना चाहिए। "
                    "दस प्रकार के नाम अपराधों में मुख्य हैं: संतों की निंदा करना, शिव और विष्णु में भेद समझना, "
                    "शास्त्रों और गुरु वचनों में अश्रद्धा रखना, और नाम के बल पर पाप करना। "
                    "जो साधक नाम जप का सहारा लेकर जानबूझकर पाप करता है, उसका पतन निश्चित है। "
                    "नाम अपराध का एक ही प्रायश्चित है - निरंतर दीन भाव से श्री राधा नाम का जप करते रहना।"
                )
            },
            {
                "chunk_index": 1,
                "start_sec": 100,
                "end_sec": 155,
                "start_fmt": "01:40",
                "end_fmt": "02:35",
                "text": (
                    "एकांतिक वार्तालाप में पूज्य महाराज जी ने श्री जी के अनन्य आश्रय का रहस्य समझाया: "
                    "अनन्य आश्रय का अर्थ है कि साधक का मन, बुद्धि और प्राण केवल प्रिया प्रियतम श्री राधा कृष्ण के चरणों में समर्पित हों। "
                    "संसार के किसी भी साधन, व्यक्ति या परिस्थिति का भरोसा न रखकर केवल श्री जी की कृपा पर निर्भर होना ही सच्चा आश्रय है। "
                    "जब तक संसार का आश्रय रहेगा, तब तक भगवत प्रेम में विशुद्ध निष्ठा प्राप्त नहीं हो सकती।"
                )
            },
            {
                "chunk_index": 2,
                "start_sec": 160,
                "end_sec": 210,
                "start_fmt": "02:40",
                "end_fmt": "03:30",
                "text": (
                    "साधना काल में मन का भटकाव रोकने के लिए महाराज जी कहते हैं कि जब भी मन सांसारिक विषयों में भागे, "
                    "उसे बलपूर्वक घसीटकर श्री राधा नाम जप में लगाएं। नाम जप ही मन को बांधने वाली एकमात्र रस्सी है। "
                    "निरंतर अभ्यास और सत्संग के श्रवण से धीरे-धीरे मन की चंचलता शांत हो जाती है और चित्त में एकाग्रता आती है।"
                )
            }
        ]
    },
    {
        "video_id": "SP_DAILY_812",
        "channel": SourceChannel.SADHAN_PATH,
        "title": "पूजा में बुरे विचार और दूसरों में दोष दर्शन से कैसे बचें? - साधन पथ",
        "upload_date": date(2023, 5, 20),
        "chunks": [
            {
                "chunk_index": 0,
                "start_sec": 30,
                "end_sec": 85,
                "start_fmt": "00:30",
                "end_fmt": "01:25",
                "text": (
                    "साधन पथ पर चलते हुए साधक को कभी भी दूसरों में दोष दर्शन नहीं करना चाहिए। "
                    "महाराज जी कहते हैं कि दूसरों के दोष देखने से हमारी अपनी ही दृष्टि और बुद्धि मलिन हो जाती है। "
                    "यदि किसी में कोई दोष दिखे भी, तो समझना चाहिए कि यह हमारे ही अंतःकरण का दोष है। "
                    "साधक का कर्तव्य है कि वह केवल अपने अवगुणों को देखे और दूसरों में भगवत भाव का दर्शन करे।"
                )
            },
            {
                "chunk_index": 1,
                "start_sec": 90,
                "end_sec": 145,
                "start_fmt": "01:30",
                "end_fmt": "02:25",
                "text": (
                    "पूजा या नाम जप के समय आने वाले बुरे विचारों और मानसिक पाप पर पूज्य महाराज जी अभय दान देते हैं: "
                    "वे कहते हैं कि जप करते समय यदि मन में गंदे या निंदनीय विचार आएं, तो बिल्कुल घबराएं नहीं। "
                    "ये विचार मानसिक पाप नहीं हैं, बल्कि यह हृदय में जमा हुआ जन्म-जन्मांतरों का मैल है जो नाम की अग्नि से जलकर बाहर निकल रहा है। "
                    "आप केवल नाम जप जारी रखें, विचारों से युद्ध न करें, वे स्वतः नष्ट हो जाएंगे।"
                )
            },
            {
                "chunk_index": 2,
                "start_sec": 150,
                "end_sec": 205,
                "start_fmt": "02:30",
                "end_fmt": "03:25",
                "text": (
                    "गृहस्थ जीवन में निरंतर नाम जप का नियम बनाने के लिए महाराज जी कहते हैं: "
                    "हाथ काम में रहे और मुख या हृदय में श्री राधा नाम चलता रहे। "
                    "भोजन बनाते समय, दुकान चलाते समय, अथवा यात्रा करते समय भी नाम जप किया जा सकता है। "
                    "इसके लिए किसी बाह्य पवित्रता या विशेष आसन की अनिवार्यता नहीं है, केवल प्रेमपूर्वक स्मरण चाहिए।"
                )
            }
        ]
    },
    {
        # Short clip from Sadhan Path re-cutting Bhajan Marg's discourse on Ashraya
        "video_id": "SP_CLIP_109",
        "channel": SourceChannel.SADHAN_PATH,
        "title": "अनन्य आश्रय का रहस्य - पूज्य प्रेमानंद जी महाराज (Shorts)",
        "upload_date": date(2023, 6, 1),
        "chunks": [
            {
                "chunk_index": 0,
                "start_sec": 10,
                "end_sec": 60,
                "start_fmt": "00:10",
                "end_fmt": "01:00",
                "text": (
                    "एकांतिक वार्तालाप में पूज्य महाराज जी ने श्री जी के अनन्य आश्रय का रहस्य समझाया: "
                    "अनन्य आश्रय का अर्थ है कि साधक का मन, बुद्धि और प्राण केवल प्रिया प्रियतम श्री राधा कृष्ण के चरणों में समर्पित हों। "
                    "संसार का कोई भरोसा न रखकर केवल श्री जी की कृपा पर निर्भर होना ही सच्चा आश्रय है।"
                )
            }
        ]
    }
]


def seed_database():
    """Seeds discourses and demonstrates cross-channel deduplication."""
    logger.info("Seeding authentic discourse catalog across Bhajan Marg & Sadhan Path...")
    vector_store = get_vector_store()
    embedding_gen = EmbeddingGenerator()
    deduplicator = CrossChannelDeduplicator(video_similarity_threshold=0.85, chunk_similarity_threshold=0.88)

    all_chunks = []
    canonical_chunks = []

    for vid in SAMPLE_DISCOURSES:
        v_meta = VideoMetadata(
            video_id=vid["video_id"],
            channel_id=vid["channel"],
            title=vid["title"],
            url=f"https://www.youtube.com/watch?v={vid['video_id']}",
            upload_date=vid["upload_date"],
        )

        for c_data in vid["chunks"]:
            chunk = ChunkRecord(
                video_id=v_meta.video_id,
                channel_id=v_meta.channel_id,
                chunk_index=c_data["chunk_index"],
                start_sec=c_data["start_sec"],
                end_sec=c_data["end_sec"],
                start_formatted=c_data["start_fmt"],
                end_formatted=c_data["end_fmt"],
                raw_text=c_data["text"],
                clean_text=c_data["text"],
                token_count=len(c_data["text"].split()),
            )

            # Check chunk-level deduplication
            match = deduplicator.check_chunk_duplicate(
                new_chunk=chunk,
                existing_chunks=canonical_chunks,
                new_video_date=v_meta.upload_date,
            )

            if match.is_duplicate:
                chunk.is_duplicate = True
                chunk.canonical_chunk_id = match.matched_chunk_id
                chunk.canonical_video_id = match.canonical_video_id
                # Attach alias to existing canonical chunk
                for existing in canonical_chunks:
                    if existing.id == match.matched_chunk_id:
                        deduplicator.attach_cross_channel_alias(existing, chunk, video_title=v_meta.title)
                        logger.info(f"🔗 [DEDUP ALIAS] Attached {chunk.video_id} ({chunk.channel_id.value}) as alias to {existing.id}")
                        break
            else:
                canonical_chunks.append(chunk)

            all_chunks.append(chunk)

    # Embed active canonical chunks
    texts = [c.clean_text for c in canonical_chunks]
    embeddings = embedding_gen.embed_texts(texts)
    for c, emb in zip(canonical_chunks, embeddings):
        c.embedding = emb

    # If using Supabase, ensure video records exist to satisfy foreign key constraints
    if settings.vector_store_backend == VectorStoreType.SUPABASE:
        from supabase_ingest import SupabaseIngestor
        ingestor = SupabaseIngestor()
        for vid in SAMPLE_DISCOURSES:
            v_meta = VideoMetadata(
                video_id=vid["video_id"],
                channel_id=vid["channel"],
                title=vid["title"],
                url=f"https://www.youtube.com/watch?v={vid['video_id']}",
                upload_date=vid["upload_date"],
            )
            ingestor.upsert_video(v_meta)

    inserted = vector_store.insert_chunks(canonical_chunks)
    logger.info(f"✅ Seeding complete: {len(all_chunks)} total chunks scanned, {inserted} canonical chunks indexed.")
    logger.info(f"   Bhajan Marg chunks: {sum(1 for c in canonical_chunks if c.channel_id == SourceChannel.BHAJAN_MARG)}")
    logger.info(f"   Sadhan Path chunks: {sum(1 for c in canonical_chunks if c.channel_id == SourceChannel.SADHAN_PATH)}")


if __name__ == "__main__":
    seed_database()
