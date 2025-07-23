# my-rag-ui/Dockerfile

FROM python:3.11-slim

RUN pip install --upgrade pip

WORKDIR /app

# 安裝必要套件，但不複製 app.py 進 image（用 volume 連接）
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# 開發模式下啟動
CMD ["python", "-u", "app.py"]