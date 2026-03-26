import logging
import threading
from database import init_db, get_paper_count
from paper_collector import collect_from_dblp, collect_from_semantic_scholar, enrich_abstracts_from_ss
from drive_backup import backup_to_drive
from bot import create_bot_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def background_ss_collect():
    try:
        collect_from_semantic_scholar()
        enrich_abstracts_from_ss()
        logger.info(f"백그라운드 수집 완료, DB 총 {get_paper_count()}편")
    except Exception as e:
        logger.error(f"백그라운드 수집 오류: {e}")


def periodic_backup():
    import time
    while True:
        time.sleep(86400)
        try:
            backup_to_drive()
        except Exception as e:
            logger.error(f"백업 오류: {e}")


def background_dblp_collect():
    try:
        collect_from_dblp()
        logger.info(f"DBLP 수집 완료, DB 총 {get_paper_count()}편")
        collect_from_semantic_scholar()
        enrich_abstracts_from_ss()
        logger.info(f"전체 수집 완료, DB 총 {get_paper_count()}편")
    except Exception as e:
        logger.error(f"수집 오류: {e}")


def main():
    logger.info("DB 초기화...")
    init_db()

    # 모든 수집을 백그라운드로 — 봇 즉시 시작
    logger.info("논문 수집을 백그라운드에서 시작...")
    threading.Thread(target=background_dblp_collect, daemon=True).start()
    threading.Thread(target=periodic_backup, daemon=True).start()

    logger.info(f"텔레그램 봇 시작! (DB: {get_paper_count()}편)")
    app = create_bot_app()
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
