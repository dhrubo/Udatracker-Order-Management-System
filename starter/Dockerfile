# Lightweight image for running Udatracker locally (the Udacity Workspace
# already runs in Docker, so this is only for local development).
#
#   docker build -t udatracker .
#   docker run --rm -p 5000:5000 udatracker      # app on http://127.0.0.1:5000
#   docker run --rm udatracker pytest            # run the test suite
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home appuser
WORKDIR /app
RUN chown appuser /app

# Install dependencies first so this layer is cached between code changes.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY --chown=appuser . .
USER appuser

EXPOSE 5000

# Bind to 0.0.0.0 so the server is reachable from outside the container.
CMD ["flask", "--app", "backend.app", "run", "--host", "0.0.0.0", "--port", "5000"]
