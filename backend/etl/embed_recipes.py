# =====================================================================
# [전체 프로젝트에서의 역할]
# 이 파일은 MongoDB에 적재된 레시피 데이터의 'ingredients' 필드를 읽어와
# OpenAI API를 통해 256차원 벡터 임베딩으로 변환한 뒤, 다시 DB에 저장하는 배치 스크립트입니다.
# 새로운 레시피 데이터가 추가되었을 때 관리자가 터미널에서 1회성으로 실행하거나 
# 주기적으로 실행하여 AI의 검색 능력을 업데이트하는 역할을 합니다.
# =====================================================================

import time
from pymongo import UpdateOne
from backend.utils.config import open_client
from backend.db.mongo_db import recipe_collection

# 🚨 Atlas 무료 티어(512MB) 보호를 위한 최대 허용 용량(MB)
MAX_SAFE_STORAGE_MB = 480
BATCH_SIZE = 1000
EMBEDDING_MODEL = "text-embedding-3-small"
DIMENSIONS = 256

def check_db_storage(db):
    """현재 데이터베이스의 실제 차지 용량(MB)을 확인합니다."""
    stats = db.command("dbstats")
    storage_mb = stats.get("storageSize", 0) / (1024 * 1024)
    return storage_mb

def run_embedding_job():
    db = recipe_collection.database
    
    print(f"🚀 {DIMENSIONS}차원 압축 임베딩 작업을 시작합니다!")
    print(f"방어 모드 가동: DB 용량이 {MAX_SAFE_STORAGE_MB}MB를 넘으면 자동 정지됩니다.\n")

    # 임베딩이 안 된 데이터만 가져오기 (이미 처리된 데이터 스킵)
    cursor = recipe_collection.find(
        {
            "ingredients": {"$exists": True}, 
            "ingredients_text": {"$exists": False} # 👈 임베딩 여부와 상관없이 이 필드가 없는 모든 문서 탐색
        },
        {"ingredients": 1, "_id": 1}
    )

    current_batch_texts = []
    current_batch_ids = []
    processed_count = 0

    for doc in cursor:
        # 1. 텍스트 전처리 (' 구매' 등 불필요한 단어 제거)
        raw = doc.get("ingredients", [])
        cleaned = ", ".join([item.replace(" 구매", "").strip() for item in raw if item.strip()])
        
        # 전처리 후 내용이 없으면 건너뜁니다.
        if not cleaned: 
            continue
            
        current_batch_texts.append(cleaned)
        current_batch_ids.append(doc["_id"])
        
        # 2. 지정된 배치 사이즈(1000)에 도달하면 API 호출 및 DB 업데이트
        if len(current_batch_texts) >= BATCH_SIZE:
            current_storage = check_db_storage(db)
            if current_storage >= MAX_SAFE_STORAGE_MB:
                print(f"\n🛑 [긴급 정지] 현재 용량이 {current_storage:.2f}MB에 도달했습니다!")
                print("DB가 터지는 것을 막기 위해 작업을 안전하게 중단합니다.")
                return # 루프와 함수 전체 종료
                
            try:
                # OpenAI API 호출 (반드시 dimensions 파라미터 포함)
                response = open_client.embeddings.create(
                    input=current_batch_texts, 
                    model=EMBEDDING_MODEL,
                    dimensions=DIMENSIONS 
                )
                
                # MongoDB Bulk Update 쿼리 생성
                ops = [
                    UpdateOne(
                        {"_id": _id}, 
                        {"$set": {
                            "ingredients_embedding": data.embedding,
                            "ingredients_text": text  # 👈 검색용 문자열 필드 추가!
                        }}
                    )
                    for _id, data, text in zip(current_batch_ids, response.data, current_batch_texts)
                ]
                
                # 한 번에 DB에 쏴주기
                recipe_collection.bulk_write(ops)
                processed_count += len(ops)
                
                print(f"✅ {processed_count}개 처리 완료... (현재 DB 용량: {current_storage:.2f}MB)")
                
                # 바구니 초기화 및 API Rate Limit 방지용 휴식
                current_batch_texts, current_batch_ids = [], []
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"\n❌ 작업 중 에러 발생: {e}")
                return # 에러 시 무리하게 진행하지 않고 즉시 종료

    # 3. 마지막 남은 잔여 데이터(1000개 미만) 처리
    if current_batch_texts and check_db_storage(db) < MAX_SAFE_STORAGE_MB:
        try:
            response = open_client.embeddings.create(
                input=current_batch_texts, 
                model=EMBEDDING_MODEL,
                dimensions=DIMENSIONS
            )
            ops = [
                UpdateOne({"_id": _id}, {"$set": {"ingredients_embedding": data.embedding}})
                for _id, data in zip(current_batch_ids, response.data)
            ]
            recipe_collection.bulk_write(ops)
            processed_count += len(ops)
            print(f"🎉 최종 {processed_count}개 처리 완료! 남은 데이터까지 싹 비웠습니다.")
        except Exception as e:
            print(f"마지막 데이터 처리 중 에러: {e}")
    elif current_batch_texts:
        print("마지막 데이터가 남았지만, 용량 초과 위험으로 처리를 생략했습니다.")

    print("\n--- 모든 임베딩 작업이 종료되었습니다 ---")

if __name__ == "__main__":
    run_embedding_job()