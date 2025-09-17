FROM python:3.12-alpine

LABEL maintainer="https://github.com/techouse"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir sqlite3-to-mysql && \
    pip install typing-extensions

ENTRYPOINT ["sqlite3mysql"]
