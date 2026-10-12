FROM python:3.15-alpine

LABEL maintainer="https://github.com/techouse"

RUN pip install --no-cache-dir sqlite3-to-mysql

ENTRYPOINT ["sqlite3mysql"]