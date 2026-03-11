# VPS deployment (bakaya.tech + SSL)

This guide publishes Detectish behind **host Nginx** with a Let's Encrypt certificate.

## 1) DNS and firewall

- Point `A` records to your VPS public IP:
  - `bakaya.tech`
  - `www.bakaya.tech`
- Open inbound ports `80` and `443` on your VPS/security group.

## 2) Server prerequisites (Ubuntu)

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx docker.io docker-compose-plugin git
sudo systemctl enable --now docker nginx
```

## 3) Pull code and set env

```bash
cd /opt
sudo git clone <your-repo-url> emailfilter
cd emailfilter/detectish
sudo cp .env.example .env 2>/dev/null || true
sudo nano .env
```

Set production secrets in `.env` (at least `JWT_SECRET`, DB credentials, API keys).

## 4) Run app in production mode

```bash
cd /opt/emailfilter/detectish
sudo docker compose -f docker-compose.yml -f deploy/vps/docker-compose.prod.yml up -d --build
```

This binds app frontend only to `127.0.0.1:8080` and keeps internal services off public ports.

## 5) Configure Nginx reverse proxy

```bash
cd /opt/emailfilter/detectish
sudo cp deploy/vps/nginx/bakaya.tech.conf /etc/nginx/sites-available/bakaya.tech
sudo ln -sf /etc/nginx/sites-available/bakaya.tech /etc/nginx/sites-enabled/bakaya.tech
sudo nginx -t
sudo systemctl reload nginx
```

## 6) Issue SSL certificate

```bash
sudo certbot --nginx -d bakaya.tech -d www.bakaya.tech --redirect -m admin@bakaya.tech --agree-tos --no-eff-email
```

## 7) Verify

- `https://bakaya.tech`
- `sudo docker compose -f docker-compose.yml -f deploy/vps/docker-compose.prod.yml ps`
- `sudo systemctl status nginx`

## Updates

```bash
cd /opt/emailfilter
sudo git pull
cd detectish
sudo docker compose -f docker-compose.yml -f deploy/vps/docker-compose.prod.yml up -d --build
```
