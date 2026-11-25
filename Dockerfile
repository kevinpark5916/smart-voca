# 2026-11-25 - SmartVoca - 학교 서버 배포용 이미지: 웹 버전, SQLite(/data), UID 10001, 포트 8080 (DR-18)
# 파일 위치: Dockerfile
# 빌드: docker build -t smartvoca-web .
# 실행: docker run --rm -p 8080:8080 -v smartvoca-data:/data smartvoca-web

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DB_PATH=/data/voca.db

WORKDIR /app

# UID 10001 사용자를 만들고 쓰기 가능한 /data를 준비한다 (R-05, R-06)
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /data \
    && chown 10001:10001 /data

# 의존성을 먼저 설치해 빌드 캐시를 살린다 (R-13)
COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

COPY src ./src
COPY data/words.csv ./data/words.csv

USER 10001

EXPOSE 8080

# 운영 서버로 실행한다. 워커는 1개, 스레드는 1개 (진행 중 시험 상태가 프로세스 메모리에 있고 SQLite 연결을 여러 스레드가 나눠 쓰지 않도록)
CMD ["gunicorn", "--chdir", "/app/src", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "1", "wsgi:app"]
