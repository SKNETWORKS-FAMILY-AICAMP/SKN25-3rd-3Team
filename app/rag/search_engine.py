import os
import requests
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .env 파일에서 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 로드합니다
load_dotenv()

NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def clean_html(text: str) -> str:
    """
    네이버 API 결과값에 포함된 HTML 태그(<b> 등)를 제거하여 깨끗한 텍스트로 만듭니다.
    """
    if not text:
        return ""
    # 모든 HTML 태그를 제거하고 양끝 공백을 정리합니다
    return re.sub(r"<[^>]+>", "", text).strip()

def search_naver_blogs(query: str, display: int = 5, sort_type: str = "sim") -> list:
    """
    네이버 블로그 검색 API를 호출합니다[cite: 87, 117]. 
    정찰 검색(최신순)과 상세 검색(정확도순) 모두에 공통으로 사용됩니다.
    """
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET
    }
    params = {
        "query": query, 
        "display": display, 
        "sort": sort_type # sim(유사도순) 또는 date(날짜순)
    }
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        res.raise_for_status()
        return res.json().get("items", []) # 검색 결과 리스트 반환
    except Exception as e:
        print(f"[ERROR] 네이버 API 호출 실패: {e}")
        return []

def resolve_blog_url(url: str) -> str:
    """
    네이버 블로그 URL을 실제 포스트 URL로 변환합니다.
    API 반환 link가 리다이렉트 URL인 경우 사람이 읽을 수 있는 형태로 바꿉니다.
    """
    if "blog.naver.com" in url:
        match = re.search(r"blog\.naver\.com/([^/\?]+)/(\d+)", url)
        if match:
            blogger_id, log_no = match.groups()
            return f"https://blog.naver.com/{blogger_id}/{log_no}"
    return url

def fetch_blog_body(url: str, max_chars: int = 2000) -> str:
    """
    제공된 블로그 URL에 접속하여 실제 본문 텍스트를 추출(크롤링)합니다.
    네이버 블로그의 특수한 프레임 구조를 자동으로 처리합니다.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # 네이버 블로그 URL이 프레임 안에 갇혀 있는 경우 실제 포스트 주소로 변환합니다
        fetch_url = url
        if "blog.naver.com" in url:
            match = re.search(r"blog\.naver\.com/([^/\?]+)/(\d+)", url)
            if match:
                blogger_id, log_no = match.groups()
                fetch_url = f"https://blog.naver.com/PostView.naver?blogId={blogger_id}&logNo={log_no}"

        # 본문 데이터 요청
        res = requests.get(fetch_url, timeout=8, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # 네이버 블로그의 스마트에디터 영역(se-main-container) 또는 구버전 영역 탐색
        content_area = soup.find("div", class_="se-main-container") or soup.find("div", id="postViewArea")
        
        if content_area:
            # 스크립트나 스타일 태그는 제거하여 순수 텍스트만 남깁니다
            for tag in content_area(["script", "style"]): 
                tag.decompose()
            text = content_area.get_text(separator="\n")
        else:
            # 특정 영역을 못 찾을 경우 전체 페이지에서 텍스트 추출
            text = soup.get_text(separator="\n")

        # 빈 줄 제거 및 글자수 제한 적용
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)[:max_chars]
        
    except Exception as e:
        print(f"  [WARN] 본문 크롤링 실패 ({url}): {e}")
        return ""

if __name__ == "__main__":
    # 간단한 작동 테스트
    test_query = "이북식 찜닭 레시피"
    print(f"--- '{test_query}' 검색 및 첫 번째 블로그 본문 수집 테스트 ---")
    
    items = search_naver_blogs(test_query, display=1)
    if items:
        blog_url = items[0]['link']
        blog_title = clean_html(items[0]['title'])
        print(f"검색된 블로그 제목: {blog_title}")
        
        body_text = fetch_blog_body(blog_url)
        print(f"\n[본문 내용 일부]\n{body_text[:200]}...")