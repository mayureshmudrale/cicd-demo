# Build context is the `ai/` directory itself (so this image gets the
# whole `ai` package — evaluator imports ai.routing imports ai.llm):
#   docker build -f ai/evaluator/Dockerfile -t ai-evaluator:local ai/
FROM python:3.12-slim

WORKDIR /app
COPY . ai/
RUN pip install --no-cache-dir -r ai/evaluator/requirements.txt

EXPOSE 8080
CMD ["uvicorn", "ai.evaluator.main:app", "--host", "0.0.0.0", "--port", "8080"]
