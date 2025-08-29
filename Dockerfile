FROM python:3.11-slim

# Sistem güncelle ve Java (JDK) kur
RUN apt-get update && \
    apt-get install -y default-jdk && \
    java -version && javac -version && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["python", "app.py"]
