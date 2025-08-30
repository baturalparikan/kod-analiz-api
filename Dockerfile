# Dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# sistem paketleri + JDK + wget unzip
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-jdk wget unzip ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# JAVA_HOME ve PATH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /app

# python bağımlılıkları
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# checkstyle indir
RUN wget -q https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.12.0/checkstyle-10.12.0-all.jar -O /usr/local/bin/checkstyle.jar \
    && mkdir -p /usr/local/etc/checkstyle \
    && wget -q https://raw.githubusercontent.com/checkstyle/checkstyle/master/src/main/resources/google_checks.xml -O /usr/local/etc/checkstyle/google_checks.xml

# uygulama
COPY . /app

# Render genelde PORT verir, EXPOSE optional
EXPOSE 10000

# production: gunicorn, env var $PORT kullanılacak
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120"]
