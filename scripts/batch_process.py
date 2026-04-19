#!/usr/bin/env python3
"""영수증 폴더 일괄 처리."""
import sys
import os
import json
import time
import csv
import shutil
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _common import sanitize_filename
from parse_receipt import parse_receipt

SUPPORTED = {".pdf", ".jpg", ".jpeg", ".png"}


def determine_destination(data, strategy, output_root):
    date_str = data.get("date") or "날짜미상"
    if strategy == "by_doctype":
        folder = data.get("doc_type") or "기타"
    elif strategy == "by_month":
        folder = date_str[:7] if len(date_str) >= 7 else "날짜미상"
    elif strategy == "by_category":
        conf = data.get("category_confidence") or 0
        folder = data.get("category") or "기타" if conf >= 0.7 else "기타"
    elif strategy == "by_vendor":
        folder = sanitize_filename(data.get("vendor_name") or "거래처미상")
    else:
        folder = "미분류"
    return output_root / folder


def build_filename(data, ext):
    date = data.get("date") or "날짜미상"
    vendor = sanitize_filename(data.get("vendor_name") or "거래처미상")
    doc_type = sanitize_filename(data.get("doc_type") or "기타")
    amount = data.get("total_amount") or 0
    return f"{date}_{vendor}_{doc_type}_{amount}{ext}"


def export_csv(records, path):
    fieldnames = ["거래일자", "증빙유형", "공급자상호", "공급자사업자번호",
                  "공급가액", "부가세", "합계", "경비카테고리", "결제수단",
                  "파일경로", "검증플래그"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "거래일자": r.get("date") or "",
                "증빙유형": r.get("doc_type") or "",
                "공급자상호": r.get("vendor_name") or "",
                "공급자사업자번호": r.get("vendor_brn") or "",
                "공급가액": r.get("supply_amount") or 0,
                "부가세": r.get("vat_amount") or 0,
                "합계": r.get("total_amount") or 0,
                "경비카테고리": r.get("category") or "",
                "결제수단": r.get("payment_method") or "",
                "파일경로": r.get("_new_path") or "",
                "검증플래그": "; ".join(r.get("_validation_flags") or []),
            })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_folder")
    parser.add_argument("--output", default="./organized_receipts")
    parser.add_argument("--strategy", default="by_category",
                        choices=["by_doctype", "by_month", "by_category", "by_vendor"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    review_folder = output_root / "_수동확인필요"
    review_folder.mkdir(exist_ok=True)

    files = sorted(p for p in input_folder.iterdir()
                   if p.is_file() and p.suffix.lower() in SUPPORTED)
    print(f"📂 {len(files)}개 파일 발견", file=sys.stderr)

    records = []
    for i, fpath in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {fpath.name}", file=sys.stderr)
        data = parse_receipt(str(fpath))

        if "_error" in data:
            dest = review_folder / fpath.name
            if not args.dry_run:
                shutil.copy2(fpath, dest)
            data["_new_path"] = str(dest)
            records.append(data)
            time.sleep(1)
            continue

        dest_folder = review_folder if data.get("_needs_review") else determine_destination(data, args.strategy, output_root)
        dest_folder.mkdir(parents=True, exist_ok=True)
        dest_path = dest_folder / build_filename(data, fpath.suffix.lower())

        counter = 2
        while dest_path.exists():
            dest_path = dest_folder / f"{dest_path.stem}_{counter}{dest_path.suffix}"
            counter += 1

        if not args.dry_run:
            shutil.copy2(fpath, dest_path)
        data["_new_path"] = str(dest_path)
        records.append(data)
        time.sleep(1)

    if not args.dry_run:
        export_csv(records, output_root / "summary.csv")
        with (output_root / "full_log.json").open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    success = sum(1 for r in records if "_error" not in r and not r.get("_needs_review"))
    review = sum(1 for r in records if r.get("_needs_review"))
    failed = sum(1 for r in records if "_error" in r)
    total_supply = sum(r.get("supply_amount") or 0 for r in records if "_error" not in r)
    total_vat = sum(r.get("vat_amount") or 0 for r in records if "_error" not in r)

    print(f"\n{'='*50}")
    print(f"✅ 성공: {success}건")
    print(f"⚠️  수동확인: {review}건")
    print(f"❌ 실패: {failed}건")
    print(f"💰 총 공급가액: {total_supply:,}원")
    print(f"💰 총 부가세: {total_vat:,}원")


if __name__ == "__main__":
    main()