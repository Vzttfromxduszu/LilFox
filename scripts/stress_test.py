import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import argparse


@dataclass
class TestResult:
    """测试结果"""
    url: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class TestStats:
    """测试统计"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float


class StressTester:
    """压力测试工具"""
    
    def __init__(
        self,
        base_url: str,
        max_concurrent: int = 10,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = headers or {}
        self.results: List[TestResult] = []
    
    async def make_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """发送单个请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self.headers
            ) as response:
                response_time = time.time() - start_time
                return TestResult(
                    url=url,
                    method=method,
                    status_code=response.status,
                    response_time=response_time,
                    success=200 <= response.status_code < 300
                )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                url=url,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e)
            )
    
    async def run_concurrent_requests(
        self,
        method: str,
        endpoint: str,
        num_requests: int,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> List[TestResult]:
        """运行并发请求"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout
        ) as session:
            tasks = [
                self.make_request(session, method, endpoint, data, params)
                for _ in range(num_requests)
            ]
            return await asyncio.gather(*tasks)
    
    def calculate_stats(self, results: List[TestResult], duration: float) -> TestStats:
        """计算统计信息"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        response_times = [r.response_time for r in successful]
        
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            sorted_times = sorted(response_times)
            n = len(sorted_times)
            p50 = sorted_times[int(n * 0.5)]
            p95 = sorted_times[int(n * 0.95)]
            p99 = sorted_times[int(n * 0.99)]
        else:
            avg_time = min_time = max_time = p50 = p95 = p99 = 0.0
        
        return TestStats(
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            avg_response_time=avg_time,
            min_response_time=min_time,
            max_response_time=max_time,
            p50_response_time=p50,
            p95_response_time=p95,
            p99_response_time=p99,
            requests_per_second=len(results) / duration if duration > 0 else 0,
            error_rate=len(failed) / len(results) if results else 0
        )
    
    def print_stats(self, stats: TestStats, test_name: str):
        """打印统计信息"""
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print(f"{'='*60}")
        print(f"总请求数:      {stats.total_requests}")
        print(f"成功请求数:    {stats.successful_requests}")
        print(f"失败请求数:    {stats.failed_requests}")
        print(f"错误率:        {stats.error_rate:.2%}")
        print(f"QPS:           {stats.requests_per_second:.2f}")
        print(f"\n响应时间 (秒):")
        print(f"  平均:        {stats.avg_response_time:.4f}")
        print(f"  最小:        {stats.min_response_time:.4f}")
        print(f"  最大:        {stats.max_response_time:.4f}")
        print(f"  P50:         {stats.p50_response_time:.4f}")
        print(f"  P95:         {stats.p95_response_time:.4f}")
        print(f"  P99:         {stats.p99_response_time:.4f}")
        print(f"{'='*60}\n")


class LilFoxStressTest:
    """LilFox 压力测试套件"""
    
    def __init__(self, gateway_url: str = "http://localhost:8080"):
        self.gateway_url = gateway_url
        self.auth_token: Optional[str] = None
    
    async def test_health_check(self, num_requests: int = 100):
        """测试健康检查接口"""
        print("开始健康检查测试...")
        
        tester = StressTester(self.gateway_url, max_concurrent=20)
        start_time = time.time()
        results = await tester.run_concurrent_requests("GET", "/health", num_requests)
        duration = time.time() - start_time
        
        stats = tester.calculate_stats(results, duration)
        tester.print_stats(stats, "健康检查")
        
        return stats
    
    async def test_user_registration(self, num_requests: int = 100):
        """测试用户注册"""
        print("开始用户注册测试...")
        
        tester = StressTester(self.gateway_url, max_concurrent=10)
        
        results = []
        start_time = time.time()
        
        for i in range(num_requests):
            data = {
                "username": f"testuser_{int(time.time() * 1000)}_{i}",
                "email": f"test_{i}_{int(time.time() * 1000)}@example.com",
                "password": "Test@123456"
            }
            batch_results = await tester.run_concurrent_requests("POST", "/api/auth/register", 1, data)
            results.extend(batch_results)
        
        duration = time.time() - start_time
        stats = tester.calculate_stats(results, duration)
        tester.print_stats(stats, "用户注册")
        
        return stats
    
    async def test_user_login(self, num_requests: int = 100):
        """测试用户登录"""
        print("开始用户登录测试...")
        
        tester = StressTester(self.gateway_url, max_concurrent=20)
        
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        start_time = time.time()
        results = await tester.run_concurrent_requests("POST", "/api/auth/login", num_requests, data)
        duration = time.time() - start_time
        
        stats = tester.calculate_stats(results, duration)
        tester.print_stats(stats, "用户登录")
        
        return stats
    
    async def test_get_user_info(self, num_requests: int = 100, token: Optional[str] = None):
        """测试获取用户信息"""
        print("开始获取用户信息测试...")
        
        if not token:
            print("警告: 未提供认证令牌，使用测试令牌")
            token = "test_token"
        
        headers = {"Authorization": f"Bearer {token}"}
        tester = StressTester(self.gateway_url, max_concurrent=20, headers=headers)
        
        start_time = time.time()
        results = await tester.run_concurrent_requests("GET", "/api/users/me", num_requests)
        duration = time.time() - start_time
        
        stats = tester.calculate_stats(results, duration)
        tester.print_stats(stats, "获取用户信息")
        
        return stats
    
    async def test_model_chat(self, num_requests: int = 50, token: Optional[str] = None):
        """测试模型对话接口"""
        print("开始模型对话测试...")
        
        if not token:
            print("警告: 未提供认证令牌，使用测试令牌")
            token = "test_token"
        
        headers = {"Authorization": f"Bearer {token}"}
        tester = StressTester(self.gateway_url, max_concurrent=5, headers=headers)
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        start_time = time.time()
        results = await tester.run_concurrent_requests("POST", "/api/llm/chat", num_requests, data)
        duration = time.time() - start_time
        
        stats = tester.calculate_stats(results, duration)
        tester.print_stats(stats, "模型对话")
        
        return stats
    
    async def test_concurrent_mixed_requests(self, num_requests: int = 200, token: Optional[str] = None):
        """测试混合并发请求"""
        print("开始混合并发请求测试...")
        
        if not token:
            token = "test_token"
        
        headers = {"Authorization": f"Bearer {token}"}
        tester = StressTester(self.gateway_url, max_concurrent=50, headers=headers)
        
        results = []
        start_time = time.time()
        
        for i in range(num_requests):
            if i % 4 == 0:
                batch = await tester.run_concurrent_requests("GET", "/health", 1)
            elif i % 4 == 1:
                batch = await tester.run_concurrent_requests("GET", "/api/users/me", 1)
            elif i % 4 == 2:
                batch = await tester.run_concurrent_requests(
                    "POST",
                    "/api/llm/chat",
                    1,
                    {
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 50
                    }
                )
            else:
                batch = await tester.run_concurrent_requests(
                    "POST",
                    "/api/auth/login",
                    1,
                    {"username": "admin", "password": "admin123"}
                )
            results.extend(batch)
        
        duration = time.time() - start_time
        stats = tester.calculate_stats(results, duration)
        tester.print_stats(stats, "混合并发请求")
        
        return stats
    
    async def test_sustained_load(self, duration: int = 60, rps: int = 10, token: Optional[str] = None):
        """测试持续负载"""
        print(f"开始持续负载测试 (持续 {duration} 秒, 目标 RPS: {rps})...")
        
        if not token:
            token = "test_token"
        
        headers = {"Authorization": f"Bearer {token}"}
        tester = StressTester(self.gateway_url, max_concurrent=50, headers=headers)
        
        results = []
        start_time = time.time()
        end_time = start_time + duration
        
        connector = aiohttp.TCPConnector(limit=50)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            while time.time() < end_time:
                batch_start = time.time()
                
                tasks = []
                for _ in range(rps):
                    if time.time() >= end_time:
                        break
                    tasks.append(tester.make_request(session, "GET", "/health"))
                
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                
                batch_duration = time.time() - batch_start
                if batch_duration < 1.0:
                    await asyncio.sleep(1.0 - batch_duration)
        
        actual_duration = time.time() - start_time
        stats = tester.calculate_stats(results, actual_duration)
        tester.print_stats(stats, f"持续负载 ({duration}秒)")
        
        return stats
    
    async def test_rate_limiting(self, num_requests: int = 150):
        """测试限流功能"""
        print("开始限流测试...")
        
        tester = StressTester(self.gateway_url, max_concurrent=50)
        
        start_time = time.time()
        results = await tester.run_concurrent_requests("GET", "/health", num_requests)
        duration = time.time() - start_time
        
        rate_limited = sum(1 for r in results if r.status_code == 429)
        
        stats = tester.calculate_stats(results, duration)
        tester.print_stats(stats, "限流测试")
        
        print(f"被限流的请求数: {rate_limited}")
        print(f"限流比例: {rate_limited / num_requests:.2%}\n")
        
        return stats
    
    async def run_all_tests(self, token: Optional[str] = None):
        """运行所有测试"""
        print(f"\n{'#'*60}")
        print(f"# LilFox 压力测试套件")
        print(f"# 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"# 网关地址: {self.gateway_url}")
        print(f"{'#'*60}\n")
        
        all_stats = {}
        
        try:
            all_stats['health_check'] = await self.test_health_check(100)
        except Exception as e:
            print(f"健康检查测试失败: {e}\n")
        
        try:
            all_stats['user_login'] = await self.test_user_login(100)
        except Exception as e:
            print(f"用户登录测试失败: {e}\n")
        
        try:
            all_stats['get_user_info'] = await self.test_get_user_info(100, token)
        except Exception as e:
            print(f"获取用户信息测试失败: {e}\n")
        
        try:
            all_stats['model_chat'] = await self.test_model_chat(20, token)
        except Exception as e:
            print(f"模型对话测试失败: {e}\n")
        
        try:
            all_stats['concurrent_mixed'] = await self.test_concurrent_mixed_requests(200, token)
        except Exception as e:
            print(f"混合并发请求测试失败: {e}\n")
        
        try:
            all_stats['rate_limiting'] = await self.test_rate_limiting(150)
        except Exception as e:
            print(f"限流测试失败: {e}\n")
        
        try:
            all_stats['sustained_load'] = await self.test_sustained_load(30, 10, token)
        except Exception as e:
            print(f"持续负载测试失败: {e}\n")
        
        self.print_summary(all_stats)
        self.save_results(all_stats)
    
    def print_summary(self, all_stats: Dict[str, TestStats]):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("测试总结")
        print(f"{'='*60}")
        print(f"{'测试名称':<20} {'成功率':<10} {'QPS':<10} {'P95响应时间':<15}")
        print(f"{'-'*60}")
        
        for name, stats in all_stats.items():
            success_rate = (1 - stats.error_rate) * 100
            print(f"{name:<20} {success_rate:>6.2f}%   {stats.requests_per_second:>6.2f}   {stats.p95_response_time:>10.4f}s")
        
        print(f"{'='*60}\n")
    
    def save_results(self, all_stats: Dict[str, TestStats]):
        """保存测试结果"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "gateway_url": self.gateway_url,
            "tests": {}
        }
        
        for name, stats in all_stats.items():
            results["tests"][name] = {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "error_rate": stats.error_rate,
                "requests_per_second": stats.requests_per_second,
                "avg_response_time": stats.avg_response_time,
                "p50_response_time": stats.p50_response_time,
                "p95_response_time": stats.p95_response_time,
                "p99_response_time": stats.p99_response_time
            }
        
        filename = f"stress_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"测试结果已保存到: {filename}\n")


async def main():
    parser = argparse.ArgumentParser(description='LilFox 压力测试工具')
    parser.add_argument('--url', default='http://localhost:8080', help='网关地址')
    parser.add_argument('--token', help='认证令牌')
    parser.add_argument('--test', choices=[
        'all', 'health', 'register', 'login', 'user', 'chat', 'mixed', 'sustained', 'rate'
    ], default='all', help='测试类型')
    parser.add_argument('--requests', type=int, default=100, help='请求数量')
    parser.add_argument('--duration', type=int, default=60, help='持续负载测试时长(秒)')
    parser.add_argument('--rps', type=int, default=10, help='持续负载测试目标RPS')
    
    args = parser.parse_args()
    
    tester = LilFoxStressTest(args.url)
    
    if args.test == 'all':
        await tester.run_all_tests(args.token)
    elif args.test == 'health':
        await tester.test_health_check(args.requests)
    elif args.test == 'register':
        await tester.test_user_registration(args.requests)
    elif args.test == 'login':
        await tester.test_user_login(args.requests)
    elif args.test == 'user':
        await tester.test_get_user_info(args.requests, args.token)
    elif args.test == 'chat':
        await tester.test_model_chat(args.requests, args.token)
    elif args.test == 'mixed':
        await tester.test_concurrent_mixed_requests(args.requests, args.token)
    elif args.test == 'sustained':
        await tester.test_sustained_load(args.duration, args.rps, args.token)
    elif args.test == 'rate':
        await tester.test_rate_limiting(args.requests)


if __name__ == "__main__":
    asyncio.run(main())
