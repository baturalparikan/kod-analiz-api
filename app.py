from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import tempfile
import sys
import traceback

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
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

        # Geçici dosyayı sil
        try:
            os.remove(temp_filename)
        except Exception:
            pass

        if returncode != 0:
            # Hata satırını bul
            line_no = "?"
            try:
                tb_lines = stderr.splitlines()
                for line in reversed(tb_lines):
                    if ", line " in line:
                        parts = line.split(", line ")
                        line_no = int(parts[1].split(",")[0])
                        break
            except:
                pass

            # Hata tipini ayrıştır
            last_line = stderr.splitlines()[-1] if stderr else ""
            if ": " in last_line:
                err_type, err_msg = last_line.split(": ", 1)
            else:
                err_type, err_msg = "RuntimeError", stderr

            return {"error": err_msg, "error_type": err_type.strip(), "line": line_no}
        else:
            return {"output": stdout}

    except subprocess.TimeoutExpired:
        try:
            if temp_filename:
                os.remove(temp_filename)
        except Exception:
            pass
        return {"error": "Execution timed out.", "error_type": "TimeoutError", "line": "?"}
    except Exception as e:
        try:
            if temp_filename:
                os.remove(temp_filename)
        except Exception:
            pass
        tb = traceback.extract_tb(e.__traceback__)
        line_no = tb[-1].lineno if tb else "?"
        return {"error": str(e), "error_type": type(e).__name__, "line": line_no}

# ---------------------------------------------------------------

# Hata mesajlarını basitleştirmek için sözlük
ERROR_TRANSLATIONS = {
    "tr": {
        "SyntaxError": {
            "explanation": "Yazım hatası (eksik veya yanlış sembol).",
            "solution": "Kodunuzu dikkatlice gözden geçirin, eksik parantez veya iki nokta gibi sembolleri ekleyin."
        },
        "IndentationError": {
            "explanation": "Girinti hatası (boşluklar veya tab yanlış).",
            "solution": "Girintileri kontrol edin; karışık tab ve boşluk kullanmamaya dikkat edin."
        },
        "NameError": {
            "explanation": "Tanımsız değişken veya fonksiyon kullanılmış.",
            "solution": "Değişken veya fonksiyon adlarını doğru yazdığınızdan emin olun."
        },
        "TypeError": {
            "explanation": "Tür hatası (yanlış tipte değer kullanımı).",
            "solution": "Değişkenlerin tiplerini kontrol edin, uygun tipte değerler kullanın."
        },
        "ZeroDivisionError": {
            "explanation": "Sıfıra bölme hatası.",
            "solution": "Bölünecek sayının sıfır olmadığını kontrol edin."
        },
        "IndexError": {
            "explanation": "Liste/array içinde olmayan bir elemana erişmeye çalıştın.",
            "solution": "İndekslerin liste uzunluğu içinde olup olmadığını kontrol edin."
        },
        "KeyError": {
            "explanation": "Sözlükte olmayan bir anahtar kullanıldı.",
            "solution": "Kullanmak istediğiniz anahtarın sözlükte var olduğundan emin olun."
        },
        "ValueError": {
            "explanation": "Geçersiz değer kullanıldı.",
            "solution": "Fonksiyon veya metod için geçerli değerler girin."
        },
        "AttributeError": {
            "explanation": "Nesnede olmayan bir özellik veya metod çağrıldı.",
            "solution": "Nesnenin metod ve özelliklerini kontrol edin."
        },
        "ImportError": {
            "explanation": "Modül veya fonksiyon bulunamadı.",
            "solution": "Modülün doğru kurulduğundan ve ismini doğru yazdığınızdan emin olun."
        },
        "ModuleNotFoundError": {
            "explanation": "İstenilen modül bulunamadı.",
            "solution": "Modülün kurulu olup olmadığını ve doğru yazıldığını kontrol edin."
        },
        "OverflowError": {
            "explanation": "Sayı değeri çok büyük.",
            "solution": "Sayı değerlerini makul aralıkta kullanın."
        },
        "RuntimeError": {
            "explanation": "Çalışma zamanı hatası.",
            "solution": "Kodun mantığını gözden geçirin, beklenmeyen durumları kontrol edin."
        },
        "RecursionError": {
            "explanation": "Fonksiyon çok fazla kez kendini çağırdı (sonsuz döngü).",
            "solution": "Fonksiyonunuzun çıkış koşulunu doğru tanımladığınızdan emin olun."
        }
    },
    "en": {
        "SyntaxError": {
            "explanation": "Syntax error (missing or incorrect symbol).",
            "solution": "Check your code for missing or misplaced symbols like parentheses or colons."
        },
        "IndentationError": {
            "explanation": "Indentation error (spaces or tabs incorrect).",
            "solution": "Check your indentation; avoid mixing tabs and spaces."
        },
        "NameError": {
            "explanation": "Undefined variable or function used.",
            "solution": "Make sure the variable or function exists and is spelled correctly."
        },
        "TypeError": {
            "explanation": "Type error (wrong type used).",
            "solution": "Check variable types and use compatible types."
        },
        "ZeroDivisionError": {
            "explanation": "Division by zero error.",
            "solution": "Ensure the denominator is not zero before dividing."
        },
        "IndexError": {
            "explanation": "Index out of range.",
            "solution": "Check that indexes are within the length of lists or arrays."
        },
        "KeyError": {
            "explanation": "Key does not exist in dictionary.",
            "solution": "Check that the key exists in the dictionary."
        },
        "ValueError": {
            "explanation": "Invalid value used.",
            "solution": "Provide a valid value for the function or method."
        },
        "AttributeError": {
            "explanation": "Object has no such attribute or method.",
            "solution": "Verify that the object has the attribute or method you are calling."
        },
        "ImportError": {
            "explanation": "Module or function not found.",
            "solution": "Check if the module is installed and the name is correct."
        },
        "ModuleNotFoundError": {
            "explanation": "Requested module not found.",
            "solution": "Ensure the module is installed and correctly named."
        },
        "OverflowError": {
            "explanation": "Number value too large.",
            "solution": "Use numbers within a reasonable range."
        },
        "RuntimeError": {
            "explanation": "Runtime error occurred.",
            "solution": "Check your code logic and handle unexpected cases."
        },
        "RecursionError": {
            "explanation": "Function called itself too many times (infinite loop).",
            "solution": "Make sure your recursive function has a proper exit condition."
        }
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
            "line": runtime_result.get("line", "?"),
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
