# CHCP - 用户认证 & 积分系统

基于 **Clerk** 认证 + **Supabase Cloud** 数据库的用户注册积分系统。

## 项目结构

```
chcp/
├── backend/
│   ├── app.py                # Flask 入口
│   ├── config.py             # 配置
│   ├── db.py                 # Supabase 客户端
│   ├── schema.sql            # 数据库建表 SQL
│   ├── .env.example          # 环境变量模板
│   ├── requirements.txt      # Python 依赖
│   ├── utils/auth.py         # Clerk JWT 验证
│   └── controllers/
│       ├── webhook_controller.py  # Clerk Webhook
│       └── user_controller.py     # 用户 API
└── frontend/
    ├── index.html            # 单页应用
    ├── css/style.css         # 暗色主题
    └── js/app.js             # 前端逻辑
```

## 快速开始

### 1. 创建 Supabase 项目
1. 访问 [supabase.com](https://supabase.com)，注册并创建项目
2. 进入 **SQL Editor**，粘贴 `backend/schema.sql` 并运行
3. 进入 **Settings → API**，复制 **Project URL** 和 **service_role key**

### 2. 创建 Clerk 应用
1. 访问 [clerk.com](https://clerk.com)，注册并创建应用
2. 记录 **Publishable Key** 和 **Domain**

### 3. 配置环境变量
```bash
cd backend
copy .env.example .env
# 编辑 .env，填入 Supabase 和 Clerk 的配置
```

### 4. 配置前端 Clerk Key
编辑 `frontend/index.html`，在 Clerk script 标签中填入 Publishable Key：
```html
<script data-clerk-publishable-key="pk_test_你的key" ...>
```

### 5. 安装依赖并启动
```bash
pip install -r requirements.txt
python app.py
```
访问 http://localhost:5000

### 6. 配置 Clerk Webhook
1. Clerk Dashboard → **Webhooks** → **Add Endpoint**
2. URL: `https://你的公网地址/webhooks/clerk`
3. 订阅事件: `user.created`, `user.updated`, `user.deleted`
4. 复制 Signing Secret 到 `.env` 的 `CLERK_WEBHOOK_SECRET`

> 💡 本地开发用 [ngrok](https://ngrok.com) 暴露端口给 Clerk 回调

## 功能
- 🔐 Clerk 登录/注册
- 🎉 注册赠送 50 积分
- 👤 用户信息展示
- 📋 积分流水记录
- 🚪 退出登录
