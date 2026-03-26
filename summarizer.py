import google.generativeai as genai
import logging
from config import GEMINI_API_KEY, GEMINI_MODEL
from database import update_summary

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

SUMMARY_PROMPT = """다음 HCI(Human-Computer Interaction) 논문의 제목과 초록을 읽고 한국어로 간결하게 요약해주세요.

요약 형식:
1. 📌 핵심 주제 (1줄)
2. 🔬 연구 방법 (1-2줄)
3. 💡 주요 발견/기여 (2-3줄)
4. 🏷️ 키워드 (3-5개)

논문 제목: {title}

초록:
{abstract}
"""


async def summarize_paper(paper: dict) -> str:
    """Gemini를 사용하여 논문을 요약"""
    try:
        prompt = SUMMARY_PROMPT.format(title=paper["title"], abstract=paper["abstract"])
        response = await model.generate_content_async(prompt)
        summary = response.text

        update_summary(paper["id"], summary)
        return summary

    except Exception as e:
        logger.error(f"요약 실패 (ID: {paper.get('id')}): {e}")
        return f"요약 생성 중 오류가 발생했습니다: {e}"
