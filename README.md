TCBwithMongo

一個使用 FastAPI 框架 搭配 MongoDB 資料庫開發的後端系統，具備完整的使用者管理、商品管理與購物流程。

功能介紹：

1.使用者系統

    1-1 註冊、登入、登出

    1-2 權限控管（管理員可編輯/刪除所有使用者與商品）

2.商品管理 (CRUD)

    2-1 新增、編輯、刪除、列表

3.購物車機制

    3-1 使用 Session 追蹤購物內容

4.登入狀態與權限保護

    4-1Cookie & Session

    4-2Middleware 實作 RBAC（角色存取控制）

5.前端整合

    5-1使用 Jinja2 模板渲染頁面

🛠️ Tech Stack

Backend: FastAPI · Uvicorn

Database: MongoDB Atlas (Async PyMongo)

Auth: JWT (python-jose · HS256) · passlib/bcrypt

Validation: Pydantic v2

Infra: Docker · Amazon ECR · AWS App Runner (AutoScaling/TLS)

Config: python-dotenv

版本更新紀錄
v1.1（2025-09）

1. RESTful 重構：改為資源導向 API，統一 JSON 回應與狀態碼。

2. 認證與授權：JWT 驗證；中介層 + @require_level([2,3]) RBAC。

3. 資料模型與驗證：Pydantic v2 (RegisterData/LoginData/UserUpdate)，密碼加密採用 bcrypt+passlib。

4. 可維運：GET /health 健康檢查；啟動時 ping MongoDB 確認連線。

5. 雲端佈署：Docker 容器化 → ECR 版本管理 → AWS App Runner 佈署。

6. 安全性：MongoDB Atlas IP Access List，限制允許連線來源。

v1.2（2025-10，進行中）

1. 金流整合：串接 ECPay 全方位金流 API

    1-1 訂單建立、付款回調（notify/return）

    1-2 CheckMacValue 驗簽

    1-3 交易狀態更新

    1-4 支援信用卡、超商代碼、ATM 多元付款方式

    1-5 確保流程符合 冪等性 與 安全性

專案架構：

    TCBwithMongo/
    ├─ main.py              # FastAPI 主程式入口
    ├─ database.py          # MongoDB 連線與操作
    ├─ jwt_handler.py       # JWT 產生、驗證、加解密
    ├─ middleware.py        # Middleware：登入狀態與權限控管
    ├─ model.py             # Pydantic 資料模型 (User, Product, Login, Register)
    │
    ├─ requirements.txt     # Python 相依套件清單
    ├─ Dockerfile           # Docker 映像建置設定
    ├─ .gitignore           # Git 忽略清單
    ├─ .dockerignore        # Docker build 忽略清單
    ├─ .env.example         # 環境變數範本 (僅示意，不含敏感值)
    ├─ README.md            # 專案說明文件
    │
    ├─ static/              # 前端靜態資源 (CSS / JS / 圖示等)
    ├─ image/               # 商品圖片或其他圖檔
    ├─ ECPay/               # 綠界金流 API 串接程式 (排除憑證檔)
    │   └─ ecpay_payment_sdk.py
    │
    └─ __pycache__/         # Python 編譯快取檔 (已被 gitignore)
