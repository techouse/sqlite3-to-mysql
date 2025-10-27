FROM python:3.14-alpine

LABEL maintainer="https://github.com/techouse"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir sqlite3-to-mysql

ENTRYPOINT ["sqlite3mysql"]