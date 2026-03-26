import time
import logging
import requests
from config import (
    YEAR_START, YEAR_END, MAX_PAPERS_PER_SOURCE,
    HCI_VENUES, SS_QUERIES,
)
from database import insert_paper, get_paper_count

logger = logging.getLogger(__name__)

SS_API = "https://api.semanticscholar.org/graph/v1"
DBLP_API = "https://dblp.org/search/publ/api"


def collect_from_semantic_scholar():
    """Semantic Scholar에서 HCI 논문 수집 (rate limit 고려, 소량씩)"""
    count = 0
    retries = 0
    max_retries = 3

    for query in SS_QUERIES:
        logger.info(f"Semantic Scholar 검색: '{query}'")
        offset = 0
        per_query_limit = MAX_PAPERS_PER_SOURCE // len(SS_QUERIES)

        while offset < per_query_limit:
            try:
                resp = requests.get(
                    f"{SS_API}/paper/search",
                    params={
                        "query": query,
                        "year": f"{YEAR_START}-{YEAR_END}",
                        "fields": "paperId,title,authors,abstract,year,url,externalIds",
                        "limit": 50,
                        "offset": offset,
                    },
                    timeout=30,
                )
                if resp.status_code == 429:
                    retries += 1
                    if retries > max_retries:
                        logger.warning("Semantic Scholar 요청 제한 초과, 다음 쿼리로 이동")
                        break
                    wait = 30 * retries
                    logger.warning(f"Semantic Scholar 요청 제한, {wait}초 대기... ({retries}/{max_retries})")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                retries = 0
            except Exception as e:
                logger.error(f"Semantic Scholar API 오류: {e}")
                break

            papers = data.get("data", [])
            if not papers:
                break

            for p in papers:
                if not p.get("abstract"):
                    continue
                authors = ", ".join(a["name"] for a in (p.get("authors") or [])[:5])
                if len(p.get("authors") or []) > 5:
                    authors += f" 외 {len(p['authors']) - 5}명"

                paper_url = p.get("url") or ""
                if p.get("externalIds", {}).get("DOI"):
                    paper_url = f"https://doi.org/{p['externalIds']['DOI']}"

                insert_paper(
                    source_id=p.get("paperId", ""),
                    title=p["title"],
                    authors=authors,
                    abstract=p["abstract"],
                    published=str(p.get("year", "")),
                    url=paper_url,
                    source="semantic_scholar",
                )
                count += 1

            offset += 50
            time.sleep(5)

    logger.info(f"Semantic Scholar 수집 완료: {count}편")
    return count


def collect_from_dblp():
    """DBLP에서 HCI 주요 학회/저널 논문 수집"""
    count = 0
    for venue_info in HCI_VENUES:
        venue_name = venue_info["name"]
        publisher = venue_info["publisher"]
        paper_type = venue_info["type"]
        query_type = venue_info["query_type"]
        venue_query = venue_info.get("venue_query", venue_name)

        logger.info(f"DBLP 수집: {venue_name} ({publisher}, {paper_type})")

        for year in range(YEAR_START, YEAR_END + 1):
            try:
                if query_type == "stream":
                    q = f"stream:{venue_info['key']}: year:{year}"
                else:
                    q = f"venue:{venue_query} year:{year}"

                resp = requests.get(
                    DBLP_API,
                    params={
                        "q": q,
                        "format": "json",
                        "h": 500,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"DBLP API 오류 ({venue_name} {year}): {e}")
                continue

            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            for hit in hits:
                info = hit.get("info", {})
                title = info.get("title", "")
                if not title:
                    continue

                # authors 처리
                authors_data = info.get("authors", {}).get("author", [])
                if isinstance(authors_data, dict):
                    authors_data = [authors_data]
                authors = ", ".join(
                    a.get("text", a) if isinstance(a, dict) else str(a)
                    for a in authors_data[:5]
                )
                if len(authors_data) > 5:
                    authors += f" 외 {len(authors_data) - 5}명"

                paper_url = info.get("ee", info.get("url", ""))
                if isinstance(paper_url, list):
                    paper_url = paper_url[0] if paper_url else ""

                insert_paper(
                    source_id=f"dblp:{hit.get('@id', '')}",
                    title=title,
                    authors=authors,
                    abstract="",  # DBLP는 초록 미제공
                    published=str(info.get("year", year)),
                    url=paper_url,
                    source="dblp",
                    venue=venue_name,
                    publisher=publisher,
                    paper_type=paper_type,
                )
                count += 1

            time.sleep(1)

    logger.info(f"DBLP 수집 완료: {count}편")
    return count


def enrich_abstracts_from_ss():
    """DBLP에서 수집한 논문의 초록을 Semantic Scholar에서 보완"""
    from database import get_papers_without_abstract

    papers = get_papers_without_abstract(limit=50)
    enriched = 0

    for paper in papers:
        try:
            resp = requests.get(
                f"{SS_API}/paper/search",
                params={
                    "query": paper["title"],
                    "fields": "abstract",
                    "limit": 1,
                },
                timeout=15,
            )
            if resp.status_code == 429:
                time.sleep(60)
                continue
            resp.raise_for_status()
            data = resp.json()
            results = data.get("data", [])
            if results and results[0].get("abstract"):
                from database import update_abstract
                update_abstract(paper["id"], results[0]["abstract"])
                enriched += 1
        except Exception as e:
            logger.error(f"초록 보완 실패 ({paper['title'][:30]}): {e}")

        time.sleep(3)

    logger.info(f"초록 보완 완료: {enriched}편")
    return enriched


def collect_papers():
    """모든 소스에서 논문 수집"""
    logger.info("논문 수집 시작...")
    total = 0
    total += collect_from_dblp()
    total += collect_from_semantic_scholar()

    # DBLP 논문 중 초록이 없는 것들을 Semantic Scholar에서 보완
    enrich_abstracts_from_ss()

    db_total = get_paper_count()
    logger.info(f"전체 수집 완료: 신규 {total}편, DB 총 {db_total}편")
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from database import init_db
    init_db()
    collect_papers()
