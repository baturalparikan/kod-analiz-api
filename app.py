from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import tempfile
import os

app = Flask(__name__)
CORS(app)

# Hata mesajlarını basitleştirmek için sözlük
ERROR_TRANSLATIONS = {
    "convention": "Kod stili uyarısı.",
    "refactor": "Kodun iyileştirilmesi önerisi.",
    "warning": "Uyarı, potansiyel sorun.",
    "error": "Hata oluştu.",
    "fatal": "Ciddi hata, kod çalışmaz.",
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
    errors = []

    try:
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(code)
            temp_filename = temp_file.name

        # pylint çalıştır (kod çalıştırılmadan analiz)
        result = subprocess.run(
            ["pylint", "--output-format=json", temp_filename],
            capture_output=True, text=True
        )

        pylint_output = json.loads(result.stdout) if result.stdout else []

        for item in pylint_output:
            error_type = item.get("type", "error")
            line_no = item.get("line", "?")
            msg = item.get("message", "")
            explanation = ERROR_TRANSLATIONS.get(error_type, "Bilinmeyen hata.")
            errors.append({
                "error_type": error_type,
                "line": line_no,
                "original_message": msg,
                "explanation": explanation,
                "simple_explanation": explanation
            })

        os.remove(temp_filename)

        if errors:
            return jsonify(errors)
        else:
            return jsonify({"result": "Kodda herhangi bir hata bulunamadı ✅"})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
