import os
import time
import json
import requests

def send_slack(message, webhook_url):
    try:
        payload = {"text": message}
        resp = requests.post(webhook_url, json=payload)
        if resp.status_code == 200:
            print("[슬랙 알림 전송됨]")
        else:
            print(f"[슬랙 전송 오류] status: {resp.status_code}, resp: {resp.text}")
    except Exception as e:
        print(f"[슬랙 알림 오류]: {e}")

def monitor_log(log_file, config_path):
    with open(config_path, encoding="utf-8") as f: config = json.load(f)
    webhook_url = config["slack_webhook_url"]
    check_interval = config.get("check_interval", 30)
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
                    send_slack(f"[RAG 시스템 오류 발생]\n{new_logs}", webhook_url)
                last_size = size
        time.sleep(check_interval)

if __name__ == "__main__":
    log_path = input("모니터링 로그 경로: ").strip()
    config_fn = input("config 파일 (예: agents/monitoring_config_slack.json): ").strip()
    monitor_log(log_path, config_fn)
