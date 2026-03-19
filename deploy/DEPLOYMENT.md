# Deployment Guide

## 1. VPS Setup (Run as Root)
```bash
# 1. System Prep
apt update && apt install -y python3-venv tesseract-ocr git

# 2. Setup Dedicated User
useradd -m -s /bin/bash mansurbot

# 3. Setup Project Dir
mkdir -p /opt/mansur-assistant
# (Copy your repo files here: scp -r . mansurbot@your_vps:/opt/mansur-assistant)
chown -R mansurbot:mansurbot /opt/mansur-assistant

# 4. Setup Python Venv
sudo -u mansurbot bash <<EOF
cd /opt/mansur-assistant
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -e .
EOF

# 5. Configure Security
sudo -u mansurbot chmod 600 /opt/mansur-assistant/.env

# 6. Service & Logging
cp deploy/mansur-assistant.service /etc/systemd/system/
cp deploy/logrotate.mansur-assistant /etc/logrotate.d/mansur-assistant
systemctl daemon-reload
systemctl enable mansur-assistant
systemctl start mansur-assistant
```

## 2. Validation
- Check service: `systemctl status mansur-assistant`
- Check logs: `tail -f /opt/mansur-assistant/data/assistant.log`
- Check admin: `/admin status` via Telegram.

## 3. Rollback
- If service fails: `systemctl stop mansur-assistant`, then revert Git commit: `git checkout <commit_hash>`.
- If data corruption: Extract latest backup: `tar -xzf backup_data_<timestamp>.tar.gz -C /opt/mansur-assistant/`.
