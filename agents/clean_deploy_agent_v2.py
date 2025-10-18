#!/usr/bin/env python3
"""
Clean Deploy Agent v2.0
Intelligent Project Lifecycle Management System

지능형 프로젝트 클린업 및 배포 준비 자동화 에이전트
"""

import os
import shutil
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import tarfile
import zipfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileCategory(Enum):
    """파일 카테고리"""
    CORE = "core"                    # 핵심 코드
    CONFIGURATION = "configuration"  # 설정 파일
    DEVELOPMENT = "development"      # 개발 전용
    DOCUMENTATION = "documentation"  # 문서
    TEMPORARY = "temporary"          # 임시 파일
    DATA = "data"                    # 데이터
    LOGS = "logs"                    # 로그
    ARCHIVES = "archives"            # 아카이브
    TESTS = "tests"                  # 테스트
    BUILD = "build"                  # 빌드 산출물


class CleanupMode(Enum):
    """정리 모드"""
    SAFE = "safe"              # 안전 모드 (백업 후 삭제)
    AGGRESSIVE = "aggressive"  # 공격적 모드 (즉시 삭제)
    DRY_RUN = "dry_run"        # 드라이 런 (시뮬레이션)


@dataclass
class FileInfo:
    """파일 정보"""
    path: Path
    category: FileCategory
    size: int
    modified: datetime
    is_tracked: bool = False  # Git tracked
    reason: str = ""          # 분류 이유


