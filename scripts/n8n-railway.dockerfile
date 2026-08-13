# Dockerfile separado para o n8n no Railway
# Use este arquivo ao criar o segundo serviço no Railway

FROM n8nio/n8n:latest

# Timezone Brasil
ENV GENERIC_TIMEZONE=America/Sao_Paulo
ENV TZ=America/Sao_Paulo
ENV N8N_DIAGNOSTICS_ENABLED=false
ENV N8N_HIRING_BANNER_ENABLED=false
ENV DB_TYPE=sqlite
ENV DB_SQLITE_DATABASE=/home/node/.n8n/database.sqlite

EXPOSE 5678

# Railway usa a variável PORT automaticamente
CMD ["sh", "-c", "n8n start --port ${PORT:-5678}"]
