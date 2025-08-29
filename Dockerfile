# Python tabanı
FROM python:3.11-slim

# Sistem güncelle ve Java (JDK) kur
RUN apt-get update && \
    apt-get install -y default-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Render Docker genelde 10000 portunu kullanır
EXPOSE 10000

# Uygulamayı başlat
CMD ["python", "app.py"]
