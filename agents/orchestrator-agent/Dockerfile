FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/ agent/
COPY ../knowledge/sparql/orchestrator/ knowledge/sparql/orchestrator/
CMD ["python", "-m", "agent.worker"]
