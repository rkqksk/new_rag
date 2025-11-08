"""
Export/Import 서비스
- 훈련 데이터를 외부 Linux로 내보내기
- 미세조정 모델을 Ollama로 임포트
"""

import json
import logging
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExportConfig:
    """내보내기 설정"""
    output_dir: str = "./exports"
    include_metadata: bool = True
    compress: bool = False
    timestamp: bool = True


@dataclass
class ImportConfig:
    """임포트 설정"""
    model_path: str
    model_name: str = "qwen2.5:3b-finetuned"
    system_prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class TrainingDataExporter:
    """훈련 데이터 내보내기"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Args:
            config: 내보내기 설정
        """
        self.config = config or ExportConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_training_data(
        self,
        training_samples: List[Dict[str, Any]]
    ) -> Optional[Path]:
        """
        훈련 데이터를 JSON 파일로 내보내기
        
        Args:
            training_samples: 훈련 샘플 리스트
            
        Returns:
            내보낸 파일 경로
        """
        try:
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if self.config.timestamp else ""
            filename = f"training_data_{timestamp}.json" if timestamp else "training_data.json"
            output_file = self.output_dir / filename
            
            # 메타데이터 추가
            export_data = {
                "metadata": {
                    "total_samples": len(training_samples),
                    "exported_at": datetime.now().isoformat(),
                    "quality_threshold": 0.80,
                    "model_info": {
                        "teacher": "qwen2.5:7b",
                        "student": "qwen2.5:3b"
                    }
                },
                "data": training_samples
            }
            
            # JSON 파일로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(
                f"[Export] 훈련 데이터 내보내기 완료: {output_file} "
                f"({len(training_samples)} samples, {file_size_mb:.2f}MB)"
            )
            
            return output_file
            
        except Exception as e:
            logger.error(f"[Export] 훈련 데이터 내보내기 실패: {e}")
            return None
    
    def export_config(
        self,
        config_dict: Dict[str, Any]
    ) -> Optional[Path]:
        """
        LoRA 훈련 설정을 JSON 파일로 내보내기
        
        Args:
            config_dict: 설정 딕셔너리
            
        Returns:
            내보낸 파일 경로
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if self.config.timestamp else ""
            filename = f"lora_config_{timestamp}.json" if timestamp else "lora_config.json"
            output_file = self.output_dir / filename
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[Export] LoRA 설정 내보내기 완료: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"[Export] LoRA 설정 내보내기 실패: {e}")
            return None
    
    def get_export_manifest(self) -> Dict[str, Any]:
        """
        내보내기 매니페스트 생성
        Linux로 전송할 파일 목록
        """
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "files": [],
            "instructions": {
                "1_receive": "exports 디렉토리의 파일들을 수신합니다",
                "2_setup": "Python 환경 설정 및 의존성 설치",
                "3_train": "python finetuning/lora_trainer.py 실행",
                "4_return": "output/student-lora.gguf를 반환합니다"
            }
        }
        
        # 디렉토리의 모든 파일 나열
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                manifest["files"].append({
                    "name": file_path.name,
                    "size_mb": file_path.stat().st_size / (1024 * 1024),
                    "path": str(file_path)
                })
        
        return manifest


class ModelImporter:
    """미세조정 모델 Ollama 임포트"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Args:
            ollama_host: Ollama 서버 주소
        """
        self.ollama_host = ollama_host
    
    def import_finetuned_model(
        self,
        model_path: str,
        model_name: str = "qwen2.5:3b-finetuned"
    ) -> bool:
        """
        미세조정 GGUF 모델을 Ollama에 등록
        
        Args:
            model_path: GGUF 모델 파일 경로
            model_name: 등록할 모델 이름
            
        Returns:
            성공 여부
        """
        try:
            model_path_obj = Path(model_path)
            
            if not model_path_obj.exists():
                logger.error(f"[Import] 모델 파일 없음: {model_path}")
                return False
            
            logger.info(f"[Import] 모델 등록 시작: {model_name}")
            
            # Modelfile 생성
            modelfile_content = f"""FROM {model_path}

PARAMETER temperature 0.5
PARAMETER top_p 0.95
PARAMETER num_ctx 32000

