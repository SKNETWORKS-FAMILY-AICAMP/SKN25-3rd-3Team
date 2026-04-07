import requests
import re
from bs4 import BeautifulSoup

# 💡 [수정 포인트] 개별적으로 .env를 부르지 않고, 중앙 config 파일에서 가져옵니다.
from backend.utils.config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

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
    네이버 블로그 검색 API를 호출합니다. 
    정찰 검색(최신순)과 상세 검색(정확도순) 모두에 공통으로 사용됩니다.
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("⚠️ 네이버 API 키가 설정되지 않아 검색을 건너뜁니다.")
        return []

    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query, 
        "display": display,
        "sort": sort_type 
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        print(f"  [WARN] 네이버 블로그 검색 API 호출 실패: {e}")
        return []

def resolve_blog_url(url: str) -> str:
    """
    검색 API가 주는 모바일/경유 URL을 PC용 실제 블로그 URL로 변환합니다.
    (LLM이 출처로 사용자에게 보여줄 때 깔끔하게 만들기 위함)
    """
    if "blog.naver.com" in url:
        return url
    
    try:
        # 경유 URL(예: https://openapi.naver.com/...)을 따라가서 실제 목적지 도출
        res = requests.get(url, allow_redirects=True, timeout=5)
        final_url = res.url
        
        # 모바일 버전(m.blog.naver.com)이면 PC 버전으로 변경
        if "m.blog.naver.com" in final_url:
            final_url = final_url.replace("m.blog.naver.com", "blog.naver.com")
        return final_url
    except Exception:
        return url

def fetch_blog_body(url: str, max_chars: int = 1500) -> str:
    """
    블로그 본문 HTML을 가져와서 요리 조리법 텍스트만 추출합니다.
    비용 최적화를 위해 max_chars(기본 1500자)만큼만 잘라서 반환합니다.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # 1. iframe을 우회하기 위해 실제 PC URL로 정규화
        pc_url = resolve_blog_url(url)
        
        # blog.naver.com 형식의 URL에서 iframe 내부의 실제 본문 주소를 생성
        if "blog.naver.com/" in pc_url:
            parts = pc_url.split("blog.naver.com/")
            if len(parts) > 1:
                sub_parts = parts[1].split("/")
                if len(sub_parts) == 2:
                    blogger_id, log_no = sub_parts
                else:
                    # blog.naver.com/id?Redirect=Log&logNo=no 패턴 처리
                    import urllib.parse
                    parsed = urllib.parse.urlparse(pc_url)
                    qs = urllib.parse.parse_qs(parsed.query)
                    blogger_id = parts[1].split("?")[0]
                    log_no = qs.get("logNo", [""])[0]
                
                if blogger_id and log_no:
                    # iframe 안쪽의 진짜 본문 URL
                    fetch_url = f"https://blog.naver.com/PostView.naver?blogId={blogger_id}&logNo={log_no}"
        else:
            fetch_url = url

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
            text = soup.get_text(separator="\n")

        # 빈 줄 제거 및 글자수 제한 적용
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)[:max_chars]
        
    except Exception as e:
        print(f"  [WARN] 본문 크롤링 실패 ({url}): {e}")
        return ""