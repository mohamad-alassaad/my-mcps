FROM ollama/ollama:latest

# Copy the script into the image
COPY entrypoint.sh /entrypoint.sh

# Ensure it has execution permissions
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]