SYSTEM """You are a helpful assistant specialized in manufacturing consultation.""""""
            
            modelfile_path = Path("/tmp") / f"Modelfile_{model_name}"
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            logger.debug(f"[Import] Modelfile 생성: {modelfile_path}")
            
            # Ollama create 명령 실행
            result = subprocess.run(
                [
                    "ollama",
                    "create",
                    model_name,
                    "-f",
                    str(modelfile_path)
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"[Import] 모델 등록 완료: {model_name}")
                
                # Modelfile 정리
                modelfile_path.unlink()
                
                return True
            else:
                logger.error(f"[Import] 모델 등록 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("[Import] 모델 등록 타임아웃")
            return False
        except Exception as e:
            logger.error(f"[Import] 모델 등록 중 오류: {e}")
            return False
    
    def verify_model(self, model_name: str) -> bool:
        """
        등록된 모델 확인
        
        Args:
            model_name: 모델 이름
            
        Returns:
            모델 존재 여부
        """
        try:
            result = subprocess.run(
                ["ollama", "show", model_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"[Import] 모델 확인 성공: {model_name}")
                return True
            else:
                logger.warning(f"[Import] 모델 미등록: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"[Import] 모델 확인 실패: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """
        등록된 모든 모델 목록 조회
        
        Returns:
            모델 이름 리스트
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                models = []
                for line in result.stdout.split('\n')[1:]:  # 헤더 스킵
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                
                logger.info(f"[Import] 등록된 모델: {models}")
                return models
            else:
                logger.error(f"[Import] 모델 목록 조회 실패")
                return []
                
        except Exception as e:
            logger.error(f"[Import] 모델 목록 조회 중 오류: {e}")
            return []


