FROM python:3.12-slim

# --- Certificados da rede corporativa -------------------------------------
# A rede faz inspeção de HTTPS e reassina o tráfego com um certificado próprio.
# Esse certificado está no repositório do Windows, mas não na imagem Linux, então
# sem este passo tanto o pip quanto as chamadas à AWS falham na validação SSL.
# Os arquivos em certs/ são gerados por `python export_windows_certs.py`.
# A verificação SSL continua ligada: estamos adicionando confiança, não desligando.
COPY certs/*.crt /usr/local/share/ca-certificates/
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Faz as bibliotecas Python (requests, botocore, urllib3) usarem o mesmo bundle
# do sistema, que agora inclui os certificados da rede.
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY collect.py sender.py rewrite_parquets.py main.py ./

# Os parquets vão para /app/data e o cache do fastf1 para /root/.fastf1,
# ambos montados como volumes pelo docker-compose.
RUN mkdir -p /app/data /root/.fastf1

CMD ["python", "sender.py"]
