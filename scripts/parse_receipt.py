#!/usr/bin/env python3
"""단일 영수증 파싱 → 구조화된 JSON."""
import sys
import os
import json
import requests

sys.path.insert(0, os.path.dirname(__file__))
from _common import get_api_key, get_solar_client
from validate_brn import validate_brn

UPSTAGE_KEY = get_api_key()


def extract_text(file_path: str) -> str:
    with open(file_path, "rb") as f:
        resp = requests.post(
            "https://api.upstage.ai/v1/document-digitization",
            headers={"Authorization": f"Bearer {UPSTAGE_KEY}"},
            files={"document": f},
            data={"model": "document-parse", "output_formats": '["text"]'},
        )
    resp.raise_for_status()
    result = resp.json()
    return result.get("content", {}).get("text", "")


RECEIPT_SCHEMA = {
    "doc_type": "세금계산서 | 간이영수증 | 카드영수증 | 현금영수증 | 기타",
    "date": "YYYY-MM-DD",
    "vendor_name": "공급자 상호",
    "vendor_brn": "공급자 사업자번호 (XXX-XX-XXXXX, 없으면 null)",
    "buyer_name": "공급받는자 상호 (없으면 null)",
    "buyer_brn": "공급받는자 사업자번호 (없으면 null)",
    "supply_amount": "공급가액 (정수)",
    "vat_amount": "부가세 (정수, 간이영수증은 0)",
    "total_amount": "합계 (정수)",
    "items": [{"name": "품목", "quantity": "수량", "unit_price": "단가", "amount": "금액"}],
    "payment_method": "현금 | 카드 | 계좌이체 | 기타",
    "category": "식비 | 교통비 | 소프트웨어 | 사무용품 | 통신비 | 교육비 | 공과금 | 기타",
    "category_confidence": "0.0~1.0",
}


def structure_with_solar(text: str) -> dict:
    client = get_solar_client()
    system_prompt = f"""당신은 한국 세무 문서 분석 전문가입니다.
영수증 OCR 텍스트를 아래 JSON 스키마에 맞게 구조화하세요.

스키마:
{json.dumps(RECEIPT_SCHEMA, ensure_ascii=False, indent=2)}

규칙:
- 찾을 수 없는 필드는 null
- 금액은 정수로 (쉼표 제거)
- 날짜는 YYYY-MM-DD로 정규화 (2026.03.15, 2026년 3월 15일 → 2026-03-15)
- 사업자번호는 XXX-XX-XXXXX 형식
- JSON만 출력, 마크다운/설명 금지
"""

    resp = client.chat.completions.create(
        model="solar-pro3",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw = resp.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"JSON 파싱 실패: {e}", "_raw": raw}


def post_process(data: dict, source_file: str) -> dict:
    flags = []
    for brn_field in ["vendor_brn", "buyer_brn"]:
        brn = data.get(brn_field)
        if brn and not validate_brn(brn):
            flags.append(f"{brn_field} 체크섬 오류: {brn}")

    supply = data.get("supply_amount") or 0
    vat = data.get("vat_amount") or 0
    total = data.get("total_amount") or 0
    if supply and total and abs(supply + vat - total) > 10:
        flags.append(f"합계 불일치: {supply}+{vat}≠{total}")

    if data.get("doc_type") == "세금계산서" and vat == 0 and supply > 0:
        flags.append("세금계산서인데 부가세=0")

    data["_source_file"] = os.path.basename(source_file)
    data["_validation_flags"] = flags
    data["_needs_review"] = len(flags) > 0
    return data


def parse_receipt(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {"_error": f"파일 없음: {file_path}"}

    text = extract_text(file_path)
    if not text.strip():
        return {"_error": "OCR 결과 비어있음", "_source_file": os.path.basename(file_path)}

    data = structure_with_solar(text)
    if "_error" in data:
        data["_source_file"] = os.path.basename(file_path)
        return data

    return post_process(data, file_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_receipt.py <파일경로>", file=sys.stderr)
        sys.exit(1)

    result = parse_receipt(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))