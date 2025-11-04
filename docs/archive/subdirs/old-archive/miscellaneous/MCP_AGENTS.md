# 🤖 MCP 서버 & 에이전트 상세

## MCP 서버 구성

### 인프라 서비스 (Docker)
```yaml
qdrant:
  host: 172.28.0.2
  ports: [6333, 6334]
  role: 벡터 검색 엔진

redis:
  host: 172.28.0.3
  port: 6379
  role: 캐싱 및 세션

postgres:
  host: 172.28.0.4
  port: 5432
  role: 메타데이터 저장

n8n:
  host: 172.28.0.5
  port: 5678
  role: 워크플로우 자동화

ollama:
  host: 172.28.0.6
  port: 11434
  role: 로컬 LLM 추론
```

### Python MCP 서버 (.mcp.json)
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["mcp_servers/filesystem_server.py"],
      "env": {
        "ALLOWED_DIRS": "/Users/oypnus/Project/rag-enterprise/documents"
      }
    },
    "qdrant_server": {
      "command": "python",
      "args": ["mcp_servers/qdrant_server.py"],
      "env": {
        "QDRANT_HOST": "172.28.0.2",
        "QDRANT_PORT": "6333"
      }
    },
    "ollama_server": {
      "command": "python",
      "args": ["mcp_servers/ollama_server.py"],
      "env": {
        "OLLAMA_HOST": "http://172.28.0.6:11434"
      }
    }
  }
}
```

---

## 커스텀 에이전트

### workflow_orchestrator
```python
class WorkflowOrchestrator:
    """중앙 파이프라인 조정"""

    config = {
        'max_workers': 4,
        'batch_size': 10,
        'retry_attempts': 3,
        'timeout': 300
    }

    async def execute_pipeline(self, pipeline_name: str, inputs: Dict):
        """파이프라인 실행"""
        pipeline = self.pipelines[pipeline_name]

        tasks = []
        for stage in pipeline.stages:
            task = asyncio.create_task(
                self.execute_stage(stage, inputs)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

### crawler_scheduler
```python
class CrawlerScheduler:
    """자동 크롤링 스케줄러"""

    config = {
        'schedule': "0 */6 * * *",  # 6시간마다
        'targets': "./config/crawl_targets.json"
    }

    async def run_scheduled_crawl(self):
        """스케줄 기반 크롤링"""
        targets = self.load_targets()

        for target in targets:
            await self.crawl_and_process(target)
```

### quality_monitor
```python
class QualityMonitor:
    """RAG 품질 모니터링"""

    config = {
        'evaluation_interval': 3600,  # 1시간
        'metrics': ['relevance', 'accuracy', 'latency']
    }

    async def evaluate_quality(self):
        """품질 평가"""
        results = await self.run_ragas_evaluation()

        if results['relevance'] < 0.8:
            await self.alert_quality_degradation()
```

---

*Last Updated: 2025-10-18*
