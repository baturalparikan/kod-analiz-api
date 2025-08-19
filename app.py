from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Kod Analiz API çalışıyor!"})

@app.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"error": "Kod gönderilmedi"}), 400

    code = data["code"]

    # Basit test analizleri
    errors = []
    if "print(" not in code:
        errors.append("Kodda 'print()' kullanılmamış.")
    if "def " not in code:
        errors.append("Fonksiyon tanımı bulunamadı.")
    if "import " not in code:
        errors.append("Herhangi bir kütüphane import edilmemiş.")

    if not errors:
        result = "Kodda temel kontroller geçti, sorun bulunamadı."
    else:
        result = " | ".join(errors)

    return jsonify({
        "result": result
    })
