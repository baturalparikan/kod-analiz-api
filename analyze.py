# analyze.py
from flask import Flask, request, jsonify
from pylint import epylint as lint
from java_runner import analyze_java
import tempfile
import os

app = Flask(__name__)

def analyze_python(code: str):
    """
    Python kodunu Pylint ile analiz eder ve hataları JSON olarak döndürür.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_file.write(code.encode("utf-8"))
    temp_file.close()

    (pylint_stdout, pylint_stderr) = lint.py_run(temp_file.name, return_std=True)
    stdout = pylint_stdout.getvalue()
    stderr = pylint_stderr.getvalue()

    os.unlink(temp_file.name)  # geçici dosyayı sil

    errors = []
    for line in stdout.splitlines():
        # Pylint formatı: path:line:col: type: message
        parts = line.split(":", 3)
        if len(parts) == 4:
            _, line_no, _, message = parts
            errors.append({
                "error_type": "PythonLint",
                "line": line_no.strip(),
                "original_message": message.strip(),
                "explanation": "Python kodu Pylint ile analiz edildi.",
                "solution": "Hata mesajına göre kodu düzeltin."
            })

    return {"compiled": True, "compilation_errors": errors}

@app.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.json or {}
    code = data.get("code", "")
    programming_language = data.get("programming_language", "python").lower()

    if not code.strip():
        return jsonify({"error": "Kod boş olamaz."}), 400

    try:
        if programming_language == "java":
            result = analyze_java(code)
        else:
            result = analyze_python(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "compiled": False,
            "compilation_errors": [{
                "error_type": type(e).__name__,
                "line": "?",
                "original_message": str(e),
                "explanation": "Beklenmeyen hata.",
                "solution": "Sunucu loglarını kontrol edin."
            }]
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
