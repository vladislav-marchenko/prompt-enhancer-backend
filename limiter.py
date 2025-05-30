from fastapi import Request
from datetime import datetime, timedelta

REQUESTS = {}
LIMIT = 50
WINDOW = timedelta(days=1)


def limiter(request: Request):
    client_ip = request.client.host
    now = datetime.now()

    if client_ip not in REQUESTS:
        REQUESTS[client_ip] = []

    # Remove expired timestamps
    REQUESTS[client_ip] = [timestamp for timestamp in REQUESTS[client_ip]
                           if now - timestamp < WINDOW]

    if len(REQUESTS[client_ip]) >= LIMIT:
        return False

    REQUESTS[client_ip].append(now)
    return True
