#!/bin/bash

##############################################################################
# LoRA Fine-tuning 실행 스크립트 (External Linux RTX 3070Ti)
# 
# 사용법:
#   bash run_lora.sh [options]
#
# 옵션:
#   --model_name      허깅페이스 모델 ID (기본값: Qwen/Qwen2.5-3B-Instruct)
#   --training_data   훈련 데이터 경로 (기본값: ./data/training_data.json)
#   --output_dir      출력 디렉토리 (기본값: ./output)
#   --batch_size      배치 크기 (기본값: 8)
#   --epochs          에포크 (기본값: 3)
#   --learning_rate   학습률 (기본값: 1e-4)
##############################################################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 기본값
MODEL_NAME="Qwen/Qwen2.5-3B-Instruct"
TRAINING_DATA="./data/training_data.json"
OUTPUT_DIR="./output"
BATCH_SIZE=8
EPOCHS=3
LEARNING_RATE=1e-4

# 옵션 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --model_name)
            MODEL_NAME="$2"
            shift 2
            ;;
        --training_data)
            TRAINING_DATA="$2"
            shift 2
            ;;
        --output_dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --batch_size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --epochs)
            EPOCHS="$2"
            shift 2
            ;;
        --learning_rate)
            LEARNING_RATE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 함수 정의
print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 시스템 체크
check_system() {
    print_header "시스템 환경 확인"
    
    # Python 버전 확인
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 설치 필요"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python: $python_version"
    
    # CUDA 확인
    if command -v nvidia-smi &> /dev/null; then
        gpu_info=$(nvidia-smi --query-gpu=name --format=csv,noheader)
        gpu_vram=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,unit=GB)
        print_success "GPU: $gpu_info ($gpu_vram)"
    else
        print_warning "GPU/CUDA 미감지 - CPU에서 훈련됩니다"
    fi
    
    # 디렉토리 확인
    if [ ! -f "$TRAINING_DATA" ]; then
        print_error "훈련 데이터 파일 없음: $TRAINING_DATA"
        exit 1
    fi
    print_success "훈련 데이터: $TRAINING_DATA"
    
    # 출력 디렉토리 생성
    mkdir -p "$OUTPUT_DIR"
    print_success "출력 디렉토리: $OUTPUT_DIR"
}

# 환경 설정
setup_environment() {
    print_header "Python 환경 설정"
    
    # 가상환경 확인
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "가상환경 미활성화"
        
        if [ -d "venv" ]; then
            print_warning "venv 디렉토리 발견, 활성화 중..."
            source venv/bin/activate
            print_success "가상환경 활성화됨"
        else
            print_warning "가상환경 생성 중..."
            python3 -m venv venv
            source venv/bin/activate
            print_success "가상환경 생성 및 활성화됨"
        fi
    else
        print_success "가상환경 활성화됨: $VIRTUAL_ENV"
    fi
    
    # 의존성 설치
    print_header "의존성 설치"
    
    pip install --upgrade pip wheel setuptools
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install transformers datasets peft accelerate bitsandbytes
    
    print_success "의존성 설치 완료"
}

# 훈련 실행
run_training() {
    print_header "LoRA Fine-tuning 시작"
    
    echo -e "설정:"
    echo -e "  모델: $MODEL_NAME"
    echo -e "  훈련 데이터: $TRAINING_DATA"
    echo -e "  출력 디렉토리: $OUTPUT_DIR"
    echo -e "  배치 크기: $BATCH_SIZE"
    echo -e "  에포크: $EPOCHS"
    echo -e "  학습률: $LEARNING_RATE"
    echo ""
    
    # 훈련 시작
    start_time=$(date +%s)
    
    python3 lora_trainer.py \
        --model_name "$MODEL_NAME" \
        --training_data "$TRAINING_DATA" \
        --output_dir "$OUTPUT_DIR" \
        --batch_size "$BATCH_SIZE" \
        --epochs "$EPOCHS" \
        --learning_rate "$LEARNING_RATE" \
        --device cuda
    
    train_exit_code=$?
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    minutes=$((duration / 60))
    seconds=$((duration % 60))
    
    if [ $train_exit_code -eq 0 ]; then
        print_success "LoRA Fine-tuning 완료! (소요 시간: ${minutes}m ${seconds}s)"
        return 0
    else
        print_error "LoRA Fine-tuning 실패"
        return 1
    fi
}

# 결과 처리
process_results() {
    print_header "결과 처리"
    
    # 출력 파일 확인
    if [ -f "$OUTPUT_DIR/student-lora/adapter_config.json" ]; then
        print_success "LoRA 어댑터 저장됨: $OUTPUT_DIR/student-lora"
    else
        print_error "LoRA 어댑터를 찾을 수 없음"
        return 1
    fi
    
    # 모델 크기 확인
    if [ -d "$OUTPUT_DIR/student-lora" ]; then
        model_size=$(du -sh "$OUTPUT_DIR/student-lora" | cut -f1)
        print_success "모델 크기: $model_size"
    fi
    
    # 메트릭 확인
    if [ -f "$OUTPUT_DIR/metrics.json" ]; then
        print_success "메트릭 저장됨: $OUTPUT_DIR/metrics.json"
    fi
    
    # 결과 요약
    echo ""
    print_header "훈련 완료 요약"
    echo -e "모델 경로: ${GREEN}$OUTPUT_DIR/student-lora${NC}"
    echo -e "다음 단계:"
    echo -e "  1. 모델을 Colima로 전송: ${YELLOW}scp -r $OUTPUT_DIR/student-lora user@colima:/path/to/imports${NC}"
    echo -e "  2. Colima에서 모델 등록: ${YELLOW}ollama create qwen2.5:3b-finetuned -f Modelfile${NC}"
    echo -e "  3. 프로덕션 배포"
    echo ""
}

# 메인 실행
main() {
    print_header "LoRA Fine-tuning 파이프라인"
    echo -e "시작 시간: $(date)"
    echo ""
    
    # 시스템 확인
    check_system
    echo ""
    
    # 환경 설정
    setup_environment
    echo ""
    
    # 훈련 실행
    if run_training; then
        echo ""
        # 결과 처리
        process_results
        
        print_header "작업 완료"
        echo -e "종료 시간: $(date)"
        return 0
    else
        print_error "훈련 실패"
        return 1
    fi
}

# 실행
main
exit $?
