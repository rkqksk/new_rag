import os
import shutil
import json

def clean_folders(config_path):
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    for folder in config["clean_targets"]:
        if os.path.exists(folder):
            print(f"[삭제] {folder}")
            shutil.rmtree(folder)
    for folder in config["backup_targets"]:
        if os.path.exists(folder):
            backup_folder = folder + "_backup"
            print(f"[백업] {folder} → {backup_folder}")
            if os.path.exists(backup_folder):
                shutil.rmtree(backup_folder)
            shutil.copytree(folder, backup_folder)
    print("[정리/백업 완료]")

if __name__ == "__main__":
    config_fn = input("config 파일 (예: agents/clean_deploy_config.json): ").strip()
    clean_folders(config_fn)
