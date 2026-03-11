FROM python:3.14-slim

# System deps: ffmpeg + fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        fonts-liberation \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project (no lockfile — resolves fresh with the right torch variant)
COPY pyproject.toml README.md LICENSE ./
COPY aipoop/ aipoop/

# Build arg: cpu (default) or cu126 for CUDA
ARG TORCH_VARIANT=cpu
RUN UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/${TORCH_VARIANT} \
    uv sync --no-dev

# Output goes to /output (mount a volume here)
RUN mkdir -p /output

ENTRYPOINT ["uv", "run", "aipoop"]