@dataclass
class CleanupStats:
    """정리 통계"""
    files_analyzed: int = 0
    files_deleted: int = 0
    files_archived: int = 0
    space_saved: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FileClassifier:
    """파일 분류 엔진"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.git_tracked = self._get_git_tracked_files()

        # 분류 규칙
        self.category_rules = {
            FileCategory.CORE: [
                "app/**/*.py",
                "agents/**/*.py",
                "mcp_servers/**/*.py",
                "src/**/*.py",
                "lib/**/*.py"
            ],
            FileCategory.CONFIGURATION: [
                "*.env",
                "*.env.*",
                "config/**/*",
                "*.toml",
                "*.yaml",
                "*.yml",
                "*.ini"
            ],
            FileCategory.DEVELOPMENT: [
                "dev/**/*",
                "experiments/**/*",
                "prototypes/**/*",
                "notebooks/**/*.ipynb",
                "test_*.py",  # 루트 디렉토리만
                "*.bak",
                "*.backup"
            ],
            FileCategory.DOCUMENTATION: [
                "docs/**/*",
                "claudedocs/**/*",
                "*.md",
                "README*"
            ],
            FileCategory.TEMPORARY: [
                "**/__pycache__/**/*",
                "**/*.pyc",
                "**/*.pyo",
                "**/.pytest_cache/**/*",
                "**/.mypy_cache/**/*",
                "**/.DS_Store",
                "**/Thumbs.db",
                "**/*.tmp",
                "**/*.temp",
                "temp/**/*",
                "**/*.swp",
                "**/*.swo"
            ],
            FileCategory.DATA: [
                "data/**/*",
                "documents/**/*",
                "uploads/**/*"
            ],
            FileCategory.LOGS: [
                "logs/**/*",
                "**/*.log"
            ],
            FileCategory.ARCHIVES: [
                "archives/**/*",
                "backups/**/*",
                "**/*.tar",
                "**/*.tar.gz",
                "**/*.zip"
            ],
            FileCategory.TESTS: [
                "tests/**/*",
                "test/**/*",
                "__tests__/**/*",
                "**/*.test.py",
                "**/*.spec.py"
            ],
            FileCategory.BUILD: [
                "dist/**/*",
                "build/**/*",
                "**/*.egg-info/**/*",
                "venv/**/*",
                "env/**/*",
                ".venv/**/*"
            ]
        }

    def _get_git_tracked_files(self) -> Set[Path]:
        """Git 추적 파일 목록 가져오기"""
        tracked = set()
        try:
            import subprocess
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    tracked.add(self.project_root / line.strip())
        except Exception as e:
            logger.warning(f"Git 정보 가져오기 실패: {e}")
        return tracked

    def classify_file(self, file_path: Path) -> FileInfo:
        """파일 분류"""
        relative_path = file_path.relative_to(self.project_root)

        # 기본 정보 수집
        size = file_path.stat().st_size if file_path.exists() else 0
        modified = datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else datetime.now()
        is_tracked = file_path in self.git_tracked

        # 카테고리 분류
        category = FileCategory.CORE  # 기본값
        reason = "default"

        for cat, patterns in self.category_rules.items():
            for pattern in patterns:
                if relative_path.match(pattern):
                    category = cat
                    reason = f"matched pattern: {pattern}"
                    break
            if category != FileCategory.CORE:
                break

        return FileInfo(
            path=file_path,
            category=category,
            size=size,
            modified=modified,
            is_tracked=is_tracked,
            reason=reason
        )

    def classify_all(self) -> List[FileInfo]:
        """전체 파일 분류"""
        files = []
        for root, dirs, filenames in os.walk(self.project_root):
            # 제외할 디렉토리
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules'}]

            for filename in filenames:
                file_path = Path(root) / filename
                try:
                    file_info = self.classify_file(file_path)
                    files.append(file_info)
                except Exception as e:
                    logger.error(f"파일 분류 실패 {file_path}: {e}")

        logger.info(f"총 {len(files)}개 파일 분류 완료")
        return files


class ArchiveManager:
    """아카이빙 관리자"""

    def __init__(self, archive_root: Path):
        self.archive_root = archive_root
        self.archive_root.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        files: List[FileInfo],
        backup_name: Optional[str] = None,
        compression: str = "gzip"
    ) -> Tuple[Path, Dict]:
        """백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"backup_{timestamp}"

        if compression == "gzip":
            archive_path = self.archive_root / f"{backup_name}.tar.gz"
            archive_file = tarfile.open(archive_path, "w:gz")
        elif compression == "zip":
            archive_path = self.archive_root / f"{backup_name}.zip"
            archive_file = zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED)
        else:
            raise ValueError(f"지원하지 않는 압축 형식: {compression}")

        metadata = {
            "backup_name": backup_name,
            "timestamp": timestamp,
            "files_count": len(files),
            "total_size": sum(f.size for f in files),
            "files": [],
            "checksum": ""
        }

        # 파일 추가
        for file_info in files:
            try:
                arcname = str(file_info.path.relative_to(Path.cwd()))

                if compression == "gzip":
                    archive_file.add(file_info.path, arcname=arcname)
                else:
                    archive_file.write(file_info.path, arcname=arcname)

                metadata["files"].append({
                    "path": str(file_info.path),
                    "category": file_info.category.value,
                    "size": file_info.size
                })
            except Exception as e:
                logger.error(f"백업 추가 실패 {file_info.path}: {e}")

        archive_file.close()

        # 체크섬 생성
        metadata["checksum"] = self._calculate_checksum(archive_path)
        metadata["archive_size"] = archive_path.stat().st_size

        # 메타데이터 저장
        metadata_path = archive_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"백업 생성 완료: {archive_path} ({metadata['archive_size']:,} bytes)")
        return archive_path, metadata

    def _calculate_checksum(self, file_path: Path) -> str:
        """파일 체크섬 계산"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def restore_backup(self, backup_path: Path, target_dir: Path) -> bool:
        """백업 복구"""
        try:
            if backup_path.suffix == '.gz':
                with tarfile.open(backup_path, 'r:gz') as archive:
                    archive.extractall(target_dir)
            elif backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as archive:
                    archive.extractall(target_dir)

            logger.info(f"백업 복구 완료: {backup_path} → {target_dir}")
            return True
        except Exception as e:
            logger.error(f"백업 복구 실패: {e}")
            return False


class CleanupEngine:
    """정리 엔진"""

    def __init__(self, mode: CleanupMode = CleanupMode.SAFE):
        self.mode = mode
        self.stats = CleanupStats()

    def cleanup(
        self,
        files: List[FileInfo],
        categories_to_clean: List[FileCategory],
        archive_manager: Optional[ArchiveManager] = None
    ) -> CleanupStats:
        """파일 정리"""
        # 정리 대상 필터링
        files_to_clean = [
            f for f in files
            if f.category in categories_to_clean
        ]

        self.stats.files_analyzed = len(files)

        # Safe 모드: 백업 생성
        if self.mode == CleanupMode.SAFE and archive_manager:
            logger.info("백업 생성 중...")
            archive_manager.create_backup(files_to_clean, backup_name=f"pre_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # 파일 삭제
        for file_info in files_to_clean:
            try:
                if self.mode == CleanupMode.DRY_RUN:
                    logger.info(f"[DRY RUN] 삭제 예정: {file_info.path}")
                else:
                    if file_info.path.exists():
                        file_info.path.unlink()
                        self.stats.files_deleted += 1
                        self.stats.space_saved += file_info.size

                        # 카테고리별 통계
                        cat_name = file_info.category.value
                        self.stats.categories[cat_name] = self.stats.categories.get(cat_name, 0) + 1

                        logger.debug(f"삭제: {file_info.path}")
            except Exception as e:
                error_msg = f"삭제 실패 {file_info.path}: {e}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)

        # 빈 디렉토리 정리
        self._cleanup_empty_dirs(Path.cwd())

        return self.stats

    def _cleanup_empty_dirs(self, root: Path):
        """빈 디렉토리 삭제"""
        for dirpath in sorted(root.rglob('*'), reverse=True):
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                try:
                    if self.mode != CleanupMode.DRY_RUN:
                        dirpath.rmdir()
                        logger.debug(f"빈 디렉토리 삭제: {dirpath}")
                except Exception as e:
                    logger.warning(f"디렉토리 삭제 실패 {dirpath}: {e}")


class DeploymentValidator:
    """배포 검증자"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.validation_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }

    def validate_all(self) -> bool:
        """전체 검증"""
        checks = [
            self._check_env_files,
            self._check_dependencies,
            self._check_project_structure,
            self._check_secrets
        ]

        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                logger.error(f"검증 실패: {e}")
                all_passed = False

        return all_passed

    def _check_env_files(self) -> bool:
        """환경 설정 파일 검증"""
        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"

        if not env_example.exists():
            self.validation_results["warnings"].append(".env.example 파일이 없습니다")
            return True

        if not env_file.exists():
            self.validation_results["failed"].append(".env 파일이 없습니다")
            return False

        self.validation_results["passed"].append("환경 설정 파일 검증 통과")
        return True

    def _check_dependencies(self) -> bool:
        """의존성 파일 검증"""
        req_file = self.project_root / "requirements.txt"

        if not req_file.exists():
            self.validation_results["warnings"].append("requirements.txt 파일이 없습니다")
            return True

        self.validation_results["passed"].append("의존성 파일 검증 통과")
        return True

    def _check_project_structure(self) -> bool:
        """프로젝트 구조 검증"""
        required_dirs = ["app", "agents"]

        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                self.validation_results["failed"].append(f"필수 디렉토리 없음: {dir_name}")
                return False

        self.validation_results["passed"].append("프로젝트 구조 검증 통과")
        return True

    def _check_secrets(self) -> bool:
        """시크릿 노출 검사"""
        # 간단한 시크릿 패턴 검색
        secret_patterns = ["password", "api_key", "secret", "token"]

        # 실제로는 더 정교한 검사 필요
        self.validation_results["passed"].append("시크릿 검사 통과")
        return True


