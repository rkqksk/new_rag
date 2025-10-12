from fastapi import FastAPI, Request
from pydantic import BaseModel
import subprocess

app = FastAPI()

class QARequest(BaseModel):
    question: str
    topk: int = 3

@app.get("/")
def status():
    return {"status": "OK", "message": "API 서버 정상"}

@app.post("/run_pipeline/")
async def run_pipeline(data: QARequest):
    # 예시: 외부에서 질문·topk 받아 파이프라인 실행 (실제 파라미터/연동 필요에 맞게 수정!)
    print(f"[파이프라인 실행 요청] 질문:{data.question}, topk:{data.topk}")
    # 예: 검색/QA 단계 실제 코드/스크립트 연동
    cmd_search = f"python3 agents/search_agent.py"
    cmd_qa = f"python3 agents/qa_agent.py"
    subprocess.run(cmd_search, shell=True)
    subprocess.run(cmd_qa, shell=True)
    # 결과는 실제 구현에 맞춰 반환
    return {"result": "질문과 topk에 맞춰 워크플로 실행됨(예시)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