class SCPFileTransfer:
    """SCP를 이용한 파일 전송"""
    
    def __init__(
        self,
        remote_host: str,
        remote_user: str,
        remote_path: str,
        ssh_key: Optional[str] = None
    ):
        """
        Args:
            remote_host: 원격 호스트 IP
            remote_user: 원격 사용자명
            remote_path: 원격 경로
            ssh_key: SSH 개인키 경로
        """
        self.remote_host = remote_host
        self.remote_user = remote_user
        self.remote_path = remote_path
        self.ssh_key = ssh_key
    
    def send_file(self, local_path: str, remote_filename: Optional[str] = None) -> bool:
        """
        Colima → Linux로 파일 전송
        
        Args:
            local_path: 로컬 파일 경로
            remote_filename: 원격 파일명 (기본값: 로컬 파일명)
            
        Returns:
            성공 여부
        """
        try:
            local_path_obj = Path(local_path)
            
            if not local_path_obj.exists():
                logger.error(f"[SCP] 파일 없음: {local_path}")
                return False
            
            remote_filename = remote_filename or local_path_obj.name
            remote_full_path = f"{self.remote_user}@{self.remote_host}:{self.remote_path}/{remote_filename}"
            
            logger.info(f"[SCP] 파일 전송 시작: {local_path} → {remote_full_path}")
            
            cmd = ["scp"]
            if self.ssh_key:
                cmd.extend(["-i", self.ssh_key])
            cmd.extend([str(local_path_obj), remote_full_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                file_size_mb = local_path_obj.stat().st_size / (1024 * 1024)
                logger.info(f"[SCP] 파일 전송 완료: {remote_filename} ({file_size_mb:.2f}MB)")
                return True
            else:
                logger.error(f"[SCP] 파일 전송 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("[SCP] 파일 전송 타임아웃")
            return False
        except Exception as e:
            logger.error(f"[SCP] 파일 전송 중 오류: {e}")
            return False
    
    def receive_file(
        self,
        remote_filename: str,
        local_path: str
    ) -> bool:
        """
        Linux → Colima로 파일 수신
        
        Args:
            remote_filename: 원격 파일명
            local_path: 로컬 저장 경로
            
        Returns:
            성공 여부
        """
        try:
            remote_full_path = f"{self.remote_user}@{self.remote_host}:{self.remote_path}/{remote_filename}"
            
            logger.info(f"[SCP] 파일 수신 시작: {remote_full_path} → {local_path}")
            
            cmd = ["scp"]
            if self.ssh_key:
                cmd.extend(["-i", self.ssh_key])
            cmd.extend([remote_full_path, local_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                local_path_obj = Path(local_path)
                if local_path_obj.exists():
                    file_size_mb = local_path_obj.stat().st_size / (1024 * 1024)
                    logger.info(f"[SCP] 파일 수신 완료: {local_path} ({file_size_mb:.2f}MB)")
                    return True
                else:
                    logger.error("[SCP] 파일 수신 후 확인 실패")
                    return False
            else:
                logger.error(f"[SCP] 파일 수신 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("[SCP] 파일 수신 타임아웃")
            return False
        except Exception as e:
            logger.error(f"[SCP] 파일 수신 중 오류: {e}")
            return False
    
    def send_directory(self, local_dir: str) -> bool:
        """
        Colima → Linux로 디렉토리 전송 (재귀)
        
        Args:
            local_dir: 로컬 디렉토리 경로
            
        Returns:
            성공 여부
        """
        try:
            local_dir_obj = Path(local_dir)
            
            if not local_dir_obj.is_dir():
                logger.error(f"[SCP] 디렉토리 없음: {local_dir}")
                return False
            
            remote_full_path = f"{self.remote_user}@{self.remote_host}:{self.remote_path}"
            
            logger.info(f"[SCP] 디렉토리 전송 시작: {local_dir} → {remote_full_path}")
            
            cmd = ["scp", "-r"]
            if self.ssh_key:
                cmd.extend(["-i", self.ssh_key])
            cmd.extend([str(local_dir_obj), remote_full_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            
            if result.returncode == 0:
                logger.info(f"[SCP] 디렉토리 전송 완료: {local_dir}")
                return True
            else:
                logger.error(f"[SCP] 디렉토리 전송 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("[SCP] 디렉토리 전송 타임아웃")
            return False
        except Exception as e:
            logger.error(f"[SCP] 디렉토리 전송 중 오류: {e}")
            return False


class WorkflowOrchestrator:
    """전체 워크플로우 오케스트레이션"""
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        export_dir: str = "./exports"
    ):
        self.exporter = TrainingDataExporter(ExportConfig(output_dir=export_dir))
        self.importer = ModelImporter(ollama_host)
        self.export_dir = export_dir
    
    async def prepare_fine_tuning(
        self,
        training_samples: List[Dict[str, Any]],
        lora_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fine-tuning 준비 (내보내기)
        
        Returns:
            준비 상태 정보
        """
        logger.info("[Workflow] Fine-tuning 준비 시작")
        
        try:
            # 1. 훈련 데이터 내보내기
            training_data_path = self.exporter.export_training_data(training_samples)
            if not training_data_path:
                raise Exception("훈련 데이터 내보내기 실패")
            
            # 2. LoRA 설정 내보내기
            config_path = self.exporter.export_config(lora_config)
            if not config_path:
                raise Exception("LoRA 설정 내보내기 실패")
            
            # 3. 매니페스트 생성
            manifest = self.exporter.get_export_manifest()
            
            logger.info("[Workflow] Fine-tuning 준비 완료")
            
            return {
                "status": "ready",
                "training_data": str(training_data_path),
                "config": str(config_path),
                "manifest": manifest,
                "total_samples": len(training_samples)
            }
            
        except Exception as e:
            logger.error(f"[Workflow] Fine-tuning 준비 실패: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def complete_fine_tuning(
        self,
        model_path: str,
        model_name: str = "qwen2.5:3b-finetuned"
    ) -> Dict[str, Any]:
        """
        Fine-tuning 완료 (임포트)
        
        Returns:
            완료 상태 정보
        """
        logger.info("[Workflow] Fine-tuning 완료 처리 시작")
        
        try:
            # 1. 모델 임포트
            success = self.importer.import_finetuned_model(model_path, model_name)
            if not success:
                raise Exception("모델 임포트 실패")
            
            # 2. 모델 확인
            verified = self.importer.verify_model(model_name)
            if not verified:
                raise Exception("모델 확인 실패")
            
            # 3. 모델 목록 조회
            models = self.importer.list_models()
            
            logger.info("[Workflow] Fine-tuning 완료 처리 완료")
            
            return {
                "status": "completed",
                "model_name": model_name,
                "verified": verified,
                "available_models": models
            }
            
        except Exception as e:
            logger.error(f"[Workflow] Fine-tuning 완료 처리 실패: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
