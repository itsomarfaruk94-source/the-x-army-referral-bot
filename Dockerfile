FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt
COPY app ./app
COPY .env.example ./.env.example
RUN mkdir -p /app/data
CMD ["uvicorn", "app.web:app", "--host", "0.0.0.0", "--port", "8000"]
