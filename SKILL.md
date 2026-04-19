---
name: korean-receipt-organizer
description: >
  한국의 영수증·세금계산서·현금영수증·카드영수증을 Upstage Document Parse와
  Solar Pro 3로 자동 처리합니다. 이미지/PDF 더미를 읽어 공급가액·부가세·
  사업자등록번호·거래처명을 구조화된 JSON으로 추출하고, 증빙 유형별로
  분류한 뒤 표준 파일명으로 리네임하여 카테고리 폴더에 정리합니다.
  홈택스 호환 CSV도 함께 생성합니다.
  "영수증 정리", "세금계산서 엑셀", "경비 처리", "지출 증빙 분류",
  "홈택스 업로드", "연말정산 영수증", "사업자번호 검증", "간이영수증",
  "현금영수증 정리", "receipt organize", "한국 세무 자동화",
  "부가세 계산" 등의 요청에 사용합니다.
allowed-tools: Bash(python *), Read, Write
---

# 한국 영수증·세금계산서 정리 도구

한국 세무 양식에 특화된 영수증 자동 처리 Skill입니다.

## 사전 조건

- `UPSTAGE_API_KEY` 환경변수 설정 (https://console.upstage.ai)
- Python 3.10+, `openai`, `requests` 패키지

## 실행 흐름

### 1. 폴더 스캔

사용자가 영수증 폴더를 지정하면:
1. 폴더 내 지원 포맷(.pdf, .jpg, .jpeg, .png) 파일 수 확인
2. 예상 처리 시간 안내
3. 사용자에게 분류 기준 질문:
   - 증빙 유형별 / 월별 / 카테고리별 / 거래처별

### 2. 일괄 처리

`scripts/batch_process.py <폴더> --strategy <전략>` 실행.
배치당 1초 딜레이로 rate limit 방어.

### 3. 결과 요약

- 총 처리 건수, 성공/실패/수동확인
- 총 공급가액, 총 부가세, 세액공제 가능 금액
- 수동 확인 필요 파일 목록

## 출력 파일명 규칙

`YYYY-MM-DD_거래처명_증빙유형_공급가액.확장자`

예시:
- `2026-04-15_스타벅스_카드영수증_12000.jpg`
- `2026-03-10_AWS_세금계산서_250000.pdf`

## Gotchas

- Document Parse는 50MB/파일 제한
- HEIC는 `pillow-heif`로 JPG 변환 후 처리
- 사업자번호 체크섬 불일치 시 OCR 오류 가능성
- 간이영수증은 부가세 공제 불가 — 별도 표시
- 원본 파일은 절대 삭제하지 말 것
- 개인정보 보호: 주민번호는 로그에 남기지 않음

## 참조

- 한국 세무 JSON 스키마: `references/korean_tax_schema.md`
- 파싱 결과 예시: `examples/sample_output.json`