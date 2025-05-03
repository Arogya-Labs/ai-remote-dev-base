FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV POETRY_HOME="/opt/poetry"
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# --- System Dependencies (stable layer) ---
RUN apt-get update && apt-get install -y \
    curl openssh-server sudo build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Install Poetry globally and link to PATH ---
RUN curl -sSL https://install.python-poetry.org | python3 && \
    ln -s "${POETRY_HOME}/bin/poetry" /usr/local/bin/poetry
RUN poetry --version

# --- Install Ollama ---
RUN curl -fsSL https://ollama.com/install.sh | sh
RUN ollama --version

# --- Verify GPU Access ---
RUN nvidia-smi || (echo "GPU not accessible. Ensure NVIDIA drivers and container toolkit are installed. Won't exit build.")

# --- Create user (stable layer) ---
RUN useradd -ms /bin/bash dev && echo "dev:devpass" | chpasswd && adduser dev sudo

# --- SSH Setup (stable) ---
RUN mkdir /var/run/sshd && chmod 755 /var/run/sshd

# --- Create app directory and set workdir ---
WORKDIR /home/dev/app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# --- Copy only dependency files first (triggers poetry install layer only when deps change) ---
COPY --chown=dev:dev pyproject.toml poetry.lock* ./
RUN poetry install --no-root || true  # tolerate missing lock file

# --- Copy full app (only affects last layer rebuild) ---
COPY --chown=dev:dev . .

# --- Expose ports and set runtime ---
EXPOSE 22 3000 11434

USER root
# Copy entrypoint and make executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
