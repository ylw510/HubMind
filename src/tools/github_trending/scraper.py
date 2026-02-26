"""
GitHub Trending 抓取模块：请求 https://github.com/trending 页面并解析为结构化数据。

流程：GitHub Trending 页面 (HTML) -> 本模块 (请求 + 解析) -> List[Dict]
"""
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://github.com"
TRENDING_PATH = "/trending"


def build_trending_url(
    language: Optional[str] = None,
    since: str = "daily",
    spoken_language_code: Optional[str] = None,
) -> str:
    """构建 trending 页面 URL。language 为编程语言（如 python），since 为 daily/weekly/monthly。"""
    path = TRENDING_PATH
    if language:
        # 语言在 path 中，如 /trending/python
        path = f"{TRENDING_PATH}/{language}"
    params = {"since": since}
    if spoken_language_code:
        params["spoken_language_code"] = spoken_language_code
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_URL}{path}?{qs}" if qs else f"{BASE_URL}{path}"


def fetch_trending_html(url: str, timeout: int = 15) -> str:
    """请求 GitHub trending 页面，返回 HTML 字符串。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _text(elem) -> str:
    if elem is None:
        return ""
    return (elem.get_text() or "").strip()


def _parse_one_repo(article) -> Optional[Dict]:
    """从单个 article.Box-row 解析出一个 repo 字典。"""
    try:
        # 仓库名与链接：h2.h3 > a (href="/owner/name")
        h2 = article.select_one("h2.h3")
        if not h2:
            h2 = article.select_one("h2")
        if not h2:
            return None
        a = h2.find("a", href=True)
        if not a or not a["href"].strip().startswith("/"):
            return None
        href = a["href"].strip().lstrip("/")
        if "/" not in href or href.count("/") != 1:
            return None
        full_name = href
        url = urljoin(BASE_URL, a["href"])

        # 描述
        desc_elem = article.select_one("p")
        description = _text(desc_elem) if desc_elem else ""

        # 语言、stars、forks、stars today 等（通常在 div 下的 span 或 a 里）
        language = ""
        stars = 0
        forks = 0
        stars_today = None

        # 常见结构：span[itemprop="programmingLanguage"] 或 data-ga-click 等
        lang_span = article.select_one('span[itemprop="programmingLanguage"]')
        if lang_span:
            language = _text(lang_span)

        # 链接中有 stargazers / network / members
        for link in article.select("a[href]"):
            h = link.get("href") or ""
            t = _text(link)
            if "stargazers" in h:
                # 可能带 k 如 1.2k
                num = re.sub(r"[^\d.]", "", t) or "0"
                try:
                    if "k" in t.lower():
                        stars = int(float(num.replace("k", "").strip()) * 1000)
                    else:
                        stars = int(float(num))
                except ValueError:
                    pass
            elif "network" in h or "forks" in h:
                num = re.sub(r"[^\d.]", "", t) or "0"
                try:
                    if "k" in t.lower():
                        forks = int(float(num.replace("k", "").strip()) * 1000)
                    else:
                        forks = int(float(num))
                except ValueError:
                    pass

        # stars today：部分页面有 "X stars today"
        for span in article.select("span"):
            txt = _text(span)
            if "stars today" in txt.lower() or "today" in txt.lower():
                m = re.search(r"([\d,.]+\s*k?)\s*stars?\s*today", txt, re.I)
                if m:
                    num = re.sub(r"[^\d.]", "", m.group(1)) or "0"
                    try:
                        if "k" in (m.group(1) or "").lower():
                            stars_today = int(float(num) * 1000)
                        else:
                            stars_today = int(float(num))
                    except ValueError:
                        pass
                break

        return {
            "name": full_name,
            "description": description,
            "stars": stars,
            "forks": forks,
            "language": language or None,
            "url": url,
            "stars_today": stars_today,
            "owner": full_name.split("/")[0] if "/" in full_name else "",
        }
    except Exception:
        return None


def parse_trending_page(html: str, limit: int = 25) -> List[Dict]:
    """
    解析 trending 页面 HTML，返回仓库列表。
    GitHub 使用 article.Box-row 包裹每个仓库；若结构变化则返回空列表。
    """
    repos = []
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    for article in soup.select("article.Box-row"):
        if len(repos) >= limit:
            break
        item = _parse_one_repo(article)
        if item:
            repos.append(item)

    return repos


def get_trending_from_page(
    language: Optional[str] = None,
    since: str = "daily",
    limit: int = 25,
    timeout: int = 15,
) -> List[Dict]:
    """
    从 GitHub Trending 页面抓取并解析，返回结构化列表。
    若请求或解析失败返回空列表。
    """
    url = build_trending_url(language=language, since=since)
    try:
        html = fetch_trending_html(url, timeout=timeout)
        return parse_trending_page(html, limit=limit)
    except Exception:
        return []
