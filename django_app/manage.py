#!/usr/bin/env python
"""Django의 명령줄 유틸리티(manage.py).

runserver, migrate, makemigrations 등 Django 관리 명령을 실행합니다.
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nangteol.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django를 import하지 못했습니다. 가상환경이 활성화되었는지, "
            "requirements.txt의 패키지가 설치되었는지 확인하세요."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
