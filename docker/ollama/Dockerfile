FROM ollama/ollama:latest

# Installa curl per i test
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia lo script di avvio
COPY entrypoint_ollama.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Espone la porta
EXPOSE 11434

# Volume per i modelli
VOLUME ["/root/.ollama"]

# Usa lo script di entrypoint
ENTRYPOINT ["/entrypoint.sh"]