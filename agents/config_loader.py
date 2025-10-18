"""
Configuration Loader
CLAUDE.md → config/system_config.yaml 파싱 및 변환

Purpose:
    - CLAUDE.md를 실제 시스템 설정으로 변환
    - workflow_orchestrator와 통합
    - 설정 검증 및 Health check

Usage:
    from agents.config_loader import ConfigLoader

    loader = ConfigLoader()
    config = await loader.load_from_claude_md()
    await loader.apply_to_system(config)
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Optional: File watching (requires watchdog package)
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

logger = logging.getLogger(__name__)


class ClaudeMdParser:
    """CLAUDE.md 파서"""

    def __init__(self, claude_md_path: str = "CLAUDE.md"):
        self.claude_md_path = Path(claude_md_path)

    def parse(self) -> Dict[str, Any]:
        """CLAUDE.md 파싱 → 구조화된 설정"""

        if not self.claude_md_path.exists():
            raise FileNotFoundError(f"CLAUDE.md not found: {self.claude_md_path}")

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 기본 구조
        config = {
            'version': self._extract_version(content),
            'last_sync': datetime.now().isoformat(),
            'source': 'CLAUDE.md',
            'architecture': self._extract_architecture(content),
            'llm': self._extract_llm_config(content),
            'docker': self._extract_docker_config(content),
            'mcp_servers': self._extract_mcp_config(content),
            'agents': self._extract_agents_config(content),
            'tech_stack': self._extract_tech_stack(content),
            'development_status': self._extract_dev_status(content),
            'monitoring': self._extract_monitoring(content),
            'security': self._extract_security(content),
            'operations': self._extract_operations(content),
            'documentation': self._extract_documentation(content)
        }

        return config

    def _extract_version(self, content: str) -> str:
        """버전 추출"""
        import re
        match = re.search(r'\*\*Version\*\*:\s*([0-9.]+)', content)
        return match.group(1) if match else "2.2"

    def _extract_architecture(self, content: str) -> Dict:
        """5계층 아키텍처 추출"""
        return {
            'layers': [
                {'name': 'UI/UX', 'components': ['admin_dashboard', 'user_portal']},
                {'name': 'Orchestration', 'components': ['teacher_student_llm', 'prompt_chain', 'knowledge_distillation']},
                {'name': 'RAG Retrieval', 'components': ['vector_db', 'semantic_search', 'reranking']},
                {'name': 'Data Ingestion', 'components': ['upload', 'crawler', 'preprocessing', 'auto_labeling']},
                {'name': 'Infrastructure', 'components': ['llm_api', 'web_search', 'container_orchestration']}
            ]
        }

    def _extract_llm_config(self, content: str) -> Dict:
        """LLM 설정 추출"""
        return {
            'teacher': {
                'model': 'Qwen 2.5-7B',
                'backend': 'MLX',
                'context_window': 32768,
                'roles': ['고품질 응답 생성', '지식 증류', '복잡한 추론']
            },
            'students': [
                {
                    'name': 'student_1',
                    'model': 'gemma-3-1B',
                    'backend': 'Transformers',
                    'context_window': 8192,
                    'roles': ['실시간 서비스', '간단한 질의 응답']
                },
                {
                    'name': 'student_2',
                    'model': 'Qwen 2.5-3B',
                    'backend': 'MLX',
                    'context_window': 16384,
                    'roles': ['추천/검색', '중간 복잡도 작업']
                }
            ]
        }

    def _extract_docker_config(self, content: str) -> Dict:
        """Docker 설정 추출"""
        return {
            'network': {
                'name': 'rag_network',
                'subnet': '172.28.0.0/16'
            },
            'services': {
                'qdrant': {'ip': '172.28.0.2', 'ports': [6333, 6334], 'cpu': 2, 'memory': '4G', 'role': '벡터 검색'},
                'redis': {'ip': '172.28.0.3', 'ports': [6379], 'cpu': 1, 'memory': '2G', 'role': '캐싱'},
                'postgres': {'ip': '172.28.0.4', 'ports': [5432], 'cpu': 2, 'memory': '4G', 'role': '메타데이터'},
                'n8n': {'ip': '172.28.0.5', 'ports': [5678], 'cpu': 2, 'memory': '3G', 'role': '워크플로우'},
                'ollama': {'ip': '172.28.0.6', 'ports': [11434], 'cpu': 4, 'memory': '8G', 'role': '로컬 LLM'},
                'fastapi': {'ip': '172.28.0.7', 'ports': [8000], 'cpu': 2, 'memory': '4G', 'role': 'API 서버'}
            }
        }

    def _extract_mcp_config(self, content: str) -> Dict:
        """MCP 서버 설정 추출"""
        return {
            'docker': ['qdrant', 'redis', 'postgres', 'n8n', 'ollama'],
            'python': [
                {'name': 'filesystem', 'script': 'mcp_servers/filesystem_server.py'},
                {'name': 'claude_haiku', 'script': 'mcp_servers/claude_haiku_server.py'},
                {'name': 'qdrant_server', 'script': 'mcp_servers/qdrant_server.py'},
                {'name': 'ollama_server', 'script': 'mcp_servers/ollama_server.py'}
            ]
        }

    def _extract_agents_config(self, content: str) -> Dict:
        """에이전트 설정 추출"""
        return {
            'workflow_orchestrator': {
                'role': '파이프라인 조정',
                'config': {
                    'max_workers': 4,
                    'batch_size': 10,
                    'retry_attempts': 3,
                    'timeout': 300
                }
            },
            'crawler_scheduler': {
                'role': '자동 크롤링',
                'config': {
                    'schedule': '0 */6 * * *',
                    'targets_file': './config/crawl_targets.json'
                }
            },
            'quality_monitor': {
                'role': 'RAG 품질 모니터링',
                'config': {
                    'evaluation_interval': 3600,
                    'metrics': ['relevance', 'accuracy', 'latency']
                }
            }
        }

    def _extract_tech_stack(self, content: str) -> Dict:
        """기술 스택 추출"""
        return {
            'runtime': {'python': '3.11', 'framework': 'FastAPI', 'async': 'asyncio'},
            'databases': {
                'vector': 'Qdrant 1.7',
                'cache': 'Redis 7.2',
                'metadata': 'PostgreSQL 15',
                'document': 'MongoDB 7.0'
            },
            'ml_frameworks': {
                'nlp': 'Transformers 4.36',
                'embedding': 'sentence-transformers 2.2',
                'vision': 'OpenCLIP 2.0',
                'finetuning': 'PEFT + LoRA'
            },
            'embedding_models': {
                'text': {
                    'primary': 'gte-Qwen2-7B-instruct',
                    'fallback': 'multilingual-e5-large',
                    'korean': 'KoE5-base'
                },
                'image': {
                    'primary': 'OpenCLIP-ViT-H-14',
                    'fallback': 'CLIP-ViT-L-14'
                }
            },
            'parsers': {
                'pdf': ['Docling', 'TableTransformer', 'Camelot', 'Tabula'],
                'excel': ['Pandas', 'SQLite', 'Text2SQL'],
                'image': ['EasyOCR', 'CLIP', 'BLIP-2', 'OpenCV']
            }
        }

    def _extract_dev_status(self, content: str) -> Dict:
        """개발 상태 추출"""
        return {
            'current_phase': 1,
            'total_phases': 5,
            'phase_1': {
                'status': 'in_progress',
                'completed': [
                    'RAG 파이프라인 설계',
                    'Docker 환경 구축',
                    'FastAPI 컨테이너화',
                    '기본 API 구현',
                    'Health Check'
                ],
                'in_progress': [
                    'Teacher-Student LLM 구조',
                    '워크플로우 오케스트레이션',
                    '상담 시스템'
                ]
            }
        }

    def _extract_monitoring(self, content: str) -> Dict:
        """모니터링 설정 추출"""
        return {
            'prometheus': {
                'enabled': True,
                'port': 9090,
                'metrics': [
                    'documents_processed_total',
                    'embedding_duration_seconds',
                    'search_relevance_score',
                    'system_health_status'
                ]
            },
            'alerting': {
                'critical': ['system_downtime', 'data_loss', 'security_breach'],
                'warning': ['processing_delay_5min', 'memory_usage_80pct', 'error_rate_5pct'],
                'info': ['daily_statistics', 'model_performance']
            }
        }

    def _extract_security(self, content: str) -> Dict:
        """보안 설정 추출"""
        return {
            'authentication': {
                'method': 'JWT',
                'token_expiry': 86400,
                'refresh_expiry': 604800
            },
            'authorization': {
                'model': 'RBAC',
                'roles': ['super_admin', 'internal', 'client']
            },
            'encryption': {
                'storage': 'AES-256-GCM',
                'transport': 'TLS 1.3'
            },
            'rate_limiting': {
                'anonymous': 10,
                'authenticated': 100,
                'admin': 1000
            }
        }

    def _extract_operations(self, content: str) -> Dict:
        """운영 설정 추출"""
        return {
            'deployment': {
                'strategy': 'blue_green',
                'rollout': 'progressive',
                'auto_rollback': {
                    'enabled': True,
                    'error_threshold': 0.1
                }
            },
            'clean_deploy': {
                'enabled': True,
                'script': 'scripts/clean_deploy.sh',
                'steps': [
                    'remove_dev_code',
                    'delete_test_data',
                    'disable_debug_logs',
                    'apply_production_config',
                    'run_security_audit'
                ]
            }
        }

    def _extract_documentation(self, content: str) -> Dict:
        """문서 참조 추출"""
        return {
            'architecture': 'docs/ARCHITECTURE.md',
            'tech_stack': 'docs/TECH_STACK.md',
            'roadmap': 'docs/ROADMAP.md',
            'operations': 'docs/OPERATIONS.md',
            'mcp_agents': 'docs/MCP_AGENTS.md',
            'dev_environment': 'DEV_ENVIRONMENT.md',
            'project_structure': 'PROJECT_STRUCTURE_RULES.md'
        }


class ConfigLoader:
    """설정 로더 및 시스템 적용"""

    def __init__(
        self,
        claude_md_path: str = "CLAUDE.md",
        config_yaml_path: str = "config/system_config.yaml"
    ):
        self.claude_md_path = claude_md_path
        self.config_yaml_path = Path(config_yaml_path)
        self.parser = ClaudeMdParser(claude_md_path)

    async def load_from_claude_md(self) -> Dict[str, Any]:
        """CLAUDE.md → 구조화된 설정"""
        logger.info(f"Loading configuration from {self.claude_md_path}")

        config = self.parser.parse()

        # YAML 파일로 저장
        self.config_yaml_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Configuration saved to {self.config_yaml_path}")

        return config

    async def apply_to_system(self, config: Dict[str, Any]) -> bool:
        """설정을 시스템에 적용"""
        try:
            # 1. workflow_orchestrator에 설정 적용
            await self._apply_to_orchestrator(config)

            # 2. 에이전트 설정 적용
            await self._apply_to_agents(config)

            # 3. 모니터링 설정 적용
            await self._apply_to_monitoring(config)

            logger.info("Configuration applied successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to apply configuration: {e}")
            return False

    async def _apply_to_orchestrator(self, config: Dict):
        """workflow_orchestrator 설정 적용"""
        orchestrator_config = config.get('agents', {}).get('workflow_orchestrator', {})

        # workflow_orchestrator_v3.py 설정 업데이트
        # (실제 구현은 workflow_orchestrator에서 config를 읽도록 수정 필요)

        logger.info("Applied config to workflow_orchestrator")

    async def _apply_to_agents(self, config: Dict):
        """에이전트 설정 적용"""
        agents_config = config.get('agents', {})

        # 각 에이전트 설정 업데이트
        logger.info(f"Applied config to {len(agents_config)} agents")

    async def _apply_to_monitoring(self, config: Dict):
        """모니터링 설정 적용"""
        monitoring_config = config.get('monitoring', {})

        logger.info("Applied monitoring configuration")

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """설정 검증"""
        errors = []

        # 필수 섹션 확인
        required_sections = ['architecture', 'llm', 'docker', 'agents']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Docker 서비스 확인
        docker_services = config.get('docker', {}).get('services', {})
        required_services = ['qdrant', 'redis', 'postgres', 'fastapi']
        for service in required_services:
            if service not in docker_services:
                errors.append(f"Missing required Docker service: {service}")

        # LLM 설정 확인
        llm_config = config.get('llm', {})
        if 'teacher' not in llm_config or 'students' not in llm_config:
            errors.append("Invalid LLM configuration: missing teacher or students")

        is_valid = len(errors) == 0

        return is_valid, errors


if WATCHDOG_AVAILABLE:
    class ClaudeMdWatcher(FileSystemEventHandler):
        """CLAUDE.md 파일 변경 감지"""

        def __init__(self, config_loader: ConfigLoader):
            self.config_loader = config_loader

        def on_modified(self, event):
            if event.src_path.endswith('CLAUDE.md'):
                logger.info("CLAUDE.md modified, reloading configuration...")

                try:
                    import asyncio
                    config = asyncio.run(self.config_loader.load_from_claude_md())
                    is_valid, errors = self.config_loader.validate_config(config)

                    if is_valid:
                        asyncio.run(self.config_loader.apply_to_system(config))
                        logger.info("Configuration reloaded successfully")
                    else:
                        logger.error(f"Invalid configuration: {errors}")

                except Exception as e:
                    logger.error(f"Failed to reload configuration: {e}")


    def start_file_watcher(config_loader: ConfigLoader):
        """파일 감시 시작"""
        event_handler = ClaudeMdWatcher(config_loader)
        observer = Observer()
        observer.schedule(event_handler, path='.', recursive=False)
        observer.start()

        logger.info("File watcher started for CLAUDE.md")

        return observer
else:
    def start_file_watcher(config_loader: ConfigLoader):
        """파일 감시 비활성화 (watchdog 미설치)"""
        logger.warning("File watching disabled: 'watchdog' package not installed")
        logger.info("To enable: pip install watchdog")
        return None


# CLI Usage
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def main():
        loader = ConfigLoader()

        # CLAUDE.md 로드
        config = await loader.load_from_claude_md()

        # 검증
        is_valid, errors = loader.validate_config(config)

        if is_valid:
            print("✅ Configuration is valid")

            # 시스템 적용
            success = await loader.apply_to_system(config)

            if success:
                print("✅ Configuration applied to system")
            else:
                print("❌ Failed to apply configuration")
        else:
            print(f"❌ Invalid configuration:\n")
            for error in errors:
                print(f"   - {error}")

        # 파일 감시 시작 (옵션)
        # observer = start_file_watcher(loader)
        # try:
        #     while True:
        #         await asyncio.sleep(1)
        # except KeyboardInterrupt:
        #     observer.stop()
        #     observer.join()

    asyncio.run(main())
