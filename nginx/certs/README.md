# Certificats TLS

Ce dossier doit contenir les certificats TLS pour HTTPS.

## Let's Encrypt (recommandé)

```bash
certbot certonly --standalone -d zsdevweb.com -d www.zsdevweb.com

# Copier les fichiers :
cp /etc/letsencrypt/live/zsdevweb.com/fullchain.pem ./nginx/certs/fullchain.pem
cp /etc/letsencrypt/live/zsdevweb.com/privkey.pem   ./nginx/certs/privkey.pem
```

## Développement local (auto-signé)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem -out fullchain.pem \
  -subj "/CN=localhost"
```

## Fichiers attendus

- `fullchain.pem` — certificat + chaîne intermédiaire
- `privkey.pem`   — clé privée (NE PAS committer)
