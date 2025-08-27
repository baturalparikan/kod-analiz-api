from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import tempfile

app = Flask(__name__)
CORS(app)

# Hata mesajlarını basitleştirmek için sözlük
ERROR_TRANSLATIONS = {
    "tr": {
        "SyntaxError": "Yazım hatası (eksik veya yanlış sembol).",
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
        "RecursionError": "Fonksiyon çok fazla kez kendini çağırdı (sonsuz döngü)."
    },
    "en": {
        "SyntaxError": "Syntax error (missing or incorrect symbol).",
        "IndentationError": "Indentation error (spaces or tabs incorrect).",
        "NameError": "Undefined variable or function used.",
        "TypeError": "Type error (wrong type used).",
        "ZeroDivisionError": "Division by zero error.",
        "IndexError": "Index out of range.",
        "KeyError": "Key does not exist in dictionary.",
        "ValueError": "Invalid value used.",
        "AttributeError": "Object has no such attribute or method.",
        "ImportError": "Module or function not found.",
        "ModuleNotFoundError": "Requested module not found.",
        "OverflowError": "Number value too large.",
        "RuntimeError": "Runtime error occurred.",
        "RecursionError": "Function called itself too many times (infinite loop)."
    }
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
    lang = data.get("lang", "en")  # Kullanıcı dilini al, yoksa İngilizce

    # 1️⃣ Syntax hatalarını kontrol et
    syntax_errors = []
    try:
        compile(code, "<string>", "exec")
    except Exception as e:
        error_type = type(e).__name__
        line_no = getattr(e, "lineno", "?")
        msg = str(e)
        explanation = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get(error_type, "Unknown error.")
        syntax_errors.append({
            "error_type": error_type,
            "line": line_no,
            "original_message": msg,
            "explanation": explanation,
            "simple_explanation": explanation
        })

    # Eğer syntax hatası varsa tek JSON array döndür
    if syntax_errors:
        return jsonify(syntax_errors)

    # 2️⃣ Pylint ile çoklu hata kontrolü
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(code)
            temp_filename = temp_file.name

        # pylint çalıştır
        result = subprocess.run(
            ["pylint", "--output-format=json", temp_filename],
            capture_output=True, text=True
        )

        pylint_output = json.loads(result.stdout) if result.stdout else []

        errors = []
        for item in pylint_output:
            error_type = item.get("type", "error")  # Pylint tipleri: convention, refactor, warning, error, fatal
            line_no = item.get("line", "?")
            msg = item.get("message", "")
            explanation = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get(error_type, "Unknown error.")
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
            no_error_msg = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get("NoError", "No errors found in code.")
            return jsonify({"result": no_error_msg})

    except Exception as e:
        return jsonify({"error": str(e)})


    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
