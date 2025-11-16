FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Taipei

# 先進到 /app/backend，之後這裡就是你的後端根目錄
WORKDIR /app/backend

#  安裝 uv
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir uv

# 複製 backend 的依賴定義檔（利用 Docker cache）
COPY backend/pyproject.toml backend/uv.lock* /app/backend/

#  用 uv 安裝依賴（在 /app/backend 裡建立 .venv）
#    - --frozen：照 uv.lock 鎖死版本（前提是你有 commit uv.lock）
#    - --no-dev：如果未來有 dev-dependencies，就不會裝進正式 image
RUN uv sync --frozen --no-dev

#  複製實際後端程式碼
COPY backend/ /app/backend/

#  複製 static / image 到 /app 底下，維持原來的相對位置
COPY static/ /app/static/
COPY image/  /app/image/

EXPOSE 8000

#  用 uv run 啟動，會自動使用 /app/backend/.venv 裡的環境
#    你的 main 在 backend/app/main.py → 模組路徑是 app.main:app
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
