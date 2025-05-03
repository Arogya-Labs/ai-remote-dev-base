FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# --- System Dependencies (stable layer) ---
RUN apt-get update && apt-get install -y \
    curl ca-certificates openssh-server sudo build-essential \
    cmake pkg-config libssl-dev libffi-dev libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# --- Install uv globally and test it ---
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
cp /root/.local/bin/uv /usr/local/bin/
RUN uv --version

# Step 4: Install a Python version using uv
RUN uv python install 3.12

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
RUN mkdir -p /home/dev/app && chown -R dev:dev /home/dev
WORKDIR /home/dev/app

# --- Copy full app (only affects last layer rebuild) ---
COPY --chown=dev:dev . .

# --- Expose ports and set runtime ---
EXPOSE 22 3000 11434

USER root
# Copy entrypoint and make executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
