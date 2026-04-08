import os
import schedule
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv


os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

def crawl_and_save_to_mongo():
    print(f"⏰ [작업 시작] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 크롤러 일꾼 출근!")
    
    # 1. 지금 이 파일(recipe_final_timer.py)이 있는 방 (etl 폴더)
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    # 2. 한 칸 밖으로 나가기 (backend 폴더)
    backend_dir = os.path.dirname(current_dir)               
    # 3. 두 칸 밖으로 나가기 (최상단 SKN25-3rd-3Team 폴더)
    project_root = os.path.dirname(backend_dir)               
    
    # 최상단 폴더에 있는 .env 메모장 찾아서 읽기!
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)

    # 몽고DB 주소와 OpenAI 열쇠 꺼내기
    client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=10000)
    ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        db = client['recipe_project'] 
        col = db['recipes']
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        total_checked, page = 0, 1
        print("🚀 [심부름 시작] 100개 훑기 시작!")

        while total_checked < 100:
            res = requests.get(f"https://www.10000recipe.com/recipe/list.html?order=date&page={page}", headers=headers, timeout=15)
            items = BeautifulSoup(res.text, 'html.parser').select('.common_sp_list_li')
            if not items: break

            for item in items:
                if total_checked >= 100: break
                total_checked += 1
                
                link_tag = item.select_one('.common_sp_link')
                title_tag = item.select_one('.common_sp_caption_tit')
                if not link_tag or not title_tag: continue
                
                detail_link = "https://www.10000recipe.com" + link_tag['href']
                title = title_tag.get_text(strip=True)

                # 몽고DB 장부에 이미 있는 레시피인지 확인 (중복 검사)
                if col.find_one({"$or": [{"url": detail_link}, {"title": title}]}):
                    print(f"⏭️ [{total_checked}/100] 중복! 통과~")
                    continue

                try:
                    detail_res = requests.get(detail_link, headers=headers, timeout=15)
                    d_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    ingre_box = d_soup.select_one('.ready_ingre3')
                    if not ingre_box: continue

                    ingre_list = [li.get_text(strip=True).split()[0] for li in ingre_box.select('li')]
                    steps_list = [s.get_text(strip=True) for s in d_soup.select('.view_step_cont')]
                    ingredients_text = ingre_box.get_text(strip=True, separator=', ')

                    # 인공지능한테 재료 글씨를 숫자로 바꿔달라고 하기 (임베딩)
                    res_embed = ai_client.embeddings.create(input=ingredients_text, model="text-embedding-3-small", dimensions=256)
                    
                    # 몽고DB 장부에 새 레시피 적어넣기!
                    col.insert_one({
                        "url": detail_link, "title": title, "ingredients": ingre_list,
                        "steps": steps_list, "ingredients_text": ingredients_text,
                        "ingredients_embedding": res_embed.data[0].embedding,
                        "crawled_at": datetime.now()
                    })
                    print(f"✅ [{total_checked}/100] '{title}' 저장 완료!")
                    time.sleep(0.5) # 인터넷 사이트가 힘들지 않게 0.5초 쉬기
                except Exception as e:
                    print(f"❌ 에러 발생: {e}")
            page += 1
    finally:
        client.close()
        print("🔒 오늘 할 일 끝! 일꾼은 다음 알람까지 쉽니다.")

# --- ⏰ 여기서 알람을 맞춰요! ---
# 지금 바로 테스트로 한 번 켜보고 싶다면 아래 줄 맨 앞의 '#'을 지워주세요!
# crawl_and_save_to_mongo() 

# 매일 밤 12시(00:00)에 알아서 실행하도록 예약!
schedule.every().day.at("00:00").do(crawl_and_save_to_mongo)

print("⏰ 알람 시계가 켜졌습니다. (검은 창을 끄지 말고 그대로 두세요!)")

while True:
    schedule.run_pending() # 지금 알람 울릴 시간인지 확인하기
    time.sleep(60) # 1분마다 눈 떠서 시계 보고 다시 자기