# my-rag-ui/Dockerfile

FROM python:3.11-slim

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

CMD ["python", "-u", "app.py"]