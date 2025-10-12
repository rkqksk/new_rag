import requests
import os
import json
import time

class MonitoringAgent:
    def __init__(self, webhook_url=None, check_interval=30):
        self.webhook_url = webhook_url
        self.check_interval = check_interval

    def send_slack(self, message):
        if not self.webhook_url:
            print("[슬랙 웹훅 URL 미설정]")
            return
        try:
            payload = {"text": message}
            resp = requests.post(self.webhook_url, json=payload)
            if resp.status_code == 200:
                print("[슬랙 알림 전송됨]")
            else:
                print(f"[슬랙 전송 오류] status: {resp.status_code}, resp: {resp.text}")
        except Exception as e:
            print(f"[슬랙 알림 오류]: {e}")

    async def record_success(self, document):
        msg = f"[RAG 성공] 문서 ID: {getattr(document, 'id', document)}"
        print(msg)
        self.send_slack(msg)

    async def record_error(self, document, error):
        msg = f"[RAG 오류] 문서 ID: {getattr(document, 'id', document)} | {error}"
        print(msg)
        self.send_slack(msg)

    async def record_failure(self, document):
        msg = f"[RAG 최종 실패] 문서 ID: {getattr(document, 'id', document)}"
        print(msg)
        self.send_slack(msg)

    def monitor_log(self, log_file):
        last_size = 0
        print(f"모니터링 시작: {log_file} (슬랙 연동)")
        while True:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                if size > last_size:
                    with open(log_file, encoding="utf-8") as f:
                        f.seek(last_size)
                        new_logs = f.read()
                    if "ERROR" in new_logs or "오류" in new_logs:
                        self.send_slack(f"[RAG 시스템 오류 발생]\n{new_logs}")
                    last_size = size
            time.sleep(self.check_interval)


