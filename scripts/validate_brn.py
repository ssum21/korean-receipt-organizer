#!/usr/bin/env python3
"""한국 사업자등록번호 체크섬 검증."""
import re
import sys


def normalize_brn(brn: str) -> str:
    return re.sub(r'[^\d]', '', brn)


def validate_brn(brn: str) -> bool:
    """사업자등록번호 체크섬 검증."""
    brn = normalize_brn(brn)
    if len(brn) != 10 or not brn.isdigit():
        return False

    weights = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    digits = [int(c) for c in brn]
    checksum = sum(d * w for d, w in zip(digits[:9], weights))
    checksum += (digits[8] * 5) // 10

    expected_last = (10 - (checksum % 10)) % 10
    return expected_last == digits[9]


def format_brn(brn: str) -> str:
    brn = normalize_brn(brn)
    if len(brn) == 10:
        return f"{brn[:3]}-{brn[3:5]}-{brn[5:]}"
    return brn


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_brn.py <사업자번호>")
        sys.exit(1)

    brn = sys.argv[1]
    valid = validate_brn(brn)
    print(f"{format_brn(brn)}: {'✅ 유효' if valid else '❌ 체크섬 오류'}")
    sys.exit(0 if valid else 1)