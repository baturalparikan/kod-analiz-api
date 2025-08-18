from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Kod Analiz API çalışıyor!"})

@app.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"error": "Kod gönderilmedi"}), 400

    code = data["code"]
    lang = data.get("lang", "tr")  # Türkçe varsayılan

    # Basit bir hata tespit simülasyonu (ileride yapay zekâ koyacağız)
    errors = []
    if "def " in code and not code.strip().endswith(":"):
        errors.append("Fonksiyon tanımı ':' ile bitmiyor.")

    if "print(" not in code:
        errors.append("Kodda 'print' fonksiyonu bulunamadı.")

    if not errors:
        result_tr = "Kodda hata bulunamadı ✅"
        result_en = "No errors found ✅"
    else:
        result_tr = "Hatalar:\n- " + "\n- ".join(errors)
        result_en = "Errors:\n- " + "\n- ".join(errors)

    # Dil seçimine göre cevap
    if lang == "en":
        return jsonify({"result": result_en})
    else:
        return jsonify({"
