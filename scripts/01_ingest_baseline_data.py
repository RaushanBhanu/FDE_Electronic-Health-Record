import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

def ingest_data():
    # Load environment variables
    load_dotenv()

    # 1. Dynamically resolve project root based on this script's location
    script_dir = Path(__file__).resolve().parent       # .../FDE_EHR(Electronic Health Record)/scripts
    project_root = script_dir.parent                   # .../FDE_EHR(Electronic Health Record)

    # 2. Build absolute paths to data and schema
    csv_path = project_root / 'data' / 'MIMIC_IV_Trasncript.csv'        # .../FDE_EHR(Electronic Health Record)/data/MIMIC_IV_Trasncript.csv
    schema_path = project_root / 'src' / 'database' / 'schema.sql'      # .../FDE_EHR(Electronic Health Record)/data/MIMIC_IV_Trasncript.csv

    # Verify the file actually exists before trying to read it
    if not csv_path.exists():
        raise FileNotFoundError(f"CRITICAL: Could not find dataset at {csv_path}")
        
    db_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url)
    
    print(f"Executing schema setup from:\n  {schema_path}")
    with engine.begin() as conn:
        with open(schema_path, 'r') as file:
            conn.execute(text(file.read()))
            
    print(f"Loading clinical data from:\n  {csv_path}")
    df = pd.read_csv(csv_path)
    # Replace NaN/NaT with None so SQLAlchemy inserts SQL NULLs instead of breaking
    df = df.where(pd.notnull(df), None)
    
    print(f"Ingesting {len(df)} records into Supabase instance...")
    df.to_sql('patient_encounters', engine, if_exists='append', index=False)
    
    print("✅ Baseline legacy data ingestion complete.")

if __name__ == "__main__":
    ingest_data()