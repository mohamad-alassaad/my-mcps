FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./

ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=8081 \
    OLLAMA_HOST=http://ollama:11434 \
    OLLAMA_MODEL=gemma3:4b

EXPOSE 8081

CMD ["python", "server.py"]
