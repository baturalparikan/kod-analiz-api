from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import tempfile
import sys

app = Flask(__name__)
CORS(app)
# ------------------ Güvenli runtime çalıştırma ------------------
def run_code_safely(code, timeout_sec=3):
    temp_filename = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp:
            tmp.write(code)
            temp_filename = tmp.name

        proc = subprocess.run(
            [sys.executable, temp_filename],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        returncode = proc.returncode

        try:
            os.remove(temp_filename)
        except Exception:
            pass

        if returncode != 0:
            # stderr'i ayrıştırarak hata türünü çıkarmaya çalış
            lines = stderr.splitlines()
            err_type = "RuntimeError"
            err_msg = stderr
            for line in reversed(lines):
                if ":" in line:
                    parts = line.split(":", 1)
                    if parts[0].strip().endswith("Error"):
                        err_type = parts[0].strip()
                        err_msg = parts[1].strip()
                        break
            return {"error": err_msg, "error_type": err_type}
        else:
            return {"output": stdout}

    except subprocess.TimeoutExpired:
        try:
            if temp_filename:
                os.remove(temp_filename)
        except Exception:
            pass
        return {"error": "Execution timed out.", "error_type": "TimeoutError"}
    except Exception as e:
        try:
            if temp_filename:
                os.remove(temp_filename)
        except Exception:
            pass
        return {"error": str(e), "error_type": type(e).__name__}

# ---------------------------------------------------------------

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
    lang = data.get("lang", "en")

    # ----------------- Syntax hatalarını kontrol et -----------------
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

    if syntax_errors:
        return jsonify(syntax_errors)

    # ----------------- Runtime (çalışma zamanı) kontrolü -----------------
    runtime_result = run_code_safely(code, timeout_sec=3)
    if "error" in runtime_result:
        err_msg = runtime_result["error"]
        error_type = runtime_result.get("error_type", "RuntimeError")
        explanation = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get(error_type, "Runtime error occurred.")
        return jsonify([{
            "error_type": error_type,
            "line": "?",
            "original_message": err_msg,
            "explanation": explanation,
            "simple_explanation": explanation
        }])

    # ----------------- Pylint ile çoklu hata kontrolü -----------------
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(code)
            temp_filename = temp_file.name

        result = subprocess.run(
            ["pylint", "--output-format=json", temp_filename],
            capture_output=True, text=True
        )

        pylint_output = json.loads(result.stdout) if result.stdout else []

        errors = []
        for item in pylint_output:
            error_type = item.get("type", "error")
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
