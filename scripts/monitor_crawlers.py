#!/usr/bin/env python3
"""
크롤러 모니터링 스크립트
- Freemold & Onehago 크롤러 상태 추적
- 자동 재시작 및 문제 감지
- 진행 상황 실시간 보고
"""
import time
import json
import psutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/crawler_monitor.log'),
        logging.StreamHandler()
    ]
)

class CrawlerMonitor:
    def __init__(self):
        # Freemold 설정
        self.freemold_pid = None
        self.freemold_progress_file = Path('data/freemold/crawled_v2/crawl_progress_selenium.json')
        self.freemold_log = Path('/tmp/freemold_agent_unbuffered.log')
        self.freemold_script = '.agent/freemold_crawler/crawler.py'
        self.freemold_total = 15510

        # Onehago 설정
        self.onehago_pid = None
        self.onehago_progress_file = Path('data/onehago/crawled/crawl_progress.json')
        self.onehago_log = Path('/tmp/onehago_full_crawl.log')
        self.onehago_script = 'scripts/crawl_onehago_complete.py'
        self.onehago_total = 20442

        # 모니터링 상태
        self.last_freemold_count = 0
        self.last_onehago_count = 0
        self.last_check_time = datetime.now()

        # 임계값 설정
        self.stall_threshold = 600  # 10분간 진행 없으면 경고
        self.restart_threshold = 1800  # 30분간 진행 없으면 재시작

    def find_crawler_pid(self, script_name):
        """크롤러 프로세스 찾기"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any(script_name in arg for arg in cmdline):
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logging.error(f"PID 검색 오류: {e}")
        return None

    def check_process_alive(self, pid):
        """프로세스 생존 확인"""
        if not pid:
            return False
        try:
            proc = psutil.Process(pid)
            return proc.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def get_progress(self, progress_file):
        """진행 상황 파일 읽기"""
        try:
            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'completed' in data:
                        return len(data['completed'])
                    elif isinstance(data, list):
                        return len(data)
            return 0
        except Exception as e:
            logging.error(f"진행 상황 읽기 오류 ({progress_file}): {e}")
            return 0

    def check_log_health(self, log_file, pattern=None):
        """로그 파일 건강 상태 확인"""
        if not log_file.exists():
            return "로그 파일 없음"

        try:
            # 최근 100줄 읽기
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-100:]

            # None 패턴 검사 (Onehago 문제)
            none_count = sum(1 for line in lines if '] None' in line)
            if none_count > 10:
                return f"⚠️ None 반환 과다 ({none_count}개)"

            # 에러 패턴 검사
            error_count = sum(1 for line in lines if 'Error' in line or '❌' in line)
            if error_count > 5:
                return f"⚠️ 에러 과다 ({error_count}개)"

            # 정상 진행 확인
            if any('✓' in line or 'pIdx=' in line for line in lines[-10:]):
                return "✅ 정상"

            return "⚠️ 활동 없음"

        except Exception as e:
            logging.error(f"로그 분석 오류: {e}")
            return "로그 분석 실패"

    def restart_crawler(self, crawler_name):
        """크롤러 재시작"""
        logging.warning(f"🔄 {crawler_name} 크롤러 재시작 시도...")

        try:
            if crawler_name == "Freemold":
                # 기존 프로세스 종료
                if self.freemold_pid and self.check_process_alive(self.freemold_pid):
                    subprocess.run(['kill', str(self.freemold_pid)])
                    time.sleep(5)

                # 재시작
                cmd = f"python3 -u {self.freemold_script} 2>&1 | tee {self.freemold_log} &"
                subprocess.Popen(cmd, shell=True)
                time.sleep(10)

                # 새 PID 찾기
                self.freemold_pid = self.find_crawler_pid('freemold_crawler')
                logging.info(f"✅ Freemold 재시작 완료 (새 PID: {self.freemold_pid})")

            elif crawler_name == "Onehago":
                # 기존 프로세스 종료
                if self.onehago_pid and self.check_process_alive(self.onehago_pid):
                    subprocess.run(['kill', str(self.onehago_pid)])
                    time.sleep(5)

                # 재시작
                cmd = f"python3 -u {self.onehago_script} --details 2>&1 | tee {self.onehago_log} &"
                subprocess.Popen(cmd, shell=True)
                time.sleep(10)

                # 새 PID 찾기
                self.onehago_pid = self.find_crawler_pid('crawl_onehago_complete')
                logging.info(f"✅ Onehago 재시작 완료 (새 PID: {self.onehago_pid})")

        except Exception as e:
            logging.error(f"❌ {crawler_name} 재시작 실패: {e}")

    def check_crawler_status(self, name, pid, progress_file, log_file, total, last_count):
        """개별 크롤러 상태 확인"""
        status = {
            'name': name,
            'alive': False,
            'pid': pid,
            'progress': 0,
            'percentage': 0.0,
            'health': '알 수 없음',
            'needs_restart': False
        }

        # 프로세스 생존 확인
        status['alive'] = self.check_process_alive(pid)

        # 진행 상황 확인
        current_count = self.get_progress(progress_file)
        status['progress'] = current_count
        status['percentage'] = (current_count / total * 100) if total > 0 else 0

        # 로그 건강 상태
        status['health'] = self.check_log_health(log_file)

        # 정체 여부 확인
        time_elapsed = (datetime.now() - self.last_check_time).total_seconds()
        progress_made = current_count - last_count

        if not status['alive']:
            status['needs_restart'] = True
            status['health'] = "❌ 프로세스 종료됨"
        elif progress_made == 0 and time_elapsed > self.restart_threshold:
            status['needs_restart'] = True
            status['health'] = f"❌ {int(time_elapsed/60)}분간 진행 없음"
        elif progress_made == 0 and time_elapsed > self.stall_threshold:
            status['health'] = f"⚠️ {int(time_elapsed/60)}분간 진행 없음"

        return status, current_count

    def print_status_report(self, freemold_status, onehago_status):
        """상태 보고서 출력"""
        print("\n" + "="*70)
        print(f"📊 크롤러 모니터링 보고 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # Freemold 상태
        print(f"\n🏭 Freemold 크롤러:")
        print(f"   프로세스: {'✅ 실행 중' if freemold_status['alive'] else '❌ 중지됨'} (PID: {freemold_status['pid']})")
        print(f"   진행: {freemold_status['progress']:,} / {self.freemold_total:,} ({freemold_status['percentage']:.1f}%)")
        print(f"   상태: {freemold_status['health']}")

        # Onehago 상태
        print(f"\n🏪 Onehago 크롤러:")
        print(f"   프로세스: {'✅ 실행 중' if onehago_status['alive'] else '❌ 중지됨'} (PID: {onehago_status['pid']})")
        print(f"   진행: {onehago_status['progress']:,} / {self.onehago_total:,} ({onehago_status['percentage']:.1f}%)")
        print(f"   상태: {onehago_status['health']}")

        # 전체 진행률
        total_progress = freemold_status['progress'] + onehago_status['progress']
        total_target = self.freemold_total + self.onehago_total
        overall_pct = (total_progress / total_target * 100) if total_target > 0 else 0

        print(f"\n📈 전체 진행:")
        print(f"   {total_progress:,} / {total_target:,} ({overall_pct:.1f}%)")

        # 예상 완료 시간 계산
        if freemold_status['progress'] > 0:
            freemold_remaining = self.freemold_total - freemold_status['progress']
            print(f"\n⏱️  Freemold 남은 제품: {freemold_remaining:,}개 (약 {freemold_remaining * 6 / 3600:.1f}시간)")

        if onehago_status['progress'] > 0:
            onehago_remaining = self.onehago_total - onehago_status['progress']
            print(f"   Onehago 남은 제품: {onehago_remaining:,}개 (약 {onehago_remaining * 8 / 3600:.1f}시간)")

        print("="*70)

    def monitor_loop(self, check_interval=300):
        """메인 모니터링 루프"""
        logging.info("🚀 크롤러 모니터링 시작...")

        # 초기 PID 찾기
        self.freemold_pid = self.find_crawler_pid('freemold_crawler')
        self.onehago_pid = self.find_crawler_pid('crawl_onehago_complete')

        logging.info(f"Freemold PID: {self.freemold_pid}")
        logging.info(f"Onehago PID: {self.onehago_pid}")

        while True:
            try:
                # Freemold 상태 확인
                freemold_status, freemold_count = self.check_crawler_status(
                    "Freemold",
                    self.freemold_pid,
                    self.freemold_progress_file,
                    self.freemold_log,
                    self.freemold_total,
                    self.last_freemold_count
                )

                # Onehago 상태 확인
                onehago_status, onehago_count = self.check_crawler_status(
                    "Onehago",
                    self.onehago_pid,
                    self.onehago_progress_file,
                    self.onehago_log,
                    self.onehago_total,
                    self.last_onehago_count
                )

                # 상태 보고서 출력
                self.print_status_report(freemold_status, onehago_status)

                # 재시작 필요 여부 확인
                if freemold_status['needs_restart']:
                    self.restart_crawler("Freemold")
                    self.last_freemold_count = 0  # 재시작 후 카운트 리셋
                else:
                    self.last_freemold_count = freemold_count

                if onehago_status['needs_restart']:
                    self.restart_crawler("Onehago")
                    self.last_onehago_count = 0  # 재시작 후 카운트 리셋
                else:
                    self.last_onehago_count = onehago_count

                # 완료 여부 확인
                if (freemold_status['progress'] >= self.freemold_total and
                    onehago_status['progress'] >= self.onehago_total):
                    logging.info("🎉 모든 크롤러 완료!")
                    print("\n🎉 모든 크롤링 작업이 완료되었습니다!")
                    break

                # 업데이트 시간 갱신
                self.last_check_time = datetime.now()

                # 대기
                logging.info(f"💤 {check_interval}초 대기 중...")
                time.sleep(check_interval)

            except KeyboardInterrupt:
                logging.info("⏸️  사용자가 모니터링을 중지했습니다.")
                break
            except Exception as e:
                logging.error(f"❌ 모니터링 오류: {e}")
                time.sleep(60)  # 오류 시 1분 대기

def main():
    import argparse

    parser = argparse.ArgumentParser(description='크롤러 모니터링 및 자동 관리')
    parser.add_argument('--interval', type=int, default=300, help='체크 간격 (초, 기본값: 300)')
    args = parser.parse_args()

    monitor = CrawlerMonitor()
    monitor.monitor_loop(check_interval=args.interval)

if __name__ == "__main__":
    main()
