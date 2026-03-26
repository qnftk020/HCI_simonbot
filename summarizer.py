import google.generativeai as genai
import logging
from config import GEMINI_API_KEY, GEMINI_MODEL
from database import update_summary

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

SUMMARY_WITH_ABSTRACT = """다음 HCI(Human-Computer Interaction) 논문의 제목과 초록을 읽고 한국어로 간결하게 요약해주세요.

요약 형식:
1. 📌 핵심 주제 (1줄)
2. 🔬 연구 방법 (1-2줄)
3. 💡 주요 발견/기여 (2-3줄)
4. 🏷️ 키워드 (해시태그 형식, 3-5개)

논문 제목: {title}
저자: {authors}
학회/저널: {venue} ({publisher})
연도: {published}

초록:
{abstract}
"""

SUMMARY_WITHOUT_ABSTRACT = """다음 HCI(Human-Computer Interaction) 논문의 정보를 바탕으로, 이 논문이 어떤 연구인지 한국어로 추론하여 요약해주세요.
초록이 없으므로 제목, 저자, 학회, 연도 정보를 기반으로 최대한 정확하게 추론해주세요.
만약 해당 논문에 대해 알고 있다면 그 지식을 활용해주세요.

요약 형식:
1. 📌 핵심 주제 (1줄)
2. 🔬 추정 연구 방법 (1-2줄)
3. 💡 예상 기여/의의 (2-3줄)
4. 🏷️ 키워드 (해시태그 형식, 3-5개)

⚠️ 초록 없이 제목 기반 추론이므로 실제 내용과 다를 수 있다는 점을 마지막에 한 줄로 안내해주세요.

논문 제목: {title}
저자: {authors}
학회/저널: {venue} ({publisher})
연도: {published}
"""


async def summarize_paper(paper: dict) -> str:
    """Gemini를 사용하여 논문을 요약"""
    try:
        has_abstract = bool(paper.get("abstract", "").strip())

        if has_abstract:
            prompt = SUMMARY_WITH_ABSTRACT.format(
                title=paper["title"],
                authors=paper.get("authors", "N/A"),
                venue=paper.get("venue", "N/A"),
                publisher=paper.get("publisher", "N/A"),
                published=paper.get("published", "N/A"),
                abstract=paper["abstract"],
            )
        else:
            prompt = SUMMARY_WITHOUT_ABSTRACT.format(
                title=paper["title"],
                authors=paper.get("authors", "N/A"),
                venue=paper.get("venue", "N/A"),
                publisher=paper.get("publisher", "N/A"),
                published=paper.get("published", "N/A"),
            )

        response = await model.generate_content_async(prompt)
        summary = response.text

        update_summary(paper["id"], summary)
        return summary

    except Exception as e:
        logger.error(f"요약 실패 (ID: {paper.get('id')}): {e}")
        return f"요약 생성 중 오류가 발생했습니다: {e}"
