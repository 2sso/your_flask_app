FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# gunicorn이 requirements.txt에 포함되어 있어야 합니다.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
