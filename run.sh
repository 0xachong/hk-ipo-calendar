#!/bin/bash
set -e
cd "$(dirname "$0")"

source .venv/bin/activate

# 加载 secrets (FEISHU_WEBHOOK_URL)
if [ -f /home/ubuntu/.config/hk-ipo/secrets.env ]; then
    source /home/ubuntu/.config/hk-ipo/secrets.env
fi

python fetch.py
python build_ics.py data/ipo.json ipo.ics

if [ -n "$(git status --porcelain ipo.ics)" ]; then
    COUNT=$(python -c "import json; print(len(json.load(open(\"data/ipo.json\"))))")
    git add ipo.ics
    git commit -m "update: $(date -u +%Y-%m-%dT%H:%MZ) | $COUNT IPOs"
    git push
    if [ -n "$FEISHU_WEBHOOK_URL" ]; then
        curl -s -X POST -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"港股IPO日历更新: $COUNT 只 | $(date "+%m-%d %H:%M")\"}}" \
            "$FEISHU_WEBHOOK_URL" > /dev/null || true
    fi
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] pushed: $COUNT IPOs"
else
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] no change"
fi
