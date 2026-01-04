# LilFox 运维手册

## 目录

- [系统监控](#系统监控)
- [日志管理](#日志管理)
- [备份与恢复](#备份与恢复)
- [性能优化](#性能优化)
- [安全加固](#安全加固)
- [版本更新](#版本更新)
- [应急响应](#应急响应)

## 系统监控

### 监控指标

#### 应用层指标

- **请求量**: QPS (每秒请求数)
- **响应时间**: P50, P95, P99 延迟
- **错误率**: 4xx, 5xx 错误占比
- **并发连接数**: 当前活跃连接数

#### 系统层指标

- **CPU 使用率**: 用户态、内核态、I/O 等待
- **内存使用率**: 物理内存、交换空间
- **磁盘 I/O**: 读写速率、IOPS
- **网络流量**: 入站、出站流量

#### 服务层指标

- **数据库连接池**: 活跃连接、空闲连接
- **缓存命中率**: Redis 命中率
- **队列长度**: 任务队列积压情况
- **熔断器状态**: 开启、半开、关闭

### 监控工具

#### Prometheus + Grafana

安装 Prometheus:

```bash
# 安装 Prometheus
sudo apt install -y prometheus

# 配置 Prometheus
sudo nano /etc/prometheus/prometheus.yml
```

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lilfox-gateway'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'

  - job_name: 'lilfox-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'lilfox-model'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
```

启动服务:

```bash
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

安装 Grafana:

```bash
sudo apt install -y grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

访问 Grafana: http://localhost:3000 (默认用户名/密码: admin/admin)

#### 自定义监控脚本

创建监控脚本 `scripts/monitor.py`:

```python
import psutil
import requests
import time
from datetime import datetime
import json

def check_service_health(url: str) -> dict:
    """检查服务健康状态"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def get_system_metrics() -> dict:
    """获取系统指标"""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "percent": psutil.disk_usage('/').percent
        },
        "network": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv
        }
    }

def main():
    services = {
        "gateway": "http://localhost:8080",
        "backend": "http://localhost:8000",
        "model": "http://localhost:8001"
    }
    
    while True:
        timestamp = datetime.now().isoformat()
        
        report = {
            "timestamp": timestamp,
            "services": {},
            "system": get_system_metrics()
        }
        
        for name, url in services.items():
            report["services"][name] = check_service_health(url)
        
        print(json.dumps(report, indent=2))
        
        # 写入日志文件
        with open("logs/monitor.log", "a") as f:
            f.write(json.dumps(report) + "\n")
        
        time.sleep(60)

if __name__ == "__main__":
    main()
```

### 告警规则

配置 Prometheus 告警规则:

```yaml
groups:
  - name: lilfox_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          summary: "High latency detected"
          
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
        annotations:
          summary: "High CPU usage"
          
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 10m
        annotations:
          summary: "High memory usage"
```

## 日志管理

### 日志配置

#### 结构化日志

配置 JSON 格式日志:

```python
import json
import logging
from datetime import datetime
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        return json.dumps(log_data)
```

#### 日志轮转

配置日志轮转:

```python
import logging.handlers

def setup_logging(app_name: str, log_dir: str = "logs"):
    """配置日志"""
    log_dir = Path(log_dir)
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    
    # 文件处理器 - 按大小轮转
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / f"{app_name}.log",
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=10
    )
    file_handler.setFormatter(JSONFormatter())
    
    # 文件处理器 - 按时间轮转
    time_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / f"{app_name}-daily.log",
        when="midnight",
        backupCount=30
    )
    time_handler.setFormatter(JSONFormatter())
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(time_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### 日志收集

#### ELK Stack

安装 Elasticsearch:

```bash
sudo apt install -y elasticsearch
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

安装 Logstash:

```bash
sudo apt install -y logstash
```

配置 Logstash:

```conf
input {
  file {
    path => "/var/log/lilfox/*.log"
    start_position => "beginning"
    codec => json
  }
}

filter {
  if [level] == "ERROR" {
    mutate { add_tag => ["error"] }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "lilfox-%{+YYYY.MM.dd}"
  }
}
```

安装 Kibana:

```bash
sudo apt install -y kibana
sudo systemctl start kibana
sudo systemctl enable kibana
```

访问 Kibana: http://localhost:5601

#### Loki + Grafana

安装 Loki:

```bash
wget https://github.com/grafana/loki/releases/download/v2.9.0/loki-linux-amd64.zip
unzip loki-linux-amd64.zip
sudo mv loki-linux-amd64 /usr/local/bin/loki
```

配置 Loki:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /tmp/loki/boltdb-shipper-active
    cache_location: /tmp/loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /tmp/loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

安装 Promtail:

```bash
wget https://github.com/grafana/loki/releases/download/v2.9.0/promtail-linux-amd64.zip
unzip promtail-linux-amd64.zip
sudo mv promtail-linux-amd64 /usr/local/bin/promtail
```

配置 Promtail:

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: lilfox
    static_configs:
      - targets:
          - localhost
        labels:
          job: lilfox
          __path__: /var/log/lilfox/*.log
```

### 日志分析

#### 错误日志统计

```python
import json
from collections import Counter
from pathlib import Path

def analyze_errors(log_file: str):
    """分析错误日志"""
    errors = []
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                if log.get("level") == "ERROR":
                    errors.append(log)
            except json.JSONDecodeError:
                continue
    
    # 按错误类型统计
    error_types = Counter()
    for error in errors:
        error_type = error.get("exception", {}).get("type", "Unknown")
        error_types[error_type] += 1
    
    print("错误类型统计:")
    for error_type, count in error_types.most_common():
        print(f"  {error_type}: {count}")
    
    # 按模块统计
    modules = Counter()
    for error in errors:
        modules[error.get("module", "unknown")] += 1
    
    print("\n错误模块统计:")
    for module, count in modules.most_common():
        print(f"  {module}: {count}")
```

#### 性能日志分析

```python
def analyze_performance(log_file: str):
    """分析性能日志"""
    response_times = []
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                if "response_time" in log:
                    response_times.append(log["response_time"])
            except json.JSONDecodeError:
                continue
    
    if not response_times:
        print("没有找到性能数据")
        return
    
    response_times.sort()
    n = len(response_times)
    
    print(f"总请求数: {n}")
    print(f"平均响应时间: {sum(response_times) / n:.3f}s")
    print(f"P50: {response_times[int(n * 0.5)]:.3f}s")
    print(f"P95: {response_times[int(n * 0.95)]:.3f}s")
    print(f"P99: {response_times[int(n * 0.99)]:.3f}s")
```

## 备份与恢复

### 数据库备份

#### PostgreSQL 备份

创建备份脚本 `scripts/backup_db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="lilfox"
DB_USER="lilfox"

mkdir -p $BACKUP_DIR

# 全量备份
pg_dump -U $DB_USER -h localhost -d $DB_NAME | gzip > $BACKUP_DIR/lilfox_$DATE.sql.gz

# 保留最近 30 天的备份
find $BACKUP_DIR -name "lilfox_*.sql.gz" -mtime +30 -delete

echo "备份完成: lilfox_$DATE.sql.gz"
```

定时备份:

```bash
# 添加到 crontab
0 2 * * * /path/to/scripts/backup_db.sh
```

#### 数据库恢复

```bash
# 解压备份文件
gunzip lilfox_20231230_020000.sql.gz

# 恢复数据库
psql -U lilfox -d lilfox -h localhost < lilfox_20231230_020000.sql
```

### 配置备份

```bash
#!/bin/bash

BACKUP_DIR="/backup/config"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份环境变量
cp .env $BACKUP_DIR/env_$DATE

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# 保留最近 7 天的备份
find $BACKUP_DIR -name "env_*" -mtime +7 -delete
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +7 -delete

echo "配置备份完成"
```

### 文件备份

```bash
#!/bin/bash

BACKUP_DIR="/backup/files"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz public/uploads/

# 保留最近 7 天的备份
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +7 -delete

echo "文件备份完成"
```

### 自动备份脚本

创建统一备份脚本 `scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_ROOT="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_ROOT/backup.log"

mkdir -p $BACKUP_ROOT

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

backup_database() {
    log "开始数据库备份..."
    bash scripts/backup_db.sh
    if [ $? -eq 0 ]; then
        log "数据库备份成功"
    else
        log "数据库备份失败"
        return 1
    fi
}

backup_config() {
    log "开始配置备份..."
    cp .env $BACKUP_ROOT/env_$DATE
    tar -czf $BACKUP_ROOT/config_$DATE.tar.gz config/
    log "配置备份成功"
}

backup_files() {
    log "开始文件备份..."
    tar -czf $BACKUP_ROOT/uploads_$DATE.tar.gz public/uploads/
    log "文件备份成功"
}

main() {
    log "========== 开始备份 =========="
    
    backup_database
    backup_config
    backup_files
    
    log "========== 备份完成 =========="
}

main
```

### 恢复流程

#### 完整恢复

```bash
#!/bin/bash

BACKUP_ROOT="/backup"
BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "请指定备份日期，例如: 20231230_020000"
    exit 1
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

restore_database() {
    log "开始恢复数据库..."
    gunzip -c $BACKUP_ROOT/postgresql/lilfox_$BACKUP_DATE.sql.gz | \
        psql -U lilfox -d lilfox -h localhost
    log "数据库恢复完成"
}

restore_config() {
    log "开始恢复配置..."
    cp $BACKUP_ROOT/env_$BACKUP_DATE .env
    tar -xzf $BACKUP_ROOT/config_$BACKUP_DATE.tar.gz
    log "配置恢复完成"
}

restore_files() {
    log "开始恢复文件..."
    tar -xzf $BACKUP_ROOT/uploads_$BACKUP_DATE.tar.gz -C /
    log "文件恢复完成"
}

main() {
    log "========== 开始恢复 =========="
    
    restore_database
    restore_config
    restore_files
    
    log "========== 恢复完成，请重启服务 =========="
}

main
```

## 性能优化

### 数据库优化

#### 索引优化

```sql
-- 查看索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 查看缺失的索引
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;
```

#### 查询优化

```sql
-- 查看慢查询
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 分析查询计划
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

#### 连接池配置

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### 缓存优化

#### Redis 缓存配置

```python
# config/cache.py
import redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
)
```

#### 缓存策略

```python
from functools import wraps
import json
import hashlib

def cache_result(expire=3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expire, json.dumps(result))
            
            return result
        return wrapper
    return decorator
```

### 应用优化

#### 异步处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

async def async_task(func, *args, **kwargs):
    """异步执行任务"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args, **kwargs)
```

#### 批量操作

```python
from typing import List, TypeVar, Generic

T = TypeVar('T')

class BatchProcessor(Generic[T]):
    """批量处理器"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    def process(self, items: List[T], processor):
        """批量处理"""
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            processor(batch)
```

### 网络优化

#### 连接复用

```python
import httpx

# 创建连接池
client = httpx.Client(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    timeout=httpx.Timeout(30.0)
)
```

#### 压缩传输

```python
import gzip
from fastapi import Response

@app.get("/api/data")
async def get_data():
    data = get_large_data()
    compressed = gzip.compress(data.encode())
    return Response(
        content=compressed,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )
```

## 安全加固

### 认证安全

#### JWT 配置

```python
# config/auth.py
from datetime import timedelta

JWT_CONFIG = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
    "secret_key": os.getenv("SECRET_KEY"),
}
```

#### 密码策略

```python
import re

def validate_password(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True
```

### 网络安全

#### CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### 限流配置

```python
# gateway/rate_limiter.py
RATE_LIMIT_CONFIG = {
    "default": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000
    },
    "authenticated": {
        "requests_per_minute": 120,
        "requests_per_hour": 2000
    }
}
```

### 数据安全

#### 敏感数据加密

```python
from cryptography.fernet import Fernet

cipher = Fernet(os.getenv("ENCRYPTION_KEY"))

def encrypt_data(data: str) -> str:
    """加密数据"""
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted: str) -> str:
    """解密数据"""
    return cipher.decrypt(encrypted.encode()).decode()
```

#### SQL 注入防护

```python
from sqlalchemy import text

# 使用参数化查询
def get_user_by_email(email: str):
    return db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()
```

## 版本更新

### 零停机更新

#### 蓝绿部署

```bash
#!/bin/bash

BLUE_PORT=8000
GREEN_PORT=8001
CURRENT_PORT=$BLUE_PORT

switch_traffic() {
    local new_port=$1
    echo "切换流量到端口 $new_port"
    
    # 更新 Nginx 配置
    sed -i "s/port $CURRENT_PORT/port $new_port/" /etc/nginx/sites-available/lilfox
    sudo nginx -s reload
    
    CURRENT_PORT=$new_port
}

deploy() {
    local version=$1
    echo "部署版本 $version"
    
    # 拉取代码
    git pull origin main
    
    # 安装依赖
    source venv/bin/activate
    pip install -r requirements.txt
    
    # 运行迁移
    python -m alembic upgrade head
    
    # 重启服务
    sudo systemctl restart lilfox-backend
    
    echo "部署完成"
}

main() {
    deploy $1
    switch_traffic $GREEN_PORT
}

main $1
```

#### 滚动更新

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: lilfox-backend:latest
```

### 回滚策略

```bash
#!/bin/bash

ROLLBACK_DIR="/backup/rollback"

rollback() {
    local version=$1
    echo "回滚到版本 $version"
    
    # 恢复数据库
    psql -U lilfox -d lilfox < $ROLLBACK_DIR/db_$version.sql
    
    # 恢复代码
    git checkout $version
    
    # 重启服务
    sudo systemctl restart lilfox-backend
    
    echo "回滚完成"
}

rollback $1
```

## 应急响应

### 故障检测

```python
# scripts/health_check.py
import requests
import smtplib
from email.mime.text import MIMEText

def check_service(url: str) -> bool:
    """检查服务健康"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_alert(message: str):
    """发送告警"""
    msg = MIMEText(message)
    msg['Subject'] = 'LilFox 服务告警'
    msg['From'] = 'alert@lilfox.com'
    msg['To'] = 'admin@lilfox.com'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('alert@lilfox.com', 'password')
        server.send_message(msg)

def main():
    services = {
        "Gateway": "http://localhost:8080",
        "Backend": "http://localhost:8000",
        "Model": "http://localhost:8001"
    }
    
    failed_services = []
    
    for name, url in services.items():
        if not check_service(url):
            failed_services.append(name)
    
    if failed_services:
        message = f"以下服务异常: {', '.join(failed_services)}"
        print(message)
        send_alert(message)

if __name__ == "__main__":
    main()
```

### 故障恢复

#### 自动恢复脚本

```bash
#!/bin/bash

LOG_FILE="/var/log/lilfox/recovery.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

restart_service() {
    local service=$1
    log "尝试重启服务 $service"
    
    sudo systemctl restart $service
    
    sleep 10
    
    if sudo systemctl is-active --quiet $service; then
        log "服务 $service 重启成功"
        return 0
    else
        log "服务 $service 重启失败"
        return 1
    fi
}

main() {
    log "========== 开始故障恢复 =========="
    
    # 检查并重启异常服务
    for service in lilfox-gateway lilfox-backend lilfox-model; do
        if ! sudo systemctl is-active --quiet $service; then
            log "检测到服务 $service 异常"
            restart_service $service
        fi
    done
    
    log "========== 故障恢复完成 =========="
}

main
```

### 紧急预案

#### 数据库故障

1. **检查数据库状态**
   ```bash
   sudo systemctl status postgresql
   ```

2. **查看数据库日志**
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

3. **尝试重启数据库**
   ```bash
   sudo systemctl restart postgresql
   ```

4. **如无法恢复，使用备用数据库**
   ```bash
   # 切换到备用数据库
   export DATABASE_URL="postgresql://lilfox:password@backup-db:5432/lilfox"
   sudo systemctl restart lilfox-backend
   ```

#### 服务崩溃

1. **查看服务日志**
   ```bash
   sudo journalctl -u lilfox-backend -n 100
   ```

2. **检查资源使用**
   ```bash
   htop
   df -h
   ```

3. **重启服务**
   ```bash
   sudo systemctl restart lilfox-backend
   ```

4. **如持续崩溃，回滚到上一版本**
   ```bash
   git log --oneline -10
   git checkout <previous-commit>
   sudo systemctl restart lilfox-backend
   ```

#### 网络攻击

1. **识别攻击类型**
   ```bash
   # 查看 Nginx 访问日志
   sudo tail -f /var/log/nginx/access.log
   
   # 统计访问频率
   sudo awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -20
   ```

2. **临时封禁 IP**
   ```bash
   sudo iptables -A INPUT -s <attack-ip> -j DROP
   ```

3. **启用更严格的限流**
   ```python
   # 临时降低限流阈值
   RATE_LIMIT_CONFIG["default"]["requests_per_minute"] = 10
   ```

4. **联系安全团队**
   - 收集攻击证据
   - 记录攻击时间、IP、类型
   - 通知相关人员
