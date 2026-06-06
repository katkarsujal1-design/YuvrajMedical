FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y tesseract-ocr

RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