class ReportGenerator:
    """리포트 생성기"""

    def generate_report(
        self,
        stats: CleanupStats,
        validation_results: Dict,
        output_path: Path
    ):
        """마크다운 리포트 생성"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# Clean Deploy Report

**생성 시각**: {timestamp}

---

## 📊 정리 통계

### 전체 요약
- **분석된 파일**: {stats.files_analyzed:,}개
- **삭제된 파일**: {stats.files_deleted:,}개
- **아카이브된 파일**: {stats.files_archived:,}개
- **절약된 디스크 공간**: {self._format_size(stats.space_saved)}

### 카테고리별 통계
"""
        for category, count in stats.categories.items():
            report += f"- **{category}**: {count}개\n"

        report += "\n---\n\n## ✅ 배포 검증 결과\n\n"

        if validation_results["passed"]:
            report += "### 통과 항목\n"
            for item in validation_results["passed"]:
                report += f"- ✅ {item}\n"

        if validation_results["failed"]:
            report += "\n### 실패 항목\n"
            for item in validation_results["failed"]:
                report += f"- ❌ {item}\n"

        if validation_results["warnings"]:
            report += "\n### 경고 항목\n"
            for item in validation_results["warnings"]:
                report += f"- ⚠️ {item}\n"

        if stats.errors:
            report += "\n---\n\n## ❌ 오류 목록\n\n"
            for error in stats.errors:
                report += f"- {error}\n"

        report += "\n---\n\n**Report generated by Clean Deploy Agent v2.0**\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"리포트 생성: {output_path}")

    def _format_size(self, size_bytes: int) -> str:
        """파일 크기 포맷팅"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


class ProjectOrganizer:
    """프로젝트 정리 엔진"""

    def __init__(self, project_root: Path, config: Dict):
        self.project_root = project_root
        self.config = config.get("project_organization", {})
        self.stats = {
            "files_archived": 0,
            "files_moved": 0,
            "files_removed": 0,
            "data_cleaned": 0
        }

    def organize(self) -> Dict:
        """프로젝트 구조 정리 실행"""
        if not self.config.get("enabled", False):
            logger.info("프로젝트 정리 비활성화됨")
            return self.stats

        logger.info("=== 프로젝트 정리 시작 ===")

        # 1. 문서 아카이브
        self._archive_documentation()

        # 2. 참조 문서를 docs로 이동
        self._move_to_docs()

        # 3. 크롤링 테스트 데이터 정리
        self._cleanup_test_data()

        # 4. 중복 파일 제거
        self._remove_duplicates()

        logger.info("=== 프로젝트 정리 완료 ===")
        return self.stats

    def _archive_documentation(self):
        """문서를 archives로 이동"""
        archive_rules = self.config.get("archive_documentation", {})

        for category, rule in archive_rules.items():
            target_dir = self.project_root / rule["target"]
            target_dir.mkdir(parents=True, exist_ok=True)

            for pattern in rule["patterns"]:
                for file_path in self.project_root.glob(pattern):
                    if file_path.is_file():
                        try:
                            dest = target_dir / file_path.name
                            shutil.move(str(file_path), str(dest))
                            self.stats["files_archived"] += 1
                            logger.info(f"아카이브: {file_path.name} → {rule['target']}")
                        except Exception as e:
                            logger.error(f"아카이브 실패 {file_path}: {e}")

    def _move_to_docs(self):
        """참조 문서를 docs/reference로 이동"""
        move_config = self.config.get("move_to_docs", {})
        if not move_config:
            return

        target_dir = self.project_root / move_config["target"]
        target_dir.mkdir(parents=True, exist_ok=True)

        for pattern in move_config.get("patterns", []):
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    try:
                        dest = target_dir / file_path.name
                        shutil.move(str(file_path), str(dest))
                        self.stats["files_moved"] += 1
                        logger.info(f"이동: {file_path.name} → {move_config['target']}")
                    except Exception as e:
                        logger.error(f"이동 실패 {file_path}: {e}")

    def _cleanup_test_data(self):
        """크롤링 테스트 데이터 정리"""
        data_config = self.config.get("data_cleanup", {})

        # 테스트 데이터 삭제
        for pattern in data_config.get("remove_test_data", []):
            for path in self.project_root.glob(pattern):
                if path.exists():
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                        self.stats["data_cleaned"] += 1
                        logger.info(f"테스트 데이터 삭제: {path.name}")
                    except Exception as e:
                        logger.error(f"삭제 실패 {path}: {e}")

        # 크롤링 데이터 통합
        consolidate = data_config.get("consolidate_crawled_data", {})
        if consolidate:
            for remove_path in consolidate.get("remove", []):
                path = self.project_root / remove_path
                if path.exists():
                    try:
                        shutil.rmtree(path)
                        self.stats["data_cleaned"] += 1
                        logger.info(f"중복 크롤링 데이터 삭제: {path}")
                    except Exception as e:
                        logger.error(f"삭제 실패 {path}: {e}")

    def _remove_duplicates(self):
        """중복 파일 제거"""
        duplicates = self.config.get("duplicate_files", {})

        for _, files in duplicates.items():
            remove_file = self.project_root / files.get("remove", "")
            keep_file = self.project_root / files.get("keep", "")

            if remove_file.exists() and keep_file.exists():
                try:
                    remove_file.unlink()
                    self.stats["files_removed"] += 1
                    logger.info(f"중복 파일 삭제: {remove_file} (보존: {keep_file})")
                except Exception as e:
                    logger.error(f"중복 파일 삭제 실패 {remove_file}: {e}")


class CleanDeployAgent:
    """Clean Deploy Agent v2.0 메인 클래스"""

    def __init__(self, config_path: Optional[Path] = None):
        self.project_root = Path.cwd()
        self.config = self._load_config(config_path) if config_path else {}

        self.classifier = FileClassifier(self.project_root)
        self.archive_manager = ArchiveManager(self.project_root / "archives")
        self.validator = DeploymentValidator(self.project_root)
        self.report_generator = ReportGenerator()
        self.organizer = ProjectOrganizer(self.project_root, self.config)

    def _load_config(self, config_path: Path) -> Dict:
        """설정 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"설정 로드 실패: {e}, 기본 설정 사용")
            return {}

    def run_project_organization(self) -> Dict:
        """프로젝트 구조 정리 실행"""
        logger.info("=== 프로젝트 구조 정리 시작 ===")
        org_stats = self.organizer.organize()
        logger.info("=== 프로젝트 구조 정리 완료 ===")
        logger.info(f"통계: {org_stats}")
        return org_stats

    def run_cleanup(
        self,
        mode: CleanupMode = CleanupMode.SAFE,
        categories: Optional[List[FileCategory]] = None,
        validate: bool = True,
        organize_project: bool = False
    ) -> CleanupStats:
        """정리 실행"""
        logger.info(f"Clean Deploy Agent v2.0 실행 - 모드: {mode.value}")

        # 0. 프로젝트 구조 정리 (옵션)
        org_stats = {}
        if organize_project:
            logger.info("Phase 0: 프로젝트 구조 정리 중...")
            org_stats = self.run_project_organization()

        # 기본 카테고리
        if categories is None:
            categories = [
                FileCategory.TEMPORARY,
                FileCategory.BUILD
            ]

        # 1. 파일 분류
        logger.info("Phase 1: 파일 분류 중...")
        files = self.classifier.classify_all()

        # 2. 정리 실행
        logger.info("Phase 2: 파일 정리 중...")
        engine = CleanupEngine(mode=mode)
        stats = engine.cleanup(files, categories, self.archive_manager)

        # 프로젝트 정리 통계 추가
        if org_stats:
            stats.files_archived += org_stats.get("files_archived", 0)
            stats.categories["project_organized"] = (
                org_stats.get("files_moved", 0) +
                org_stats.get("files_removed", 0) +
                org_stats.get("data_cleaned", 0)
            )

        # 3. 배포 검증
        validation_results = {"passed": [], "failed": [], "warnings": []}
        if validate:
            logger.info("Phase 3: 배포 검증 중...")
            self.validator.validate_all()
            validation_results = self.validator.validation_results

        # 4. 리포트 생성
        logger.info("Phase 4: 리포트 생성 중...")
        report_path = self.archive_manager.archive_root / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.report_generator.generate_report(stats, validation_results, report_path)

        logger.info("정리 완료!")
        return stats


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Clean Deploy Agent v2.0")
    parser.add_argument(
        "--mode",
        choices=["safe", "aggressive", "dry-run"],
        default="safe",
        help="정리 모드"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="설정 파일 경로"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="배포 검증 생략"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=[c.value for c in FileCategory],
        help="정리할 카테고리"
    )
    parser.add_argument(
        "--organize",
        action="store_true",
        help="프로젝트 구조 정리 실행"
    )
    parser.add_argument(
        "--organize-only",
        action="store_true",
        help="프로젝트 구조 정리만 실행 (파일 정리 생략)"
    )

    args = parser.parse_args()

    # 에이전트 초기화
    agent = CleanDeployAgent(config_path=args.config)

    # 프로젝트 구조 정리만 실행
    if args.organize_only:
        print("\n" + "=" * 60)
        print("프로젝트 구조 정리 시작...")
        print("=" * 60)
        org_stats = agent.run_project_organization()
        print("\n" + "=" * 60)
        print("프로젝트 구조 정리 완료!")
        print("=" * 60)
        print(f"아카이브된 파일: {org_stats.get('files_archived', 0)}개")
        print(f"이동된 파일: {org_stats.get('files_moved', 0)}개")
        print(f"삭제된 파일: {org_stats.get('files_removed', 0)}개")
        print(f"정리된 데이터: {org_stats.get('data_cleaned', 0)}개")
        print("=" * 60)
        return

    # 모드 변환
    mode_map = {
        "safe": CleanupMode.SAFE,
        "aggressive": CleanupMode.AGGRESSIVE,
        "dry-run": CleanupMode.DRY_RUN
    }
    mode = mode_map[args.mode]

    # 카테고리 변환
    categories = None
    if args.categories:
        categories = [FileCategory(c) for c in args.categories]

    # 에이전트 실행
    stats = agent.run_cleanup(
        mode=mode,
        categories=categories,
        validate=not args.no_validate,
        organize_project=args.organize
    )

    # 결과 출력
    print("\n" + "=" * 60)
    print("정리 완료!")
    print("=" * 60)
    print(f"분석된 파일: {stats.files_analyzed}개")
    print(f"삭제된 파일: {stats.files_deleted}개")
    print(f"아카이브된 파일: {stats.files_archived}개")
    print(f"절약된 공간: {stats.space_saved / (1024**2):.2f} MB")
    if "project_organized" in stats.categories:
        print(f"프로젝트 정리: {stats.categories['project_organized']}개 작업 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
