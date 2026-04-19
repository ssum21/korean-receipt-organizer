# korean-receipt-organizer

한국 영수증·세금계산서를 Upstage API로 자동 정리하는 Claude Skill.

## 주요 기능

- 📸 **OCR**: Upstage Document Parse로 한국어 영수증 텍스트 추출
- 🔍 **구조화**: Solar Pro 3로 공급가액·부가세·사업자번호 JSON 추출
- ✅ **검증**: 사업자등록번호 체크섬 자동 검증
- 📂 **분류**: 증빙 유형/월별/카테고리별 폴더 자동 정리
- 📊 **CSV 출력**: 홈택스 호환 요약 CSV 생성

## 설치

```bash
# 1. Skill 저장소 클론
git clone https://github.com/본인아이디/korean-receipt-organizer.git ~/.claude/skills/korean-receipt-organizer

# 2. Python 패키지 설치
pip install openai requests

# 3. API 키 설정 (https://console.upstage.ai)
export UPSTAGE_API_KEY="up_xxxxxxxxxx"
```

## 사용법

### Claude Code에서
input 폴더의 영수증을 카테고리별로 정리해줘

### 직접 스크립트 실행
```bash
python scripts/batch_process.py ./receipts --output ./organized --strategy by_category
```

## 분류 전략

| 전략 | 결과 폴더 |
|---|---|
| `by_category` | 식비/교통비/소프트웨어/... |
| `by_month` | 2026-01/2026-02/... |
| `by_doctype` | 세금계산서/간이영수증/카드영수증/현금영수증 |
| `by_vendor` | 거래처명별 |

## 지원 포맷

PDF, JPG, JPEG, PNG

## 라이선스

MIT License
