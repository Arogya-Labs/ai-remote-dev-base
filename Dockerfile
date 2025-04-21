FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# --- System Dependencies (stable layer) ---
RUN apt-get update && apt-get install -y \
    curl openssh-server sudo build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Install Poetry globally (stable) ---
RUN curl -sSL https://install.python-poetry.org | python3

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
ENV PATH="/opt/poetry/bin:$PATH"
RUN poetry install --no-root || true  # tolerate missing lock file
RUN poetry --version

# --- Copy full app (only affects last layer rebuild) ---
COPY --chown=dev:dev . .

# --- Expose ports and set runtime ---
EXPOSE 22 3000

USER root
# Copy entrypoint and make executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
