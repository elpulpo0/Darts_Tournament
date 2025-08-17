#!/bin/sh
chown -R appuser:appuser /app/logs /app/database /app/backups 2>/dev/null || true

exec su-exec appuser "$@"