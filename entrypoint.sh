#!/bin/bash
#!/bin/bash

# Inject SSH public key if provided via env
if [ -n "$SSH_PUB_KEY" ]; then
  echo "[INFO] Injecting SSH key for dev user"
  mkdir -p /home/dev/.ssh
  echo "$SSH_PUB_KEY" >> /home/dev/.ssh/authorized_keys
  chmod 700 /home/dev/.ssh
  chmod 600 /home/dev/.ssh/authorized_keys
  chown -R dev:dev /home/dev/.ssh
else
  echo "[WARN] No SSH_PUB_KEY provided — password login only (if enabled)"
fi

# Generate host keys if needed
ssh-keygen -A

# Start SSHD
exec /usr/sbin/sshd -D

echo "Container is ready, happy building!"
