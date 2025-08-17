FROM python:alpine

WORKDIR /app

RUN adduser -D -s /bin/sh appuser

RUN apk add --no-cache su-exec

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "run.py"]