FROM --platform=linux/amd64 python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/app/.hf
WORKDIR /app

COPY requirements.txt .
# CPU-only torch keeps the image several GB smaller than the default CUDA build
RUN pip install --no-cache-dir torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image so cold starts don't download it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('NeuML/bioclinical-modernbert-base-embeddings')"

COPY src ./src
COPY start.sh .

EXPOSE 8501
CMD ["sh", "start.sh"]

