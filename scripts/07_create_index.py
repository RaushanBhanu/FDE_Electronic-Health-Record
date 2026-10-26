import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def create_indexes():
    load_dotenv()

    db_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url)

    with engine.begin() as conn:
        print("Creating B-tree index on subject_id...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_patient_encounters_subject_id
            ON patient_encounters (subject_id);
        """))

        print("Creating HNSW index on clinical_embedding (cosine)...")
        # Parallel HNSW builds need a shared memory segment the size of
        # maintenance_work_mem, which exceeds what Supabase allows. Build serially.
        conn.execute(text("SET LOCAL max_parallel_maintenance_workers = 0;"))
        conn.execute(text("SET LOCAL maintenance_work_mem = '64MB';"))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_patient_encounters_embedding_hnsw
            ON patient_encounters
            USING hnsw (clinical_embedding vector_cosine_ops);
        """))

        conn.execute(text("ANALYZE patient_encounters;"))

    print("✅ Indexes created.")

if __name__ == "__main__":
    create_indexes()
