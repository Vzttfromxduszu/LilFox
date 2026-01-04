# LilFox 部署指南

## 目录

- [系统要求](#系统要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [Kubernetes 部署](#kubernetes-部署)
- [配置管理](#配置管理)
- [故障排查](#故障排查)

## 系统要求

### 最低配置

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+), Windows 10+, macOS 10.15+
- **Python**: 3.9+
- **Node.js**: 16+ (前端)
- **内存**: 4GB RAM
- **磁盘**: 10GB 可用空间

### 推荐配置

- **操作系统**: Linux (Ubuntu 22.04 LTS)
- **Python**: 3.10+
- **Node.js**: 18+ (前端)
- **内存**: 8GB RAM
- **磁盘**: 50GB 可用空间
- **CPU**: 4核心

### 依赖服务

- **数据库**: PostgreSQL 12+ (生产环境) 或 SQLite (开发环境)
- **缓存**: Redis 6+ (可选，用于生产环境)
- **反向代理**: Nginx 1.18+ (推荐)

## 开发环境部署

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/LilFox.git
cd LilFox
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制开发环境配置
cp .env.development .env

# 编辑配置文件
# 根据需要修改 .env 文件中的配置项
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
cd backend
python -m alembic upgrade head
```

### 5. 启动服务

使用一键启动脚本:

```bash
python scripts/start_all.py
```

或手动启动各个服务:

```bash
# 终端 1: 启动后端服务
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2: 启动模型服务
cd model_service
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 终端 3: 启动网关服务
cd gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# 终端 4: 启动前端 (可选)
cd frontend
npm install
npm run dev
```

### 6. 验证部署

访问以下 URL 验证服务是否正常运行:

- 网关: http://localhost:8080
- 后端: http://localhost:8000
- 模型服务: http://localhost:8001
- 前端: http://localhost:3000

## 生产环境部署

### 1. 系统准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y python3 python3-pip python3-venv nginx postgresql redis-server

# 创建应用用户
sudo useradd -m -s /bin/bash lilfox
sudo su - lilfox
```

### 2. 部署代码

```bash
# 克隆或上传代码
cd /home/lilfox
git clone https://github.com/yourusername/LilFox.git
cd LilFox

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置数据库

```bash
# 创建数据库
sudo -u postgres psql
CREATE DATABASE lilfox;
CREATE USER lilfox WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE lilfox TO lilfox;
\q

# 运行数据库迁移
cd backend
source /home/lilfox/LilFox/venv/bin/activate
python -m alembic upgrade head
```

### 4. 配置环境变量

```bash
# 复制生产环境配置
cp .env.production .env

# 编辑配置文件
nano .env
```

关键配置项:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://lilfox:your_password@localhost:5432/lilfox
SECRET_KEY=your-very-long-and-secure-secret-key
OPENAI_API_KEY=your-openai-api-key
```

### 5. 配置 Systemd 服务

创建网关服务:

```bash
sudo nano /etc/systemd/system/lilfox-gateway.service
```

```ini
[Unit]
Description=LilFox API Gateway
After=network.target

[Service]
Type=simple
User=lilfox
WorkingDirectory=/home/lilfox/LilFox/gateway
Environment="PATH=/home/lilfox/LilFox/venv/bin"
ExecStart=/home/lilfox/LilFox/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

创建后端服务:

```bash
sudo nano /etc/systemd/system/lilfox-backend.service
```

```ini
[Unit]
Description=LilFox Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=lilfox
WorkingDirectory=/home/lilfox/LilFox/backend
Environment="PATH=/home/lilfox/LilFox/venv/bin"
ExecStart=/home/lilfox/LilFox/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

创建模型服务:

```bash
sudo nano /etc/systemd/system/lilfox-model.service
```

```ini
[Unit]
Description=LilFox Model Service
After=network.target

[Service]
Type=simple
User=lilfox
WorkingDirectory=/home/lilfox/LilFox/model_service
Environment="PATH=/home/lilfox/LilFox/venv/bin"
ExecStart=/home/lilfox/LilFox/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable lilfox-gateway lilfox-backend lilfox-model
sudo systemctl start lilfox-gateway lilfox-backend lilfox-model

# 检查服务状态
sudo systemctl status lilfox-gateway
sudo systemctl status lilfox-backend
sudo systemctl status lilfox-model
```

### 6. 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/lilfox
```

```nginx
upstream lilfox_backend {
    server 127.0.0.1:8000;
}

upstream lilfox_model {
    server 127.0.0.1:8001;
}

upstream lilfox_gateway {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://lilfox_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /backend/ {
        proxy_pass http://lilfox_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /model/ {
        proxy_pass http://lilfox_model/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/lilfox /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. 配置 SSL (使用 Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx

sudo certbot --nginx -d yourdomain.com
```

## Docker 部署

### 1. 构建镜像

```bash
# 构建后端镜像
docker build -t lilfox-backend:latest -f backend/Dockerfile .

# 构建模型服务镜像
docker build -t lilfox-model:latest -f model_service/Dockerfile .

# 构建网关镜像
docker build -t lilfox-gateway:latest -f gateway/Dockerfile .

# 构建前端镜像 (可选)
docker build -t lilfox-frontend:latest -f frontend/Dockerfile .
```

### 2. 使用 Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: lilfox
      POSTGRES_USER: lilfox
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    image: lilfox-backend:latest
    environment:
      - DATABASE_URL=postgresql://lilfox:your_password@postgres:5432/lilfox
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"

  model:
    image: lilfox-model:latest
    environment:
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - redis
    ports:
      - "8001:8001"

  gateway:
    image: lilfox-gateway:latest
    environment:
      - BACKEND_URL=http://backend:8000
      - MODEL_URL=http://model:8001
    depends_on:
      - backend
      - model
    ports:
      - "8080:8080"

  frontend:
    image: lilfox-frontend:latest
    ports:
      - "3000:80"
    depends_on:
      - gateway

volumes:
  postgres_data:
```

启动服务:

```bash
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## Kubernetes 部署

### 1. 创建命名空间

```bash
kubectl create namespace lilfox
```

### 2. 创建 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: lilfox-config
  namespace: lilfox
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
```

### 3. 创建 Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: lilfox-secret
  namespace: lilfox
type: Opaque
stringData:
  DATABASE_URL: "postgresql://lilfox:password@postgres:5432/lilfox"
  SECRET_KEY: "your-secret-key"
  OPENAI_API_KEY: "your-openai-api-key"
```

### 4. 部署后端服务

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: lilfox
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: lilfox-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: lilfox-config
        - secretRef:
            name: lilfox-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: lilfox
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
```

### 5. 部署网关服务

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: lilfox
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: lilfox-gateway:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: lilfox-config
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: lilfox
spec:
  selector:
    app: gateway
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

### 6. 应用配置

```bash
kubectl apply -f k8s/
```

## 配置管理

### 使用配置工具

```bash
# 验证配置
python scripts/config_tool.py validate

# 显示配置
python scripts/config_tool.py show

# 导出配置
python scripts/config_tool.py export --config gateway --output config/gateway.json

# 切换环境
python scripts/config_tool.py switch production
```

### 环境变量优先级

1. 命令行参数
2. 环境变量
3. .env 文件
4. 配置类默认值

## 故障排查

### 服务无法启动

```bash
# 检查服务状态
sudo systemctl status lilfox-gateway

# 查看日志
sudo journalctl -u lilfox-gateway -f

# 检查端口占用
sudo netstat -tlnp | grep :8080
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 测试连接
psql -U lilfox -d lilfox -h localhost

# 检查数据库日志
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### 性能问题

```bash
# 检查系统资源
htop

# 检查磁盘使用
df -h

# 检查内存使用
free -m

# 检查网络连接
netstat -an | grep ESTABLISHED | wc -l
```

### 日志分析

```bash
# 查看网关日志
tail -f /var/log/lilfox/gateway.log

# 查看后端日志
tail -f /var/log/lilfox/backend.log

# 查看模型服务日志
tail -f /var/log/lilfox/model.log

# 搜索错误
grep -i error /var/log/lilfox/*.log
```

### 常见错误

**错误: Connection refused**

- 检查服务是否正在运行
- 检查防火墙设置
- 验证端口配置

**错误: Authentication failed**

- 验证 JWT 密钥配置
- 检查 token 是否过期
- 验证用户凭据

**错误: Rate limit exceeded**

- 调整限流配置
- 检查是否有异常流量
- 考虑增加限流阈值

**错误: Database connection error**

- 检查数据库服务状态
- 验证连接字符串
- 检查数据库权限
