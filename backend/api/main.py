# =====================================================================
# [전체 프로젝트에서의 역할]
# 이 파일은 FastAPI를 이용해 RAG 파이프라인을 웹 API 형태로 제공하는 백엔드 서버입니다.
# 프론트엔드(UI)에서 넘겨준 질문과 취향 설정(알레르기, 소스 등)을 받아
# pipeline.py의 RecipeAgent에 전달하고, 그 결과를 다시 프론트엔드로 응답합니다.
# =====================================================================

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# 프로젝트 루트 경로를 sys.path에 추가하여 app 모듈을 찾을 수 있게 함
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(app_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# pipeline.py에서 에이전트를 불러옵니다.
from backend.rag.pipeline import RecipeAgent

# FastAPI 앱 초기화
app = FastAPI(title="냉털봇 API", description="MongoDB Vector Search 기반 냉장고 파먹기 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 에이전트 변수
agent = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 RecipeAgent를 한 번만 초기화하여 메모리에 적재합니다."""
    global agent
    agent = RecipeAgent()

# '소스/양념' 데이터를 받을 수 있도록 모델을 업데이트
class RecipeRequest(BaseModel):
    question: str
    allergies: str = "없음"
    difficulty: str = "초보"
    cooking_time: str = "30분"
    saved_sauces: str = "없음"  # 새로 추가된 소스 정보
    chat_history: Optional[List[dict]] = []

@app.post("/chat")
async def chat_with_agent(request: RecipeRequest):
    """프론트엔드에서 질문을 받아 RAG 에이전트의 답변을 반환합니다."""
    if not agent:
        raise HTTPException(status_code=500, detail="에이전트가 아직 로드되지 않았습니다.")
    
    try:
        # 'saved_sauces' 데이터를 preferences 딕셔너리에 묶어 파이프라인으로 넘겨줍니다.
        preferences = {
            "allergies": request.allergies,
            "difficulty": request.difficulty,
            "cooking_time": request.cooking_time,
            "saved_sauces": request.saved_sauces
        }
        
        # Agent 실행 (pipeline.py의 run 메서드 호출)
        answer = agent.run(
            question=request.question,
            preferences=preferences,
            chat_history=request.chat_history
        )
        return {"answer": answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 서버 실행용 코드 (테스트용)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
