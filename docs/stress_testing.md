# LilFox 压力测试指南

## 目录

- [概述](#概述)
- [环境准备](#环境准备)
- [测试工具](#测试工具)
- [测试场景](#测试场景)
- [测试执行](#测试执行)
- [结果分析](#结果分析)
- [性能优化建议](#性能优化建议)

## 概述

压力测试是验证系统在高负载下的稳定性和性能的重要手段。LilFox 提供了一套完整的压力测试工具和测试场景，帮助开发者识别性能瓶颈和系统弱点。

### 测试目标

- 验证系统在高并发下的稳定性
- 识别性能瓶颈
- 测试限流和熔断机制
- 评估系统容量和扩展性
- 验证故障恢复能力

### 测试原则

- **渐进式**: 从低负载逐步增加到高负载
- **真实性**: 模拟真实用户行为和数据
- **可重复**: 确保测试结果可复现
- **全面性**: 覆盖所有关键接口和场景

## 环境准备

### 系统要求

- **Python**: 3.9+
- **内存**: 8GB+ (推荐 16GB)
- **CPU**: 4核心+ (推荐 8核心)
- **网络**: 千兆网络

### 依赖安装

```bash
# 安装测试依赖
pip install aiohttp asyncio

# 或安装完整依赖
pip install -r requirements.txt
```

### 服务启动

```bash
# 启动所有服务
python scripts/start_all.py

# 或分别启动
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000
cd model_service && python -m uvicorn main:app --host 0.0.0.0 --port 8001
cd gateway && python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

### 配置检查

```bash
# 验证配置
python scripts/config_tool.py validate

# 检查服务健康
curl http://localhost:8080/health
```

## 测试工具

### 压力测试脚本

`scripts/stress_test.py` 是主要的压力测试工具，提供以下功能:

- 并发请求测试
- 持续负载测试
- 混合场景测试
- 限流测试
- 结果统计和分析

### 工具特性

- **异步执行**: 使用 asyncio 和 aiohttp 实现高并发
- **灵活配置**: 支持自定义并发数、请求数、超时等
- **详细统计**: 提供响应时间、成功率、QPS 等指标
- **结果保存**: 自动保存测试结果为 JSON 文件

### 命令行参数

```bash
python scripts/stress_test.py --help

# 可用参数:
--url          网关地址 (默认: http://localhost:8080)
--token        认证令牌
--test         测试类型 (all, health, register, login, user, chat, mixed, sustained, rate)
--requests     请求数量 (默认: 100)
--duration     持续负载测试时长(秒) (默认: 60)
--rps          持续负载测试目标RPS (默认: 10)
```

## 测试场景

### 1. 健康检查测试

**目的**: 验证系统基础功能和响应能力

**测试参数**:
- 并发数: 20
- 请求数: 100

**执行命令**:
```bash
python scripts/stress_test.py --test health --requests 100
```

**预期结果**:
- 成功率: > 99%
- 平均响应时间: < 50ms
- P95 响应时间: < 100ms

### 2. 用户注册测试

**目的**: 测试用户注册接口的性能和并发处理能力

**测试参数**:
- 并发数: 10
- 请求数: 100

**执行命令**:
```bash
python scripts/stress_test.py --test register --requests 100
```

**预期结果**:
- 成功率: > 95%
- 平均响应时间: < 200ms
- P95 响应时间: < 500ms

**注意事项**:
- 每个请求使用唯一的用户名和邮箱
- 测试后清理测试数据

### 3. 用户登录测试

**目的**: 测试认证系统的性能

**测试参数**:
- 并发数: 20
- 请求数: 100

**执行命令**:
```bash
python scripts/stress_test.py --test login --requests 100
```

**预期结果**:
- 成功率: > 98%
- 平均响应时间: < 150ms
- P95 响应时间: < 300ms

### 4. 获取用户信息测试

**目的**: 测试需要认证的接口性能

**测试参数**:
- 并发数: 20
- 请求数: 100

**执行命令**:
```bash
python scripts/stress_test.py --test user --requests 100 --token YOUR_TOKEN
```

**预期结果**:
- 成功率: > 98%
- 平均响应时间: < 100ms
- P95 响应时间: < 200ms

### 5. 模型对话测试

**目的**: 测试大模型接口的性能和并发处理能力

**测试参数**:
- 并发数: 5
- 请求数: 20

**执行命令**:
```bash
python scripts/stress_test.py --test chat --requests 20 --token YOUR_TOKEN
```

**预期结果**:
- 成功率: > 90%
- 平均响应时间: < 3000ms
- P95 响应时间: < 5000ms

**注意事项**:
- 模型接口响应时间较长
- 控制并发数避免超时

### 6. 混合并发请求测试

**目的**: 模拟真实场景下的混合请求负载

**测试参数**:
- 并发数: 50
- 请求数: 200

**执行命令**:
```bash
python scripts/stress_test.py --test mixed --requests 200 --token YOUR_TOKEN
```

**预期结果**:
- 成功率: > 95%
- 平均响应时间: < 500ms
- P95 响应时间: < 1000ms

**请求分布**:
- 25% 健康检查
- 25% 获取用户信息
- 25% 模型对话
- 25% 用户登录

### 7. 持续负载测试

**目的**: 测试系统在持续负载下的稳定性和性能

**测试参数**:
- 持续时间: 60 秒
- 目标 RPS: 10

**执行命令**:
```bash
python scripts/stress_test.py --test sustained --duration 60 --rps 10 --token YOUR_TOKEN
```

**预期结果**:
- 成功率: > 99%
- 平均响应时间保持稳定
- 无内存泄漏
- 无连接泄漏

**监控指标**:
- CPU 使用率
- 内存使用率
- 数据库连接数
- 响应时间趋势

### 8. 限流测试

**目的**: 验证限流机制的有效性

**测试参数**:
- 并发数: 50
- 请求数: 150

**执行命令**:
```bash
python scripts/stress_test.py --test rate --requests 150
```

**预期结果**:
- 部分请求返回 429 状态码
- 限流后系统保持稳定
- 未限流请求正常响应

## 测试执行

### 完整测试套件

运行所有测试:

```bash
python scripts/stress_test.py --test all --token YOUR_TOKEN
```

### 单独测试

运行特定测试:

```bash
# 健康检查
python scripts/stress_test.py --test health

# 用户登录
python scripts/stress_test.py --test login --requests 200

# 模型对话
python scripts/stress_test.py --test chat --requests 50 --token YOUR_TOKEN
```

### 自定义测试

使用自定义参数:

```bash
# 高并发测试
python scripts/stress_test.py --test health --requests 1000

# 长时间持续测试
python scripts/stress_test.py --test sustained --duration 300 --rps 20

# 指定网关地址
python scripts/stress_test.py --url http://192.168.1.100:8080 --test all
```

### 监控测试过程

在另一个终端监控系统资源:

```bash
# CPU 和内存
htop

# 网络连接
netstat -an | grep ESTABLISHED | wc -l

# 日志
tail -f logs/gateway.log
tail -f logs/backend.log
```

## 结果分析

### 测试报告

测试完成后，会生成 JSON 格式的结果文件:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "gateway_url": "http://localhost:8080",
  "tests": {
    "health_check": {
      "total_requests": 100,
      "successful_requests": 100,
      "failed_requests": 0,
      "error_rate": 0.0,
      "requests_per_second": 52.63,
      "avg_response_time": 0.038,
      "p50_response_time": 0.035,
      "p95_response_time": 0.058,
      "p99_response_time": 0.072
    }
  }
}
```

### 关键指标

#### 1. 成功率

- **优秀**: > 99%
- **良好**: 95% - 99%
- **需改进**: < 95%

#### 2. QPS (每秒请求数)

- **优秀**: > 1000
- **良好**: 500 - 1000
- **需改进**: < 500

#### 3. 响应时间

| 接口类型 | 优秀 | 良好 | 需改进 |
|---------|------|------|--------|
| 健康检查 | < 50ms | 50-100ms | > 100ms |
| 认证接口 | < 100ms | 100-200ms | > 200ms |
| 业务接口 | < 200ms | 200-500ms | > 500ms |
| 模型接口 | < 2000ms | 2000-5000ms | > 5000ms |

#### 4. P95/P99 响应时间

- **P95**: 95% 的请求响应时间
- **P99**: 99% 的请求响应时间
- 关注长尾延迟，确保用户体验

### 性能瓶颈识别

#### 数据库瓶颈

**症状**:
- 数据库查询响应时间长
- 数据库连接池耗尽
- 数据库 CPU 使用率高

**解决方案**:
- 添加索引
- 优化查询
- 使用缓存
- 增加数据库连接池大小

#### 网络瓶颈

**症状**:
- 网络延迟高
- 带宽利用率高
- 连接超时

**解决方案**:
- 优化网络配置
- 使用 CDN
- 压缩响应数据
- 减少请求数量

#### 应用瓶颈

**症状**:
- 应用 CPU 使用率高
- 内存使用率高
- GC 频繁

**解决方案**:
- 优化算法
- 使用异步处理
- 增加缓存
- 水平扩展

#### 外部服务瓶颈

**症状**:
- 第三方 API 响应慢
- 外部服务超时

**解决方案**:
- 使用熔断机制
- 增加超时时间
- 使用备用服务
- 缓存外部数据

### 性能对比

#### 版本对比

对比不同版本的性能:

```python
import json

def compare_versions(v1_file: str, v2_file: str):
    """对比两个版本的测试结果"""
    with open(v1_file) as f:
        v1 = json.load(f)
    with open(v2_file) as f:
        v2 = json.load(f)
    
    print(f"{'测试':<20} {'V1 QPS':<10} {'V2 QPS':<10} {'提升':<10}")
    print("-" * 50)
    
    for test_name in v1['tests']:
        v1_qps = v1['tests'][test_name]['requests_per_second']
        v2_qps = v2['tests'][test_name]['requests_per_second']
        improvement = (v2_qps - v1_qps) / v1_qps * 100
        
        print(f"{test_name:<20} {v1_qps:>8.2f}   {v2_qps:>8.2f}   {improvement:>6.2f}%")
```

#### 配置对比

对比不同配置的性能:

```bash
# 测试不同并发数
for concurrent in 10 20 50 100; do
    echo "测试并发数: $concurrent"
    python scripts/stress_test.py --test health --requests 500
done
```

## 性能优化建议

### 数据库优化

1. **索引优化**
   ```sql
   -- 为常用查询字段添加索引
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_users_username ON users(username);
   ```

2. **连接池配置**
   ```python
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=40,
       pool_timeout=30,
       pool_recycle=3600
   )
   ```

3. **查询优化**
   - 使用 EXPLAIN ANALYZE 分析查询
   - 避免 SELECT *
   - 使用批量操作
   - 使用 JOIN 代替子查询

### 缓存优化

1. **Redis 缓存**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def get_user(user_id: int):
       return db.query(User).filter(User.id == user_id).first()
   ```

2. **缓存策略**
   - 热点数据缓存
   - 查询结果缓存
   - 会话缓存
   - 静态资源缓存

### 应用优化

1. **异步处理**
   ```python
   import asyncio
   
   async def process_data(data):
       tasks = [async_task(item) for item in data]
       await asyncio.gather(*tasks)
   ```

2. **批量操作**
   ```python
   def batch_insert(items: List[Item]):
       db.bulk_insert_mappings(Item, [item.dict() for item in items])
       db.commit()
   ```

3. **代码优化**
   - 减少不必要的计算
   - 使用高效的数据结构
   - 避免重复查询
   - 使用生成器代替列表

### 网络优化

1. **连接复用**
   ```python
   import httpx
   
   client = httpx.Client(
       limits=httpx.Limits(
           max_keepalive_connections=20,
           max_connections=100
       )
   )
   ```

2. **压缩传输**
   ```python
   from fastapi import Response
   
   @app.get("/api/data")
   async def get_data():
       data = get_large_data()
       compressed = gzip.compress(data.encode())
       return Response(
           content=compressed,
           headers={"Content-Encoding": "gzip"}
       )
   ```

3. **CDN 加速**
   - 静态资源使用 CDN
   - 图片优化和懒加载
   - 使用 HTTP/2

### 架构优化

1. **水平扩展**
   - 增加服务实例
   - 使用负载均衡
   - 微服务拆分

2. **读写分离**
   - 主从数据库
   - 读写分离中间件
   - 缓存层

3. **消息队列**
   - 异步任务处理
   - 削峰填谷
   - 解耦服务

### 监控和告警

1. **实时监控**
   - Prometheus + Grafana
   - 自定义监控脚本
   - 日志分析

2. **告警规则**
   - 错误率告警
   - 响应时间告警
   - 资源使用告警

3. **日志分析**
   - 错误日志统计
   - 性能日志分析
   - 用户行为分析

## 最佳实践

### 测试前

1. **准备测试数据**
   - 创建足够的测试数据
   - 使用真实场景数据
   - 清理旧测试数据

2. **配置环境**
   - 使用生产类似配置
   - 禁用调试模式
   - 配置日志级别

3. **基准测试**
   - 建立性能基准
   - 记录初始状态
   - 准备对比数据

### 测试中

1. **监控系统**
   - CPU、内存、磁盘
   - 网络流量
   - 应用日志

2. **逐步增加负载**
   - 从低负载开始
   - 逐步增加并发
   - 观察系统反应

3. **记录异常**
   - 记录错误信息
   - 截图保存
   - 保存日志

### 测试后

1. **分析结果**
   - 统计性能指标
   - 识别瓶颈
   - 对比基准

2. **清理环境**
   - 删除测试数据
   - 重置配置
   - 释放资源

3. **编写报告**
   - 测试环境
   - 测试场景
   - 测试结果
   - 优化建议
