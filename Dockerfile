FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
