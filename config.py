import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "hci_papers.db")

# Paper collection settings
YEAR_START = 2015
YEAR_END = 2025
MAX_PAPERS_PER_SOURCE = 250

# HCI 학회/저널 목록 (DBLP 기반)
# query_type: "stream" = stream:key: 필터, "venue" = venue:name 필터
HCI_VENUES = [
    # === ACM Conferences ===
    {"key": "conf/chi",       "name": "CHI",       "publisher": "ACM", "type": "conf", "query_type": "stream"},
    {"key": "conf/uist",      "name": "UIST",      "publisher": "ACM", "type": "conf", "query_type": "stream"},
    {"key": "conf/cscw",      "name": "CSCW",      "publisher": "ACM", "type": "conf", "query_type": "stream"},
    {"key": "conf/ubicomp",   "name": "UbiComp",   "publisher": "ACM", "type": "conf", "query_type": "venue"},
    {"key": "conf/dis",       "name": "DIS",       "publisher": "ACM", "type": "conf", "query_type": "stream"},
    {"key": "conf/iui",       "name": "IUI",       "publisher": "ACM", "type": "conf", "query_type": "stream"},
    {"key": "conf/mobilehci", "name": "MobileHCI", "publisher": "ACM", "type": "conf", "query_type": "venue"},
    {"key": "conf/assets",    "name": "ASSETS",    "publisher": "ACM", "type": "conf", "query_type": "stream"},
    {"key": "conf/group",     "name": "GROUP",     "publisher": "ACM", "type": "conf", "query_type": "venue"},

    # === ACM/IEEE Conference ===
    {"key": "conf/hri",       "name": "HRI",       "publisher": "ACM/IEEE", "type": "conf", "query_type": "stream"},

    # === IFIP Conference ===
    {"key": "conf/interact",  "name": "INTERACT",  "publisher": "IFIP/Springer", "type": "conf", "query_type": "venue"},

    # === IEEE Conferences ===
    {"key": "conf/vr",        "name": "VR",        "publisher": "IEEE", "type": "conf", "query_type": "venue"},
    {"key": "conf/ismar",     "name": "ISMAR",     "publisher": "IEEE", "type": "conf", "query_type": "venue"},

    # === ACM Journals ===
    {"key": "journals/tochi",   "name": "TOCHI",    "publisher": "ACM", "type": "journal", "query_type": "venue",
     "venue_query": "ACM Trans. Comput.-Hum. Interact."},
    {"key": "journals/imwut",   "name": "IMWUT",    "publisher": "ACM", "type": "journal", "query_type": "stream"},
    {"key": "journals/pacmhci", "name": "PACM HCI", "publisher": "ACM", "type": "journal", "query_type": "stream"},

    # === IEEE Journals ===
    {"key": "journals/tvcg",    "name": "TVCG",     "publisher": "IEEE", "type": "journal", "query_type": "stream"},

    # === Other Journals ===
    {"key": "journals/iwc",  "name": "IwC",          "publisher": "Oxford", "type": "journal", "query_type": "stream"},
    {"key": "journals/hhci", "name": "HCI Journal",  "publisher": "Taylor & Francis", "type": "journal", "query_type": "stream"},
]

# Semantic Scholar 검색 키워드
SS_QUERIES = [
    "human computer interaction",
    "user interface design",
    "usability study",
    "interactive systems",
]

# Google Drive Backup
GDRIVE_CREDENTIALS_PATH = os.getenv("GDRIVE_CREDENTIALS_PATH", "credentials.json")
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")
BACKUP_INTERVAL_HOURS = 24
