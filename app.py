from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # CORS aktif olsun ki farklı domainlerden de erişilebilsin

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Kod Analiz API çalışıyor!"})

@app.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"error": "Kod gönderilmedi"}), 400

    code = data["code"]

    # Burada yapay zekâ destekli analiz yerine şimdilik basit bir kontrol yapıyoruz
    if "print(" in code:
        analysis = "Kod geçerli görünüyor, print fonksiyonu içeriyor."
    else:
        analysis = "Kodda print fonksiyonu bulunamadı."

    return jsonify({
        "analysis": analysis
    })
