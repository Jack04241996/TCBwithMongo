FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Taipei

WORKDIR /app

# 先複製 requirements 以利快取
COPY requirements.txt /app/requirements.txt

# 安裝 requirements
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 可選：快速健檢
RUN python - <<'PY'
try:
    import motor  # 若這裡成功代表你的 requirements 還殘留 motor
    raise SystemExit("❌ motor still installed; remove it from requirements.txt")
except Exception:
    pass
from pymongo import AsyncMongoClient
print("✅ PyMongo Async OK")
PY

# 再複製程式碼
COPY . /app

EXPOSE 8000

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]

