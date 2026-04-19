#!/usr/bin/env python3
"""한국 영수증 정리 Skill 공통 유틸리티."""
import os
import sys
import re


def get_api_key() -> str:
    """UPSTAGE_API_KEY를 환경변수에서 가져옵니다."""
    key = os.environ.get("UPSTAGE_API_KEY")
    if not key:
        print("Error: UPSTAGE_API_KEY 환경변수를 설정하세요", file=sys.stderr)
        print("  https://console.upstage.ai 에서 발급받을 수 있습니다", file=sys.stderr)
        sys.exit(1)
    return key


def get_solar_client():
    """Upstage Solar LLM OpenAI 호환 클라이언트."""
    from openai import OpenAI
    return OpenAI(
        api_key=get_api_key(),
        base_url="https://api.upstage.ai/v1",
    )


def sanitize_filename(s: str) -> str:
    """파일명 불가 문자 제거."""
    s = re.sub(r'[<>:"/\\|?*\n\r\t]', '', s)
    s = re.sub(r'\s+', '_', s)
    return s.strip('_')[:80]