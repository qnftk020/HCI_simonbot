import os
import csv
import json
import shutil
import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)

GDRIVE_BACKUP_DIR = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-qnftk020@gmail.com/My Drive/HCI_Papers_Backup"
)


def backup_to_drive():
    """DB를 Google Drive 동기화 폴더에 복사 (DB + CSV + JSON)"""
    if not os.path.exists(DB_PATH):
        logger.warning("DB 파일이 존재하지 않습니다.")
        return False

    if not os.path.exists(GDRIVE_BACKUP_DIR):
        logger.warning(f"Google Drive 동기화 폴더가 없습니다: {GDRIVE_BACKUP_DIR}")
        return False

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. SQLite DB 복사
        db_dest = os.path.join(GDRIVE_BACKUP_DIR, "hci_papers.db")
        shutil.copy2(DB_PATH, db_dest)

        # 2. CSV 내보내기
        csv_dest = os.path.join(GDRIVE_BACKUP_DIR, "hci_papers.csv")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM papers").fetchall()
        conn.close()

        if rows:
            keys = rows[0].keys()
            with open(csv_dest, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        # 3. JSON 내보내기
        json_dest = os.path.join(GDRIVE_BACKUP_DIR, "hci_papers.json")
        with open(json_dest, "w", encoding="utf-8") as f:
            json.dump([dict(r) for r in rows], f, ensure_ascii=False, indent=2)

        logger.info(f"Google Drive 백업 완료: {len(rows)}편 → {GDRIVE_BACKUP_DIR}")
        return True

    except Exception as e:
        logger.error(f"Google Drive 백업 실패: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    backup_to_drive()
