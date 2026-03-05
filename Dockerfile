# ---------- FRONT BUILD ----------
FROM node:20-alpine AS front-build
WORKDIR /front
COPY front/package*.json ./
RUN npm ci
COPY front/ .
RUN npm run build


# ---------- FINAL (PYTHON + NGINX) ----------
FROM python:3.12-slim

WORKDIR /app

# install nginx + build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx curl build-essential \
  && rm -rf /var/lib/apt/lists/*

# python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download fr_core_news_sm

# app code
COPY src /app/src

# front build to nginx web root
COPY --from=front-build /front/dist /usr/share/nginx/html

# nginx config
COPY nginx.prod.conf /etc/nginx/nginx.conf

EXPOSE 80

# run backend + nginx
CMD sh -c "uvicorn src.main:app --host 0.0.0.0 --port 8000 --root-path /api & nginx -g 'daemon off;'"