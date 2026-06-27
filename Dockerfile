FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git ca-certificates libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 \
    libdbus-1-3 libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libatk1.0-0 libcups2 libxshmfence1 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir nanobot-ai && \
    pip install --no-cache-dir playwright httpx beautifulsoup4 jinja2 && \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install chromium && \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install-deps chromium

COPY pyproject.toml /app/
COPY job_hunter_tools/ /app/job_hunter_tools/
RUN pip install --no-cache-dir /app

COPY templates/ /app/templates/

RUN useradd -m -u 1000 -s /bin/bash nanobot && \
    mkdir -p /home/nanobot/.nanobot/workspace && \
    chown -R nanobot:nanobot /home/nanobot

COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER nanobot
ENV HOME=/home/nanobot
ENV JOB_HUNTER_TEMPLATES=/app/templates
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
WORKDIR /home/nanobot

EXPOSE 18790 8765

ENTRYPOINT ["entrypoint.sh"]
CMD ["gateway"]
