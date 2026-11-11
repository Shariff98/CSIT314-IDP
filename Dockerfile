# Builds the React app, then runs Flask (API + built React app) with gunicorn. Used by Render (render.yaml).
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=web /web/dist /app/frontend-dist
ENV FRONTEND_DIST=/app/frontend-dist PYTHONUNBUFFERED=1
# The free plan has no disk: rebuild the demo data on every start (fixed seed, so it is always the same).
# --timeout 60 leaves room for the two AI calls a chat message can make.
CMD ["sh", "-c", "python scripts/generate_data.py --size 20 && exec gunicorn 'app:create_app()' --bind 0.0.0.0:${PORT:-10000} --timeout 60"]
