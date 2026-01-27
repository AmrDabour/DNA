# Nginx Configuration for GenovaAI

## Overview

This directory contains the Nginx reverse proxy configuration for GenovaAI.

## Files

- `nginx.conf` - Main Nginx configuration
- `proxy_params` - Shared proxy settings
- `ssl/` - Directory for SSL certificates (not committed to git)

## Features

- **Reverse Proxy**: Routes requests to Flask/Gunicorn backend
- **Static File Serving**: Serves `/static/` files directly with caching
- **Rate Limiting**: 
  - API: 10 req/s with burst of 20
  - Upload: 2 req/s with burst of 5
- **Gzip Compression**: Enabled for text-based content
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **SSL Ready**: HTTPS configuration commented out, ready to enable

## SSL Setup (Production)

### Option 1: Let's Encrypt (Recommended)

```bash
# Install certbot
apt-get install certbot

# Get certificate (ensure DNS points to your server)
certbot certonly --webroot -w /var/www/certbot -d yourdomain.com

# Copy certificates to nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
```

### Option 2: Self-Signed (Development)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

### Enable HTTPS

1. Uncomment the HTTPS server block in `nginx.conf`
2. Uncomment the HTTP to HTTPS redirect
3. Restart Nginx: `docker-compose restart nginx`

## Rate Limiting

| Zone | Rate | Burst | Use Case |
|------|------|-------|----------|
| `api_limit` | 10/s | 20 | API endpoints |
| `upload_limit` | 2/s | 5 | File uploads |
| `conn_limit` | - | 20 | Connection limit |

Adjust these in `nginx.conf` based on your traffic patterns.

## Troubleshooting

```bash
# Check Nginx config syntax
docker-compose exec nginx nginx -t

# View Nginx logs
docker-compose logs nginx

# Reload Nginx config without restart
docker-compose exec nginx nginx -s reload
```


