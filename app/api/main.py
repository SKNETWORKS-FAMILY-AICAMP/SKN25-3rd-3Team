import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# 프로젝트 루트 경로를 sys.path에 추가하여 app 모듈을 찾을 수 있게 함
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(app_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.rag.agent_workflow import RecipeAgent

# FastAPI 앱 초기화
app = FastAPI(title="냉털봇 API", description="RAG 기반 냉장고 파먹기 레시피 추천 API")

# 전역 에이전트 변수
agent = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 RecipeAgent를 한 번만 초기화하여 메모리에 적재합니다."""
    global agent
    print("[API] 🚀 FastAPI 서버 시작: RecipeAgent 초기화를 진행합니다...")
    agent = RecipeAgent()
    print("[API] ✅ RecipeAgent 준비 완료!")

# 클라이언트로부터 받을 데이터 구조 (Pydantic 모델)
class RecipeRequest(BaseModel):
    question: str
    allergies: str = "없음"
    difficulty: str = "초보"
    cooking_time: str = "30분"
    chat_history: Optional[List[dict]] = []

@app.post("/chat")
async def chat_with_agent(request: RecipeRequest):
    """프론트엔드에서 질문을 받아 RAG 에이전트의 답변을 반환합니다."""
    if not agent:
        raise HTTPException(status_code=500, detail="에이전트가 아직 로드되지 않았습니다.")
    
    try:
        preferences = {
            "allergies": request.allergies,
            "difficulty": request.difficulty,
            "cooking_time": request.cooking_time
        }
        
        # 터미널에 요청 로그 출력
        print(f"\n[API Request] 질문: {request.question} | 설정: {preferences}")
        
        # Agent 실행
        answer = agent.run(
            question=request.question,
            preferences=preferences,
            chat_history=request.chat_history
        )
        return {"answer": answer}
        
    except Exception as e:
        print(f"[API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 서버 실행용 코드 (테스트용)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)