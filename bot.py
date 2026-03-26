import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from database import (
    get_random_paper_without_summary, get_random_paper_by_venue,
    get_random_paper_by_publisher, search_papers, get_paper_count,
    get_stats, get_venues, clear_summaries,
)
from summarizer import summarize_paper
from config import TELEGRAM_BOT_TOKEN, YEAR_START, YEAR_END

logger = logging.getLogger(__name__)


def escape_md(text: str) -> str:
    """Telegram Markdown V1 특수문자 이스케이프"""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


async def safe_reply(message, text, reply_markup=None):
    """Markdown 전송 시도, 실패하면 plain text로 fallback"""
    try:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception:
        await message.reply_text(text.replace("*", "").replace("_", ""), reply_markup=reply_markup)


async def safe_edit(query, text, reply_markup=None):
    """Markdown 편집 시도, 실패하면 plain text로 fallback"""
    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception:
        await query.edit_message_text(text.replace("*", "").replace("_", ""), reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = get_paper_count()
    await update.message.reply_text(
        f"🤖 HCI 논문 챗봇에 오신 걸 환영합니다!\n\n"
        f"현재 DB에 {total}편의 HCI 논문이 있습니다.\n\n"
        f"📚 명령어:\n"
        f"/random - 무작위 논문 요약 받기\n"
        f"/random_venue <학회명> - 특정 학회 논문\n"
        f"/random_pub <퍼블리셔> - 퍼블리셔별 논문\n"
        f"/search <키워드> - 논문 검색\n"
        f"/venues - 수록 학회/저널 목록\n"
        f"/stats - 통계 보기\n"
        f"/help - 도움말"
    )


async def random_paper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """무작위 논문을 선택하고 Gemini로 요약"""
    paper = get_random_paper_without_summary()
    if not paper:
        await update.message.reply_text("DB에 논문이 없습니다. 잠시 후 다시 시도해주세요.")
        return

    await update.message.reply_text("🔍 논문을 요약하고 있습니다... 잠시만 기다려주세요.")

    if paper.get("summary"):
        summary = paper["summary"]
    else:
        summary = await summarize_paper(paper)

    text = format_paper_message(paper, summary)
    keyboard = [[InlineKeyboardButton("🎲 다른 논문 보기", callback_data="random")]]
    await safe_reply(update.message, text, reply_markup=InlineKeyboardMarkup(keyboard))


async def random_by_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/random_venue <학회명> - 특정 학회의 무작위 논문"""
    if not context.args:
        venues = get_venues()
        venue_list = "\n".join(f"  - {v['venue']} ({v['cnt']}편)" for v in venues[:20])
        await update.message.reply_text(
            f"사용법: /random_venue <학회명>\n\n"
            f"사용 가능한 학회/저널:\n{venue_list}"
        )
        return

    venue = " ".join(context.args).upper()
    # 대소문자 무시 매칭
    venues = get_venues()
    matched = None
    for v in venues:
        if v["venue"].upper() == venue:
            matched = v["venue"]
            break

    if not matched:
        venue_list = ", ".join(v["venue"] for v in venues)
        await update.message.reply_text(f"'{venue}'을 찾을 수 없습니다.\n\n사용 가능: {venue_list}")
        return

    paper = get_random_paper_by_venue(matched)
    if not paper:
        await update.message.reply_text(f"{matched}에 초록이 있는 논문이 없습니다.")
        return

    await update.message.reply_text("🔍 논문을 요약하고 있습니다... 잠시만 기다려주세요.")

    if paper.get("summary"):
        summary = paper["summary"]
    else:
        summary = await summarize_paper(paper)

    text = format_paper_message(paper, summary)
    keyboard = [[InlineKeyboardButton(f"🎲 다른 {matched} 논문", callback_data=f"venue:{matched}")]]
    await safe_reply(update.message, text, reply_markup=InlineKeyboardMarkup(keyboard))


async def random_by_publisher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/random_pub <퍼블리셔> - 퍼블리셔별 무작위 논문"""
    if not context.args:
        stats = get_stats()
        pub_list = "\n".join(f"  - {k}: {v}편" for k, v in stats["by_publisher"].items())
        await update.message.reply_text(
            f"사용법: /random_pub <퍼블리셔>\n\n"
            f"사용 가능한 퍼블리셔:\n{pub_list}"
        )
        return

    pub_input = " ".join(context.args).upper()
    stats = get_stats()
    matched = None
    for k in stats["by_publisher"]:
        if k.upper() == pub_input:
            matched = k
            break

    if not matched:
        pub_list = ", ".join(stats["by_publisher"].keys())
        await update.message.reply_text(f"'{pub_input}'을 찾을 수 없습니다.\n\n사용 가능: {pub_list}")
        return

    paper = get_random_paper_by_publisher(matched)
    if not paper:
        await update.message.reply_text(f"{matched} 논문 중 초록이 있는 것이 없습니다.")
        return

    await update.message.reply_text("🔍 논문을 요약하고 있습니다... 잠시만 기다려주세요.")

    if paper.get("summary"):
        summary = paper["summary"]
    else:
        summary = await summarize_paper(paper)

    text = format_paper_message(paper, summary)
    keyboard = [[InlineKeyboardButton(f"🎲 다른 {matched} 논문", callback_data=f"pub:{matched}")]]
    await safe_reply(update.message, text, reply_markup=InlineKeyboardMarkup(keyboard))


async def venues_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/venues - 수록 학회/저널 목록"""
    venues = get_venues()
    if not venues:
        await update.message.reply_text("아직 수집된 학회/저널 데이터가 없습니다.")
        return

    conf_lines = []
    journal_lines = []
    for v in venues:
        line = f"  [{v['publisher']}] {v['venue']}: {v['cnt']}편"
        if v["paper_type"] == "journal":
            journal_lines.append(line)
        else:
            conf_lines.append(line)

    text = f"📚 수록 학회/저널 목록 ({YEAR_START}-{YEAR_END})\n\n"
    if conf_lines:
        text += "🎤 학회 (Conference):\n" + "\n".join(conf_lines) + "\n\n"
    if journal_lines:
        text += "📖 저널 (Journal):\n" + "\n".join(journal_lines) + "\n"

    total = sum(v["cnt"] for v in venues)
    text += f"\n총 {total}편"

    await update.message.reply_text(text)


def format_paper_message(paper: dict, summary: str) -> str:
    """논문 메시지 포맷팅"""
    title = escape_md(paper['title'])
    authors = escape_md(paper['authors'])
    url = paper.get('url', '')
    venue = paper.get('venue', '')
    publisher = paper.get('publisher', '')

    venue_info = ""
    if venue:
        venue_info = f"🏛 {venue}"
        if publisher:
            venue_info += f" ({publisher})"
        venue_info += "\n"

    text = (
        f"📄 *{title}*\n\n"
        f"👤 {authors}\n"
        f"📅 {paper['published']}\n"
        f"{venue_info}\n"
        f"---\n\n"
        f"{summary}\n\n"
    )
    if url:
        text += f"🔗 [논문 원문]({url})"

    return text


async def random_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """인라인 버튼으로 다른 논문 요청"""
    query = update.callback_query
    await query.answer()

    data = query.data
    paper = None

    if data == "random":
        paper = get_random_paper_without_summary()
    elif data.startswith("venue:"):
        venue = data[6:]
        paper = get_random_paper_by_venue(venue)
    elif data.startswith("pub:"):
        pub = data[4:]
        paper = get_random_paper_by_publisher(pub)

    if not paper:
        await query.edit_message_text("논문을 찾을 수 없습니다.")
        return

    await query.edit_message_text("🔍 논문을 요약하고 있습니다... 잠시만 기다려주세요.")

    if paper.get("summary"):
        summary = paper["summary"]
    else:
        summary = await summarize_paper(paper)

    text = format_paper_message(paper, summary)

    # 콜백 데이터에 따라 버튼 텍스트 변경
    if data == "random":
        btn_text = "🎲 다른 논문 보기"
    elif data.startswith("venue:"):
        btn_text = f"🎲 다른 {data[6:]} 논문"
    elif data.startswith("pub:"):
        btn_text = f"🎲 다른 {data[4:]} 논문"
    else:
        btn_text = "🎲 다른 논문 보기"

    keyboard = [[InlineKeyboardButton(btn_text, callback_data=data)]]
    await safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """키워드로 논문 검색"""
    if not context.args:
        await update.message.reply_text("사용법: /search <키워드>\n예: /search gesture recognition")
        return

    keyword = " ".join(context.args)
    papers = search_papers(keyword)

    if not papers:
        await update.message.reply_text(f"'{keyword}'에 해당하는 논문을 찾지 못했습니다.")
        return

    text = f"🔍 '{keyword}' 검색 결과 ({len(papers)}건):\n\n"
    for i, p in enumerate(papers, 1):
        title = escape_md(p['title'])
        url = p.get('url', '')
        venue = p.get('venue', '')
        venue_tag = f" | {venue}" if venue else ""
        if url:
            text += f"{i}. *{title}*\n   📅 {p['published']}{venue_tag} | [링크]({url})\n\n"
        else:
            text += f"{i}. *{title}*\n   📅 {p['published']}{venue_tag}\n\n"

    await safe_reply(update.message, text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DB 통계"""
    s = get_stats()
    source_lines = "\n".join(f"  - {k}: {v}편" for k, v in s["by_source"].items())
    pub_lines = "\n".join(f"  - {k}: {v}편" for k, v in s["by_publisher"].items()) if s["by_publisher"] else "  (데이터 없음)"
    venue_top = list(s["by_venue"].items())[:10]
    venue_lines = "\n".join(f"  - {k}: {v}편" for k, v in venue_top) if venue_top else "  (데이터 없음)"

    await update.message.reply_text(
        f"📊 HCI 논문 DB 통계\n\n"
        f"총 논문 수: {s['total']}편\n"
        f"초록 보유: {s['with_abstract']}편\n"
        f"요약 완료: {s['with_summary']}편\n"
        f"수집 범위: {YEAR_START}-{YEAR_END}년\n\n"
        f"출처별:\n{source_lines}\n\n"
        f"퍼블리셔별:\n{pub_lines}\n\n"
        f"학회/저널 (상위 10):\n{venue_lines}"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 HCI 논문 챗봇 도움말\n\n"
        "/start - 봇 시작\n"
        "/random - 무작위 HCI 논문 요약\n"
        "/random_venue <학회명> - 특정 학회 논문 (예: /random_venue CHI)\n"
        "/random_pub <퍼블리셔> - 퍼블리셔별 논문 (예: /random_pub ACM)\n"
        "/search <키워드> - 논문 제목/초록 검색\n"
        "/venues - 수록 학회/저널 목록 보기\n"
        "/stats - DB 통계 보기\n"
        "/clear - 요약 캐시 초기화\n"
        "/help - 이 도움말\n\n"
        "💡 논문 요약은 Gemini-3.1-flash-lite-preview가 생성합니다."
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """요약 캐시만 초기화"""
    count = clear_summaries()
    await update.message.reply_text(f"🧹 요약 캐시 초기화 완료! ({count}건 삭제)\n논문 데이터는 유지됩니다.")


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "명령어를 사용해주세요! /help 로 사용법을 확인하세요."
    )


def create_bot_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("random", random_paper))
    app.add_handler(CommandHandler("random_venue", random_by_venue))
    app.add_handler(CommandHandler("random_pub", random_by_publisher))
    app.add_handler(CommandHandler("venues", venues_command))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(random_callback, pattern="^(random|venue:|pub:)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    return app
