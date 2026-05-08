FROM python:3.11-slim

WORKDIR /app

COPY djaga/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY djaga/ ./djaga/

CMD ["python", "djaga/bot.py"]
