# Zero-Trust Clinical EHR Chat

Chat with a patient's electronic health record (MIMIC-IV) in plain English. Answers are grounded in that patient's records only, with PII redacted before anything reaches the LLM and guardrails blocking medical advice.

```
Streamlit UI ──► FastAPI /api/v1/chat
                   │ 1. embed question (BioClinical ModernBERT, local)
                   │ 2. pgvector similarity search, scoped to patient_id
                   │ 3. Presidio redacts free-text fields (comments, description)
                   │ 4. NeMo Guardrails ──► Gemini
                   ▼
                 answer + disclaimer
```

## Tech stack

| Layer | Tool |
|---|---|
| Database | Postgres + pgvector (Supabase) |
| Embeddings | `NeuML/bioclinical-modernbert-base-embeddings` (768-dim, runs locally) |
| PII redaction | Microsoft Presidio + spaCy `en_core_web_lg` |
| Guardrails / LLM | NVIDIA NeMo Guardrails → Google Gemini via LangChain |
| API / UI | FastAPI, Streamlit |

## Project structure

```
data/                      dataset (not in git, see dataRequired.txt)
scripts/                   one-time setup and smoke tests (run in order)
src/
  api/main.py              FastAPI app
  PII_redaction/           Presidio redactor
  guardrails/              NeMo config.yml + Colang flows (rails.co)
  database/schema.sql      patient_encounters table
  ui/app.py                Streamlit chat UI
```

## Setup

### 1. Prerequisites
- Python 3.14 and [uv](https://docs.astral.sh/uv/)
- A [Supabase](https://supabase.com) project (or any Postgres with the `vector` extension)
- A Google Gemini API key

### 2. Install

```bash
uv venv
uv pip install -r requirements.txt
```

> This venv has no `pip`, so use `uv pip install`. Plain `pip` installs into your system Python instead.

### 3. Configure `.env`

```bash
cp .env.example .env
```

Then fill in your Supabase connection details and Gemini API key.

### 4. Get the dataset

Download the MIMIC-IV cleaned transcripts from [Kaggle](https://www.kaggle.com/datasets/isaacritharson/mimic-iv-cleaned-medical-transcripts) and save it as `data/MIMIC_IV_Trasncript.csv`.

### 5. Load the database

Run from the project root, in order:

| Script | What it does |
|---|---|
| `scripts/01_ingest_baseline_data.py` | Creates `patient_encounters` and loads the CSV |
| `scripts/02_verify_ingestion.py` | Checks the load |
| `scripts/03_apply_vector_schema.py` | Enables pgvector, adds the `clinical_embedding` column |
| `scripts/04_generate_embeddings.py` | Embeds records (set `demo_limit` in the script; default is 2 rows) |
| `scripts/05_test_vector_search.py` | Smoke-tests similarity search |
| `scripts/06_test_guardrails.py` | Smoke-tests guardrails |

```bash
.venv/bin/python scripts/01_ingest_baseline_data.py
```

Only patients with embeddings appear in the UI.

## Run

In two terminals:

```bash
uvicorn src.api.main:app --reload     # API on http://localhost:8000
streamlit run src/ui/app.py           # UI on http://localhost:8501
```

The first API start downloads the embedding model, which takes a while.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/patients` | Patients that have embeddings |
| POST | `/api/v1/chat` | Chat over one patient's records |
| POST | `/api/v1/clinical-query` | Mock-context endpoint for testing redaction and guardrails |

Example `POST /api/v1/chat` body (`patient_id` must be numeric; the last message is the question):

```json
{
  "patient_id": "10004720",
  "messages": [
    { "role": "user", "content": "What medication was prescribed at discharge?" }
  ]
}
```

Interactive docs: http://localhost:8000/docs

## Safety design

- **Patient scoping:** vector search is filtered by `subject_id`, so one patient's records never leak into another's answer.
- **PII redaction:** Presidio masks names, phone numbers, emails, SSNs, locations, organisations and dates in free-text fields. Coded fields (drug, route, test) are left as they are, because general-English NER mislabels them (e.g. `Famotidine` → `<PERSON>`).
- **Guardrails:** requests for diagnoses or medication changes get a fixed refusal; answers must come from the provided records.
- **Disclaimer:** the UI adds an "AI generated summary" notice to every answer.

## Troubleshooting

| Error | Fix |
|---|---|
| `No default base_url for provider 'google_genai'` | NeMo must use the LangChain framework. `main.py` calls `set_default_framework("langchain")`; for other scripts, add `NEMOGUARDRAILS_LLM_FRAMEWORK=langchain` to `.env` |
| `Action '...' not found` | A Colang flow in `rails.co` calls `execute <action>` with no matching `actions.py` |
| `422` from `/api/v1/chat` | Body isn't valid JSON or a field name is wrong |
| `No module named psycopg2` | `uv pip install -r requirements.txt` |

## Compliance

This is a learning project built on de-identified MIMIC-IV data. It is not certified for real patient data. See [HIPAA compliance](https://compliancy-group.com/what-is-hipaa-compliance/).
