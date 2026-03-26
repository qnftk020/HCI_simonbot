# HCI 논문 챗봇 (Telegram)

HCI 분야 주요 학회/저널 논문을 수집하고 AI로 요약해주는 텔레그램 봇

## 기술 스택
- **Telegram Bot** — python-telegram-bot
- **AI 요약** — Gemini 3.1 Flash Lite Preview
- **DB** — SQLite (논문 메타데이터 + 요약 캐시)
- **백업** — Google Drive (24시간 주기)
- **논문 소스** — DBLP API + Semantic Scholar API

## 데이터 수집 범위

### 수집 대상 (2015-2025, 총 20개 학회/저널)

#### ACM Conferences (9개)
| 학회 | DBLP Key | 설명 |
|------|----------|------|
| CHI | `conf/chi` | ACM Conference on Human Factors in Computing Systems |
| UIST | `conf/uist` | ACM Symposium on User Interface Software and Technology |
| CSCW | `conf/cscw` | ACM Conference on Computer-Supported Cooperative Work |
| UbiComp | `conf/ubicomp` | ACM International Joint Conference on Pervasive and Ubiquitous Computing |
| DIS | `conf/dis` | ACM Conference on Designing Interactive Systems |
| IUI | `conf/iui` | ACM International Conference on Intelligent User Interfaces |
| MobileHCI | `conf/mobilehci` | ACM International Conference on Mobile Human-Computer Interaction |
| ASSETS | `conf/assets` | ACM SIGACCESS Conference on Computers and Accessibility |
| GROUP | `conf/group` | ACM International Conference on Supporting Group Work |

#### ACM/IEEE Conference (1개)
| 학회 | DBLP Key | 설명 |
|------|----------|------|
| HRI | `conf/hri` | ACM/IEEE International Conference on Human-Robot Interaction |

#### IFIP Conference (1개)
| 학회 | DBLP Key | 설명 |
|------|----------|------|
| INTERACT | `conf/interact` | IFIP TC13 International Conference on Human-Computer Interaction |

#### IEEE Conferences (2개)
| 학회 | DBLP Key | 설명 |
|------|----------|------|
| VR | `conf/vr` | IEEE Conference on Virtual Reality and 3D User Interfaces |
| ISMAR | `conf/ismar` | IEEE International Symposium on Mixed and Augmented Reality |

#### ACM Journals (3개)
| 저널 | DBLP Key | 설명 |
|------|----------|------|
| TOCHI | `journals/tochi` | ACM Transactions on Computer-Human Interaction |
| IMWUT | `journals/imwut` | Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies |
| PACM HCI | `journals/pacmhci` | Proceedings of the ACM on Human-Computer Interaction |

#### IEEE Journals (1개)
| 저널 | DBLP Key | 설명 |
|------|----------|------|
| TVCG | `journals/tvcg` | IEEE Transactions on Visualization and Computer Graphics |

#### Other Journals (2개)
| 저널 | DBLP Key | 퍼블리셔 |
|------|----------|----------|
| IwC | `journals/iwc` | Oxford (Interacting with Computers) |
| HCI Journal | `journals/hhci` | Taylor & Francis (Human-Computer Interaction) |

#### DBLP 미지원
| 저널 | 퍼블리셔 | 비고 |
|------|----------|------|
| IJHCS | Elsevier | DBLP에 인덱싱 안 됨 |

### 예상 데이터 규모

| 퍼블리셔 | 학회/저널 수 | 2024년 기준 연간 논문 수 |
|----------|-------------|----------------------|
| ACM | 12개 | ~3,500편 |
| IEEE | 3개 | ~1,600편 |
| ACM/IEEE | 1개 | ~400편 |
| IFIP/Springer | 1개 | ~3,100편 (격년) |
| Oxford | 1개 | ~30편 |
| Taylor & Francis | 1개 | ~20편 |

**2015-2025 전체 예상: ~50,000편 이상**

### 데이터 추출 알고리즘

```
1. [DBLP API] 20개 학회/저널 × 11년(2015-2025) 논문 메타데이터 수집
   - stream: 또는 venue: 필터로 정확한 학회 매칭
   - 제목, 저자, 연도, URL 저장 (DBLP는 초록 미제공)
        ↓
2. [Semantic Scholar API] HCI 키워드 검색으로 추가 논문 수집
   - "human computer interaction", "user interface design" 등
   - 초록 포함 데이터 직접 수집
        ↓
3. [Semantic Scholar API] DBLP 논문의 초록 보완
   - DBLP에서 수집한 논문 중 초록이 없는 것들을
   - 제목으로 Semantic Scholar 검색하여 초록 매칭
        ↓
4. [SQLite DB] 논문 저장 (중복 제거: source_id 기준)
   - venue, publisher, paper_type 태그 포함
        ↓
5. [Gemini API] 사용자 요청 시 초록 → 한국어 요약 생성
   - /random, /random_venue, /random_pub 명령 시 호출
   - 요약 결과는 DB에 캐시하여 재사용
```

## 설치 및 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 TELEGRAM_BOT_TOKEN, GEMINI_API_KEY 입력

# 3. (선택) Google Drive 백업 설정
# Google Cloud Console에서 OAuth 2.0 credentials.json 다운로드
# .env에 GDRIVE_FOLDER_ID 설정

# 4. 실행
python main.py
```

## 봇 명령어

| 명령어 | 설명 |
|--------|------|
| `/start` | 봇 시작 및 안내 |
| `/random` | 무작위 HCI 논문 요약 |
| `/random_venue <학회명>` | 특정 학회/저널 논문 (예: `/random_venue CHI`) |
| `/random_pub <퍼블리셔>` | 퍼블리셔별 논문 (예: `/random_pub ACM`) |
| `/search <키워드>` | 논문 제목/초록 검색 |
| `/venues` | 수록 학회/저널 목록 및 논문 수 |
| `/stats` | DB 통계 (총 논문, 초록 보유율, 퍼블리셔별 분포) |
| `/clear` | 요약 캐시 초기화 |
| `/help` | 도움말 |

## 프로젝트 구조
```
hci-paper-chatbot/
├── main.py            # 엔트리포인트
├── bot.py             # 텔레그램 봇 핸들러
├── database.py        # SQLite CRUD
├── paper_collector.py # DBLP + Semantic Scholar 논문 수집
├── summarizer.py      # Gemini 요약
├── drive_backup.py    # Google Drive 백업
├── config.py          # 설정 (학회 목록, API 키)
└── .env               # 환경변수 (API 키)
```
