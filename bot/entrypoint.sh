#!/bin/sh
set -e

# SSH requires strict ownership and permissions.
# We mount the host ~/.ssh as read-only to /root/.ssh-ro, then copy
# it here so we can apply the correct permissions inside the container.
if [ -d /root/.ssh-ro ]; then
    rm -rf /root/.ssh
    cp -r /root/.ssh-ro /root/.ssh
    find /root/.ssh -type d -exec chmod 700 {} \;
    find /root/.ssh -type f -exec chmod 600 {} \;
    echo "[entrypoint] SSH permissions fixed."
fi

exec python main.py
