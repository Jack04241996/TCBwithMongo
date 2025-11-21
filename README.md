## Project structure

```text
.
├── .vscode/
│   └── launch.json              # VS Code debug 設定
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── route/
│   │   │       ├── login.py
│   │   │       ├── users.py
│   │   │       ├── products.py
│   │   │       ├── products_management.py
│   │   │       └── register.py
│   │   ├── core/
│   │   │   ├── ECpay/
│   │   │   │   ├── ECPay_AIO.py
│   │   │   │   └── ECPay.sdk
│   │   │   ├── config.py        # 設定 & 環境變數
│   │   │   ├── db.py            # DB 連線
│   │   │   ├── security.py      # 加解密 / JWT
│   │   │   └── paths.py         # 路徑 & 靜態檔設定
│   │   ├── crud.py              # 資料庫 CRUD 操作
│   │   ├── main.py              # FastAPI app 入口
│   │   ├── models.py            # Pydantic / ORM models
│   │   └── prestarts.py         # 啟動前檢查
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── static/                  # 前端 HTML / JS / CSS
│   └── image/                   # 商品圖片等靜態資源
├── .gitignore
├── .dockerignore
├── .env                         # 本機環境變數（不入版控）
└── Dockerfile
