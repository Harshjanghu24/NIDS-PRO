FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching — only re-runs when
# requirements.txt changes, not on every code edit)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the production code (filtered by .dockerignore)
COPY . .

EXPOSE 5000

# Use gunicorn as the production WSGI server.
# This replaces `python app.py`'s built-in development server,
# which Flask itself warns should not be used in production.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
