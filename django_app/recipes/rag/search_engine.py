"""네이버 블로그 검색 + 본문 크롤링.

3차 프로젝트의 backend/rag/search_engine.py에서 import 경로를
backend.utils.config → recipes.utils.config 로 변경했습니다.
"""
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from recipes.utils.config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET


def clean_html(text: str) -> str:
    """네이버 API 결과의 <b> 태그 등을 제거합니다."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def search_naver_blogs(query: str, display: int = 5, sort_type: str = "sim") -> list:
    """네이버 블로그 검색 API 호출."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("⚠️ 네이버 API 키가 설정되지 않아 검색을 건너뜁니다.")
        return []

    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": sort_type}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        print(f"  [WARN] 네이버 블로그 검색 API 호출 실패: {e}")
        return []


def resolve_blog_url(url: str) -> str:
    """모바일/경유 URL → PC 블로그 URL 변환."""
    if "blog.naver.com" in url:
        return url
    try:
        res = requests.get(url, allow_redirects=True, timeout=5)
        final_url = res.url
        if "m.blog.naver.com" in final_url:
            final_url = final_url.replace("m.blog.naver.com", "blog.naver.com")
        return final_url
    except Exception:
        return url


def fetch_blog_body(url: str, max_chars: int = 1500) -> str:
    """블로그 본문 텍스트를 추출합니다."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        pc_url = resolve_blog_url(url)
        fetch_url = url

        if "blog.naver.com/" in pc_url:
            parts = pc_url.split("blog.naver.com/")
            if len(parts) > 1:
                sub_parts = parts[1].split("/")
                if len(sub_parts) == 2:
                    blogger_id, log_no = sub_parts
                else:
                    parsed = urllib.parse.urlparse(pc_url)
                    qs = urllib.parse.parse_qs(parsed.query)
                    blogger_id = parts[1].split("?")[0]
                    log_no = qs.get("logNo", [""])[0]
                if blogger_id and log_no:
                    fetch_url = (
                        f"https://blog.naver.com/PostView.naver?"
                        f"blogId={blogger_id}&logNo={log_no}"
                    )

        res = requests.get(fetch_url, timeout=8, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        content_area = soup.find("div", class_="se-main-container") or soup.find(
            "div", id="postViewArea"
        )

        if content_area:
            for tag in content_area(["script", "style"]):
                tag.decompose()
            text = content_area.get_text(separator="\n")
        else:
            text = soup.get_text(separator="\n")

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)[:max_chars]
    except Exception as e:
        print(f"  [WARN] 본문 크롤링 실패 ({url}): {e}")
        return ""
