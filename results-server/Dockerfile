FROM python:3.11-slim

WORKDIR /app

COPY server.py .
COPY discord_notif.py .
COPY static ./static

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5680

CMD ["python3", "server.py"]
