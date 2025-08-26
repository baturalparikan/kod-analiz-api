from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Hata mesajlarını basitleştirmek için sözlük
ERROR_TRANSLATIONS = {
    "SyntaxError": "Yazım hatası (örn. eksik parantez, yanlış sembol).",
    "IndentationError": "Girinti hatası (boşluklar veya tab yanlış).",
    "NameError": "Tanımsız değişken veya fonksiyon kullanılmış.",
    "TypeError": "Tür hatası (yanlış tipte değer kullanımı).",
    "ZeroDivisionError": "Sıfıra bölme hatası.",
    "IndexError": "Liste/array içinde olmayan bir elemana erişmeye çalıştın.",
    "KeyError": "Sözlükte olmayan bir anahtar kullanıldı.",
    "ValueError": "Geçersiz değer kullanıldı.",
    "AttributeError": "Nesnede olmayan bir özellik veya metod çağrıldı.",
    "ImportError": "Modül veya fonksiyon bulunamadı.",
    "ModuleNotFoundError": "İstenilen modül bulunamadı.",
    "OverflowError": "Sayı değeri çok büyük.",
    "RuntimeError": "Çalışma zamanı hatası.",
    "RecursionError": "Fonksiyon çok fazla kez kendini çağırdı (sonsuz döngü).",
}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Kod Analiz API çalışıyor!"})

@app.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"error": "Kod gönderilmedi"}), 400

    code = data["code"]

    try:
        # Önce sentaks hatalarını kontrol et
        compile(code, "<string>", "exec")
        exec(code, {})
        return jsonify({"result": "Kodda herhangi bir hata bulunamadı ✅"})
    except Exception as e:
        error_type = type(e).__name__
        line_no = getattr(e, "lineno", None)
        msg = str(e)

        # Kullanıcı dostu açıklama
        explanation = ERROR_TRANSLATIONS.get(error_type, "Bilinmeyen hata.")

        return jsonify({
            "error_type": error_type,
            "line": line_no,
            "original_message": msg,
            "explanation": explanation
        })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
