FROM python:alpine

WORKDIR /app

# Install dependencies required for Rust and Cargo
RUN apk add --no-cache \
    gcc \
    musl-dev \
    su-exec

RUN adduser -D -s /bin/sh appuser

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "run.py"]