#!/bin/sh
# Bu script, konteyner başladığında çalışır.

# Hugging Face cache dizininin var olduğundan ve appuser'a ait olduğundan emin ol.
# HF_HOME ortam değişkeni Dockerfile tarafından ayarlanmıştır.
echo "Entrypoint: Ensuring cache directory permissions for ${HF_HOME}..."
mkdir -p "${HF_HOME}"
sudo chown -R appuser:appgroup "${HF_HOME}"
echo "Entrypoint: Permissions set."

# Asıl komutu "appuser" olarak çalıştır.
# `exec "$@"` ifadesi, Dockerfile'daki CMD'den gelen tüm argümanları alır ve çalıştırır.
exec gosu appuser "$@"