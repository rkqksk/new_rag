#!/usr/bin/env python3
"""
LoRA Fine-tuning 스크립트 (External Linux RTX 3070Ti)
Qwen2.5:3B Student 모델 미세조정
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, PeftModel
from datasets import Dataset, load_dataset

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoRATrainer:
    """LoRA Fine-tuning 트레이너"""
    
    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        output_dir: str = "./output",
        device: str = "auto"
    ):
        """
        Args:
            model_name: 허깅페이스 모델 ID
            output_dir: 출력 디렉토리
            device: 디바이스 (cuda, cpu, auto)
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 디바이스 설정
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"[Trainer] 디바이스: {self.device}")
        if self.device == "cuda":
            logger.info(f"[Trainer] GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"[Trainer] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f}GB")
        
        self.model = None
        self.tokenizer = None
        self.trainer = None
    
    def load_training_data(
        self,
        training_data_path: str
    ) -> Dataset:
        """
        훈련 데이터 로드
        
        Args:
            training_data_path: 훈련 데이터 JSON 파일 경로
            
        Returns:
            Dataset: 훈련 데이터셋
        """
        logger.info(f"[Data] 훈련 데이터 로드: {training_data_path}")
        
        with open(training_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 메타데이터와 실제 데이터 분리
        if isinstance(data, dict) and "data" in data:
            samples = data["data"]
            metadata = data.get("metadata", {})
            logger.info(f"[Data] 메타데이터: {metadata}")
        else:
            samples = data
        
        logger.info(f"[Data] 총 {len(samples)} 샘플 로드됨")
        
        # Dataset 변환
        def format_dataset(sample):
            """훈련 포맷으로 변환"""
            return {
                "text": f"{sample['input']}\n{sample['output']}"
            }
        
        formatted_samples = [format_dataset(sample) for sample in samples]
        dataset = Dataset.from_dict({
            "text": [s["text"] for s in formatted_samples]
        })
        
        logger.info(f"[Data] 데이터셋 준비 완료: {len(dataset)} 샘플")
        return dataset
    
    def load_model_and_tokenizer(self):
        """모델과 토크나이저 로드"""
        logger.info(f"[Model] 모델 로드 시작: {self.model_name}")
        
        try:
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                padding_side="right"
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info(f"[Model] 토크나이저 로드 완료")
            
            # 모델 로드
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto",
            )
            
            logger.info(f"[Model] 모델 로드 완료")
            logger.info(f"[Model] 모델 파라미터: {self.model.num_parameters() / 1e9:.2f}B")
            
            return True
            
        except Exception as e:
            logger.error(f"[Model] 모델 로드 실패: {e}")
            return False
    
    def apply_lora(self, lora_config: Optional[Dict[str, Any]] = None):
        """LoRA 설정 적용"""
        logger.info("[LoRA] LoRA 설정 적용 시작")
        
        # 기본 LoRA 설정
        if lora_config is None:
            lora_config = {
                "r": 16,
                "lora_alpha": 32,
                "target_modules": ["q_proj", "v_proj"],
                "lora_dropout": 0.05,
                "bias": "none",
            }
        
        logger.info(f"[LoRA] LoRA 설정: {lora_config}")
        
        config = LoraConfig(
            r=lora_config.get("r", 16),
            lora_alpha=lora_config.get("lora_alpha", 32),
            target_modules=lora_config.get("target_modules", ["q_proj", "v_proj"]),
            lora_dropout=lora_config.get("lora_dropout", 0.05),
            bias=lora_config.get("bias", "none"),
            task_type="CAUSAL_LM"
        )
        
        self.model = get_peft_model(self.model, config)
        
        # 훈련 가능한 파라미터 확인
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        logger.info(f"[LoRA] 훈련 가능한 파라미터: {trainable_params / 1e6:.2f}M / {total_params / 1e9:.2f}B ({100 * trainable_params / total_params:.2f}%)")
        
        self.model.print_trainable_parameters()
    
    def train(
        self,
        dataset: Dataset,
        training_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        모델 훈련
        
        Args:
            dataset: 훈련 데이터셋
            training_config: 훈련 설정
            
        Returns:
            성공 여부
        """
        logger.info("[Train] 훈련 시작")
        
        # 기본 훈련 설정
        if training_config is None:
            training_config = {
                "num_epochs": 3,
                "per_device_train_batch_size": 8,
                "learning_rate": 1e-4,
                "warmup_steps": 100,
                "max_steps": 2000,
                "gradient_accumulation_steps": 2,
            }
        
        logger.info(f"[Train] 훈련 설정: {training_config}")
        
        try:
            # 토크나이제이션
            def tokenize_function(examples):
                return self.tokenizer(
                    examples["text"],
                    max_length=2048,
                    truncation=True,
                    padding="max_length"
                )
            
            tokenized_dataset = dataset.map(
                tokenize_function,
                batched=True,
                num_proc=4,
                remove_columns=["text"]
            )
            
            logger.info(f"[Train] 토크나이제이션 완료: {len(tokenized_dataset)} 샘플")
            
            # 훈련 설정
            training_args = TrainingArguments(
                output_dir=str(self.output_dir),
                num_train_epochs=training_config.get("num_epochs", 3),
                per_device_train_batch_size=training_config.get("per_device_train_batch_size", 8),
                learning_rate=training_config.get("learning_rate", 1e-4),
                warmup_steps=training_config.get("warmup_steps", 100),
                max_steps=training_config.get("max_steps", 2000),
                gradient_accumulation_steps=training_config.get("gradient_accumulation_steps", 2),
                logging_steps=10,
                save_steps=100,
                save_total_limit=3,
                fp16=True,
                remove_unused_columns=False,
            )
            
            # Data Collator
            data_collator = DataCollatorForLanguageModeling(
                self.tokenizer,
                mlm=False
            )
            
            # Trainer 초기화
            self.trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
            )
            
            # 훈련 실행
            logger.info("[Train] 훈련 중...")
            self.trainer.train()
            
            logger.info("[Train] 훈련 완료")
            return True
            
        except Exception as e:
            logger.error(f"[Train] 훈련 실패: {e}")
            return False
    
    def save_finetuned_model(self, output_name: str = "student-lora"):
        """
        미세조정 모델 저장
        
        Args:
            output_name: 출력 모델명
            
        Returns:
            저장 경로
        """
        logger.info(f"[Save] 모델 저장 시작: {output_name}")
        
        try:
            output_path = self.output_dir / output_name
            output_path.mkdir(parents=True, exist_ok=True)
            
            # LoRA 어댑터 저장
            self.model.save_pretrained(str(output_path))
            
            # 토크나이저 저장
            self.tokenizer.save_pretrained(str(output_path))
            
            # 메타데이터 저장
            metadata = {
                "model_name": self.model_name,
                "output_name": output_name,
                "saved_at": datetime.now().isoformat(),
                "device": self.device,
                "training_framework": "peft",
                "lora_status": "adapter_only"
            }
            
            metadata_path = output_path / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[Save] 모델 저장 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"[Save] 모델 저장 실패: {e}")
            return None
    
    def save_metrics(self):
        """훈련 메트릭 저장"""
        if self.trainer is None:
            logger.warning("[Metrics] Trainer가 없음")
            return
        
        try:
            metrics = self.trainer.evaluate()
            
            metrics_path = self.output_dir / "metrics.json"
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[Metrics] 메트릭 저장: {metrics}")
            
        except Exception as e:
            logger.error(f"[Metrics] 메트릭 저장 실패: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="LoRA Fine-tuning 스크립트")
    
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen2.5-3B-Instruct",
        help="허깅페이스 모델 ID"
    )
    parser.add_argument(
        "--training_data",
        type=str,
        default="./data/training_data.json",
        help="훈련 데이터 파일 경로"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./output",
        help="출력 디렉토리"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="배치 크기"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="훈련 에포크"
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=1e-4,
        help="학습률"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="디바이스 (cuda, cpu, auto)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("LoRA Fine-tuning 시작")
    logger.info("=" * 80)
    logger.info(f"Model: {args.model_name}")
    logger.info(f"Training Data: {args.training_data}")
    logger.info(f"Output Dir: {args.output_dir}")
    logger.info("=" * 80)
    
    # 트레이너 초기화
    trainer = LoRATrainer(
        model_name=args.model_name,
        output_dir=args.output_dir,
        device=args.device
    )
    
    # 모델 로드
    if not trainer.load_model_and_tokenizer():
        logger.error("[Main] 모델 로드 실패")
        return 1
    
    # LoRA 적용
    trainer.apply_lora({
        "r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "v_proj"],
        "lora_dropout": 0.05,
        "bias": "none"
    })
    
    # 훈련 데이터 로드
    try:
        dataset = trainer.load_training_data(args.training_data)
    except Exception as e:
        logger.error(f"[Main] 훈련 데이터 로드 실패: {e}")
        return 1
    
    # 훈련
    training_config = {
        "num_epochs": args.epochs,
        "per_device_train_batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "warmup_steps": 100,
        "max_steps": 2000,
        "gradient_accumulation_steps": 2,
    }
    
    if not trainer.train(dataset, training_config):
        logger.error("[Main] 훈련 실패")
        return 1
    
    # 모델 저장
    output_path = trainer.save_finetuned_model("student-lora")
    if output_path is None:
        logger.error("[Main] 모델 저장 실패")
        return 1
    
    # 메트릭 저장
    trainer.save_metrics()
    
    logger.info("=" * 80)
    logger.info("LoRA Fine-tuning 완료!")
    logger.info(f"출력 경로: {output_path}")
    logger.info("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())
