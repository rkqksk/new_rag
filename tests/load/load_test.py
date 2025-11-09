"""
Load Testing for RAG Enterprise
Performance and stress testing for Q&A endpoints
"""

import asyncio
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import httpx


@dataclass
class LoadTestConfig:
    """Load test configuration"""

    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    requests_per_user: int = 10
    timeout: int = 30


@dataclass
class LoadTestResult:
    """Load test results"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    total_duration: float
    errors: List[str]


class LoadTester:
    """Load tester for RAG Enterprise API"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.successful = 0
        self.failed = 0

    async def _make_request(
        self, client: httpx.AsyncClient, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a single API request"""
        start_time = time.time()
        try:
            response = await client.post(
                f"{self.config.base_url}{endpoint}", json=payload, timeout=self.config.timeout
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                self.successful += 1
                self.response_times.append(duration)
                return {"success": True, "duration": duration, "data": response.json()}
            else:
                self.failed += 1
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.errors.append(error_msg)
                return {"success": False, "error": error_msg}

        except Exception as e:
            duration = time.time() - start_time
            self.failed += 1
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.errors.append(error_msg)
            return {"success": False, "error": error_msg, "duration": duration}

    async def _user_session(self, user_id: int, client: httpx.AsyncClient, questions: List[str]):
        """Simulate a single user making multiple requests"""
        for i, question in enumerate(questions):
            payload = {
                "question": question,
                "collection": "products_all",
                "top_k": 3,
                "customer_id": f"user_{user_id}",
            }

            await self._make_request(client, "/api/v2/qa/ask", payload)

            # Small delay between requests
            await asyncio.sleep(0.1)

    async def run_sync_test(self, questions: List[str]) -> LoadTestResult:
        """Run load test on synchronous endpoint"""
        print(f"\n🔄 Starting SYNC load test...")
        print(f"   Users: {self.config.concurrent_users}")
        print(f"   Requests per user: {self.config.requests_per_user}")
        print(f"   Total requests: {self.config.concurrent_users * self.config.requests_per_user}")

        start_time = time.time()

        async with httpx.AsyncClient() as client:
            # Create tasks for concurrent users
            tasks = []
            for user_id in range(self.config.concurrent_users):
                # Each user makes multiple requests
                user_questions = questions[: self.config.requests_per_user]
                task = self._user_session(user_id, client, user_questions)
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

        total_duration = time.time() - start_time

        return self._calculate_results(total_duration)

    async def run_async_test(self, questions: List[str]) -> LoadTestResult:
        """Run load test on async endpoint"""
        print(f"\n⚡ Starting ASYNC load test...")
        print(f"   Users: {self.config.concurrent_users}")
        print(f"   Requests per user: {self.config.requests_per_user}")
        print(f"   Total requests: {self.config.concurrent_users * self.config.requests_per_user}")

        start_time = time.time()

        async with httpx.AsyncClient() as client:
            # Create tasks for concurrent users
            tasks = []
            for user_id in range(self.config.concurrent_users):
                # Each user makes multiple requests
                user_questions = questions[: self.config.requests_per_user]
                task = self._user_session(user_id, client, user_questions)
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

        total_duration = time.time() - start_time

        return self._calculate_results(total_duration)

    async def run_batch_test(self, questions: List[str]) -> LoadTestResult:
        """Run load test on batch endpoint"""
        print(f"\n📦 Starting BATCH load test...")
        print(f"   Batch size: {len(questions)}")

        start_time = time.time()

        async with httpx.AsyncClient() as client:
            payload = {"questions": questions, "collection": "products_all", "top_k": 3}

            await self._make_request(client, "/api/v2/qa/batch", payload)

        total_duration = time.time() - start_time

        return self._calculate_results(total_duration)

    def _calculate_results(self, total_duration: float) -> LoadTestResult:
        """Calculate load test results"""
        total_requests = self.successful + self.failed

        if self.response_times:
            sorted_times = sorted(self.response_times)
            avg_time = statistics.mean(self.response_times)
            p50_time = statistics.median(self.response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            p95_time = sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]
            p99_time = sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1]
            min_time = min(self.response_times)
            max_time = max(self.response_times)
        else:
            avg_time = p50_time = p95_time = p99_time = min_time = max_time = 0

        rps = total_requests / total_duration if total_duration > 0 else 0

        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=self.successful,
            failed_requests=self.failed,
            avg_response_time=avg_time,
            p50_response_time=p50_time,
            p95_response_time=p95_time,
            p99_response_time=p99_time,
            min_response_time=min_time,
            max_response_time=max_time,
            requests_per_second=rps,
            total_duration=total_duration,
            errors=self.errors[:10],  # First 10 errors
        )

    def reset(self):
        """Reset test metrics"""
        self.response_times = []
        self.errors = []
        self.successful = 0
        self.failed = 0


def print_results(test_name: str, result: LoadTestResult):
    """Print load test results"""
    print(f"\n{'='*60}")
    print(f"📊 {test_name} Results")
    print(f"{'='*60}")
    print(f"Total Requests:      {result.total_requests}")
    print(
        f"Successful:          {result.successful_requests} ({result.successful_requests/result.total_requests*100:.1f}%)"
    )
    print(
        f"Failed:              {result.failed_requests} ({result.failed_requests/result.total_requests*100:.1f}%)"
    )
    print(f"Total Duration:      {result.total_duration:.2f}s")
    print(f"Requests/Second:     {result.requests_per_second:.2f}")
    print(f"\nResponse Times:")
    print(f"  Average:           {result.avg_response_time*1000:.0f}ms")
    print(f"  Median (p50):      {result.p50_response_time*1000:.0f}ms")
    print(f"  95th percentile:   {result.p95_response_time*1000:.0f}ms")
    print(f"  99th percentile:   {result.p99_response_time*1000:.0f}ms")
    print(f"  Min:               {result.min_response_time*1000:.0f}ms")
    print(f"  Max:               {result.max_response_time*1000:.0f}ms")

    if result.errors:
        print(f"\n⚠️  First {len(result.errors)} Errors:")
        for error in result.errors[:5]:
            print(f"  - {error}")


async def main():
    """Run comprehensive load tests"""
    print("\n" + "=" * 60)
    print("🚀 RAG Enterprise Load Testing")
    print("=" * 60)

    # Test questions
    questions = [
        "50ml 용기 추천해주세요",
        "100ml PET 용기 있나요?",
        "펌프 용기 재질은 무엇인가요?",
        "화장품 용기 중 가장 인기있는 것은?",
        "친환경 소재 용기가 있나요?",
        "대용량 샴푸 용기 추천해주세요",
        "투명 PET 용기 찾고 있어요",
        "크림 용기 사이즈별로 알려주세요",
        "에어리스 용기 장점이 뭔가요?",
        "유리 용기도 판매하시나요?",
    ]

    # Configuration
    config = LoadTestConfig(concurrent_users=10, requests_per_user=10, timeout=30)

    # Test 1: Sync endpoint
    tester = LoadTester(config)
    sync_result = await tester.run_sync_test(questions)
    print_results("Synchronous Q&A", sync_result)

    # Test 2: Async endpoint
    tester.reset()
    async_result = await tester.run_async_test(questions)
    print_results("Asynchronous Q&A", async_result)

    # Test 3: Batch endpoint
    tester.reset()
    batch_result = await tester.run_batch_test(questions)
    print_results("Batch Q&A", batch_result)

    # Comparison
    print(f"\n{'='*60}")
    print("📈 Performance Comparison")
    print(f"{'='*60}")
    print(f"Async vs Sync Improvement:")
    print(
        f"  Response Time:     {(sync_result.avg_response_time - async_result.avg_response_time) / sync_result.avg_response_time * 100:.1f}% faster"
    )
    print(
        f"  Throughput:        {(async_result.requests_per_second - sync_result.requests_per_second) / sync_result.requests_per_second * 100:.1f}% increase"
    )

    # Save results
    results_file = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "concurrent_users": config.concurrent_users,
                    "requests_per_user": config.requests_per_user,
                    "timeout": config.timeout,
                },
                "sync_test": {
                    "total_requests": sync_result.total_requests,
                    "successful": sync_result.successful_requests,
                    "avg_response_time_ms": sync_result.avg_response_time * 1000,
                    "p95_response_time_ms": sync_result.p95_response_time * 1000,
                    "requests_per_second": sync_result.requests_per_second,
                },
                "async_test": {
                    "total_requests": async_result.total_requests,
                    "successful": async_result.successful_requests,
                    "avg_response_time_ms": async_result.avg_response_time * 1000,
                    "p95_response_time_ms": async_result.p95_response_time * 1000,
                    "requests_per_second": async_result.requests_per_second,
                },
                "batch_test": {
                    "total_requests": batch_result.total_requests,
                    "successful": batch_result.successful_requests,
                    "avg_response_time_ms": batch_result.avg_response_time * 1000,
                },
            },
            f,
            indent=2,
        )

    print(f"\n✅ Results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
