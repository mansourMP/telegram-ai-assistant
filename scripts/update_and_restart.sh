#!/bin/bash
set -e
cd /opt/mansur-assistant
git pull
./venv/bin/pip install -e .
systemctl restart mansur-assistant
echo "Update and restart complete."
