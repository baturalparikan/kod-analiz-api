# judge0_client.py
import os
import requests

# Varsayılan public Judge0 instance (hızlı test için). Üretimde kendi instance'ını veya API anahtarını kullan.
JUDGE0_BASE = os.environ.get("JUDGE0_BASE", "https://ce.judge0.com")
JUDGE0_API_KEY = os.environ.get("JUDGE0_API_KEY", "")  # opsiyonel

HEADERS = {"Content-Type": "application/json"}
if JUDGE0_API_KEY:
    HEADERS["X-Auth-Token"] = JUDGE0_API_KEY

def find_language_id_by_name(substr="java"):
    """Judge0'daki diller listesinden 'java' içeren bir language_id döndürür."""
    url = f"{JUDGE0_BASE}/languages"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    langs = r.json()
    for item in langs:
        name = (item.get("name") or "").lower()
        display = (item.get("display_name") or "").lower()
        if substr in name or substr in display:
            return item.get("id")
    return None

def run_code_on_judge0(source_code, language_substr="java", stdin="", wait=True, cpu_time_limit=2.0):
    """
    source_code: kod string
    language_substr: 'java' gibi (Judge0 dil ID'sini bulmak için)
    wait: True ise sync; sonucu bekler
    cpu_time_limit: Judge0 tarafı için talep edilen CPU süresi (saniye)
    Döndürür: Judge0'dan gelen JSON cevabı (compile_output, stdout, stderr, status vb.)
    """
    lang_id = find_language_id_by_name(language_substr)
    if not lang_id:
        return {"error": "Judge0 üzerinde uygun language_id bulunamadı."}

    url = f"{JUDGE0_BASE}/submissions?base64_encoded=false&wait={'true' if wait else 'false'}"
    payload = {
        "source_code": source_code,
        "language_id": lang_id,
        "stdin": stdin,
        # CPU limit string format bazı instance'larda farklı olabilir; Judge0 instance'ına göre uyarlayın
        "cpu_time_limit": str(cpu_time_limit)
    }

    r = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()
