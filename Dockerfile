# Python tabanı
FROM python:3.11-slim

# Sistem güncelleme ve Java (JDK) kurulum
RUN apt-get update && \
    apt-get install -y default-jdk wget unzip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# JAVA_HOME ve PATH ayarı
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Çalışma dizini
WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Render genelde 10000 portunu kullanır
EXPOSE $PORT

# Uygulamayı başlat
CMD ["python", "app.py"]
