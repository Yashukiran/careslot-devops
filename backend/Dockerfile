FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# upgrade the base image packages so the trivy scan doesn't flag already-fixed CVEs
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# pip/ensurepip are only needed at build time, and their vendored libs
# (urllib3, msgpack, setuptools) show up as HIGH findings in trivy
RUN pip install -r requirements.txt \
    && pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.12/ensurepip

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY start.sh .

# run as an unprivileged user
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin careslot \
    && chmod +x start.sh \
    && chown -R careslot:careslot /app
USER 10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["./start.sh"]
