from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import tempfile
import sys
import traceback

from java_runner import analyze_java

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

        try:
            os.remove(temp_filename)
        except Exception:
            pass

        if returncode != 0:
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
# Hata mesajlarını basitleştirmek için sözlük (tüm diller)
ERROR_TRANSLATIONS = {
    "tr": {
        "SyntaxError": {"explanation":"Yazım hatası (eksik veya yanlış sembol).","solution":"Hatalı satırı gözden geçirin, eksik parantez veya iki nokta gibi sembolleri ekleyin veya değiştirin."},
        "IndentationError": {"explanation":"Girinti hatası (boşluklar veya tab yanlış).","solution":"Girintileri kontrol edin; karışık tab ve boşluk kullanmamaya dikkat edin."},
        "NameError": {"explanation":"Tanımsız değişken veya fonksiyon kullanılmış.","solution":"Değişken veya fonksiyon adlarını doğru yazdığınızdan emin olun."},
        "TypeError": {"explanation":"Tür hatası (yanlış tipte değer kullanımı).","solution":"Değişkenlerin tiplerini kontrol edin, uygun tipte değerler kullanın."},
        "ZeroDivisionError": {"explanation":"Sıfıra bölme hatası.","solution":"Bölünecek sayının sıfır olmadığını kontrol edin."},
        "IndexError": {"explanation":"Liste/array içinde olmayan bir elemana erişmeye çalıştın.","solution":"İndekslerin liste içinde olup olmadığını kontrol edin."},
        "KeyError": {"explanation":"Sözlükte olmayan bir anahtar kullanıldı.","solution":"Kullanmak istediğiniz anahtarın sözlükte var olduğundan emin olun."},
        "ValueError": {"explanation":"Geçersiz değer kullanıldı.","solution":"Fonksiyon veya metod için geçerli değerler girin."},
        "AttributeError": {"explanation":"Nesnede olmayan bir özellik veya metod çağrıldı.","solution":"Nesnenin metod ve özelliklerini kontrol edin."},
        "ImportError": {"explanation":"Modül veya fonksiyon bulunamadı.","solution":"Modülün doğru kurulduğundan ve ismini doğru yazdığınızdan emin olun."},
        "ModuleNotFoundError": {"explanation":"İstenilen modül bulunamadı.","solution":"Modülün kurulu olup olmadığını ve doğru yazıldığını kontrol edin."},
        "OverflowError": {"explanation":"Sayı değeri çok büyük.","solution":"Sayı değerlerini makul aralıkta kullanın."},
        "RuntimeError": {"explanation":"Çalışma zamanı hatası.","solution":"Kodun mantığını gözden geçirin, beklenmeyen durumları kontrol edin."},
        "RecursionError": {"explanation":"Fonksiyon çok fazla kez kendini çağırdı (sonsuz döngü).","solution":"Fonksiyonunuzun çıkış koşulunu doğru tanımladığınızdan emin olun."},
        "NoError": "Kodda hata bulunamadı."
    },
    "en": {
        "SyntaxError": {"explanation":"Syntax error (missing or incorrect symbol).","solution":"Check your code for missing or misplaced symbols like parentheses or colons."},
        "IndentationError": {"explanation":"Indentation error (spaces or tabs incorrect).","solution":"Check your indentation; avoid mixing tabs and spaces."},
        "NameError": {"explanation":"Undefined variable or function used.","solution":"Make sure the variable or function exists and is spelled correctly."},
        "TypeError": {"explanation":"Type error (wrong type used).","solution":"Check variable types and use compatible types."},
        "ZeroDivisionError": {"explanation":"Division by zero error.","solution":"Ensure the denominator is not zero before dividing."},
        "IndexError": {"explanation":"Index out of range.","solution":"Check that indexes are within the length of lists or arrays."},
        "KeyError": {"explanation":"Key does not exist in dictionary.","solution":"Check that the key exists in the dictionary."},
        "ValueError": {"explanation":"Invalid value used.","solution":"Provide a valid value for the function or method."},
        "AttributeError": {"explanation":"Object has no such attribute or method.","solution":"Verify that the object has the attribute or method you are calling."},
        "ImportError": {"explanation":"Module or function not found.","solution":"Check if the module is installed and the name is correct."},
        "ModuleNotFoundError": {"explanation":"Requested module not found.","solution":"Ensure the module is installed and correctly named."},
        "OverflowError": {"explanation":"Number value too large.","solution":"Use numbers within a reasonable range."},
        "RuntimeError": {"explanation":"Runtime error occurred.","solution":"Check your code logic and handle unexpected cases."},
        "RecursionError": {"explanation":"Function called itself too many times (infinite loop).","solution":"Make sure your recursive function has a proper exit condition."},
        "NoError": "No errors found in code."
    },
    "de": {
    "SyntaxError": {"explanation":"Syntaxfehler (fehlendes oder falsches Symbol).","solution":"Überprüfen Sie Ihren Code auf fehlende oder falsch platzierte Symbole wie Klammern oder Doppelpunkte."},
    "IndentationError": {"explanation":"Einrückungsfehler (Leerzeichen oder Tabs falsch).","solution":"Überprüfen Sie die Einrückungen; vermeiden Sie gemischte Tabs und Leerzeichen."},
    "NameError": {"explanation":"Nicht definierte Variable oder Funktion verwendet.","solution":"Stellen Sie sicher, dass die Variable oder Funktion existiert und korrekt geschrieben ist."},
    "TypeError": {"explanation":"Typfehler (falscher Typ verwendet).","solution":"Überprüfen Sie die Variablentypen und verwenden Sie kompatible Typen."},
    "ZeroDivisionError": {"explanation":"Division durch Null Fehler.","solution":"Stellen Sie sicher, dass der Nenner vor der Division nicht null ist."},
    "IndexError": {"explanation":"Index außerhalb des Bereichs.","solution":"Überprüfen Sie, dass die Indizes innerhalb der Länge von Listen oder Arrays liegen."},
    "KeyError": {"explanation":"Schlüssel existiert nicht im Wörterbuch.","solution":"Überprüfen Sie, dass der Schlüssel im Wörterbuch existiert."},
    "ValueError": {"explanation":"Ungültiger Wert verwendet.","solution":"Geben Sie einen gültigen Wert für die Funktion oder Methode ein."},
    "AttributeError": {"explanation":"Objekt hat dieses Attribut oder diese Methode nicht.","solution":"Überprüfen Sie, ob das Objekt das aufgerufene Attribut oder die Methode besitzt."},
    "ImportError": {"explanation":"Modul oder Funktion nicht gefunden.","solution":"Überprüfen Sie, ob das Modul installiert ist und der Name korrekt geschrieben ist."},
    "ModuleNotFoundError": {"explanation":"Angefordertes Modul nicht gefunden.","solution":"Stellen Sie sicher, dass das Modul installiert und korrekt benannt ist."},
    "OverflowError": {"explanation":"Zahlenwert zu groß.","solution":"Verwenden Sie Zahlen innerhalb eines angemessenen Bereichs."},
    "RuntimeError": {"explanation":"Laufzeitfehler aufgetreten.","solution":"Überprüfen Sie die Logik Ihres Codes und behandeln Sie unerwartete Fälle."},
    "RecursionError": {"explanation":"Funktion hat sich zu oft selbst aufgerufen (Endlosschleife).","solution":"Stellen Sie sicher, dass Ihre rekursive Funktion eine richtige Abbruchbedingung hat."},
    "NoError": "Keine Fehler im Code gefunden."
},
"ru": {
    "SyntaxError": {"explanation":"Синтаксическая ошибка (отсутствует или неверный символ).","solution":"Проверьте код на отсутствие или неправильное расположение символов, таких как скобки или двоеточия."},
    "IndentationError": {"explanation":"Ошибка отступа (неправильные пробелы или табуляции).","solution":"Проверьте отступы; избегайте смешивания табуляций и пробелов."},
    "NameError": {"explanation":"Использована неопределённая переменная или функция.","solution":"Убедитесь, что переменная или функция существует и написана правильно."},
    "TypeError": {"explanation":"Ошибка типа (неверный тип значения).","solution":"Проверьте типы переменных и используйте совместимые типы."},
    "ZeroDivisionError": {"explanation":"Ошибка деления на ноль.","solution":"Убедитесь, что делитель не равен нулю."},
    "IndexError": {"explanation":"Индекс вне диапазона.","solution":"Проверьте, что индексы находятся в пределах длины списка или массива."},
    "KeyError": {"explanation":"Ключ отсутствует в словаре.","solution":"Проверьте, что ключ существует в словаре."},
    "ValueError": {"explanation":"Использовано недопустимое значение.","solution":"Укажите допустимое значение для функции или метода."},
    "AttributeError": {"explanation":"Объект не имеет такого атрибута или метода.","solution":"Проверьте, есть ли у объекта вызываемый атрибут или метод."},
    "ImportError": {"explanation":"Модуль или функция не найдены.","solution":"Проверьте, установлен ли модуль и правильно ли написано его имя."},
    "ModuleNotFoundError": {"explanation":"Запрошенный модуль не найден.","solution":"Убедитесь, что модуль установлен и правильно назван."},
    "OverflowError": {"explanation":"Значение числа слишком велико.","solution":"Используйте числа в разумных пределах."},
    "RuntimeError": {"explanation":"Произошла ошибка выполнения.","solution":"Проверьте логику кода и обработайте неожиданные ситуации."},
    "RecursionError": {"explanation":"Функция вызвала сама себя слишком много раз (бесконечный цикл).","solution":"Убедитесь, что рекурсивная функция имеет правильное условие выхода."},
    "NoError": "Ошибок в коде не найдено."
},
"ar": {
    "SyntaxError": {"explanation":"خطأ في الصياغة (رمز مفقود أو غير صحيح).","solution":"تحقق من كودك من الرموز المفقودة أو الموضوعة بشكل خاطئ مثل الأقواس أو النقطتين."},
    "IndentationError": {"explanation":"خطأ في المسافة البادئة (المسافات أو علامات الجدولة غير صحيحة).","solution":"تحقق من المسافات البادئة؛ تجنب خلط علامات الجدولة والمسافات."},
    "NameError": {"explanation":"تم استخدام متغير أو دالة غير معرفة.","solution":"تأكد من أن المتغير أو الدالة موجودة ومكتوبة بشكل صحيح."},
    "TypeError": {"explanation":"خطأ في النوع (استخدام نوع خاطئ).","solution":"تحقق من أنواع المتغيرات واستخدم أنواع متوافقة."},
    "ZeroDivisionError": {"explanation":"خطأ القسمة على صفر.","solution":"تأكد من أن المقسوم عليه ليس صفرًا."},
    "IndexError": {"explanation":"الفهرس خارج النطاق.","solution":"تحقق من أن الفهارس ضمن طول القوائم أو المصفوفات."},
    "KeyError": {"explanation":"المفتاح غير موجود في القاموس.","solution":"تأكد من أن المفتاح موجود في القاموس."},
    "ValueError": {"explanation":"تم استخدام قيمة غير صالحة.","solution":"أدخل قيمة صالحة للدالة أو الطريقة."},
    "AttributeError": {"explanation":"الكائن لا يحتوي على هذا السمة أو الدالة.","solution":"تحقق من أن الكائن يحتوي على السمة أو الدالة المطلوبة."},
    "ImportError": {"explanation":"الوحدة أو الدالة غير موجودة.","solution":"تحقق من تثبيت الوحدة وكتابة الاسم بشكل صحيح."},
    "ModuleNotFoundError": {"explanation":"الوحدة المطلوبة غير موجودة.","solution":"تأكد من تثبيت الوحدة وكتابة الاسم بشكل صحيح."},
    "OverflowError": {"explanation":"قيمة الرقم كبيرة جدًا.","solution":"استخدم الأرقام ضمن نطاق معقول."},
    "RuntimeError": {"explanation":"حدث خطأ أثناء التشغيل.","solution":"تحقق من منطق الكود وتعامل مع الحالات غير المتوقعة."},
    "RecursionError": {"explanation":"استدعاء الدالة لنفسها مرات كثيرة (حلقة لا نهائية).","solution":"تأكد من أن الدالة المتكررة لها شرط خروج صحيح."},
    "NoError": "لم يتم العثور على أي أخطاء في الكود."
},
"zh": {
    "SyntaxError": {"explanation":"语法错误（缺少或错误的符号）。","solution":"检查代码中是否缺少或放错符号，如括号或冒号。"},
    "IndentationError": {"explanation":"缩进错误（空格或制表符错误）。","solution":"检查缩进；避免混合使用制表符和空格。"},
    "NameError": {"explanation":"使用了未定义的变量或函数。","solution":"确保变量或函数存在且拼写正确。"},
    "TypeError": {"explanation":"类型错误（使用了错误的类型）。","solution":"检查变量类型并使用兼容类型。"},
    "ZeroDivisionError": {"explanation":"除以零错误。","solution":"确保除数不为零。"},
    "IndexError": {"explanation":"索引超出范围。","solution":"检查索引是否在列表或数组长度范围内。"},
    "KeyError": {"explanation":"字典中不存在该键。","solution":"检查字典中是否存在该键。"},
    "ValueError": {"explanation":"使用了无效值。","solution":"为函数或方法提供有效值。"},
    "AttributeError": {"explanation":"对象没有该属性或方法。","solution":"确认对象是否具有调用的属性或方法。"},
    "ImportError": {"explanation":"模块或函数未找到。","solution":"检查模块是否已安装且名称正确。"},
    "ModuleNotFoundError": {"explanation":"请求的模块未找到。","solution":"确保模块已安装且名称正确。"},
    "OverflowError": {"explanation":"数字值过大。","solution":"使用合理范围内的数字。"},
    "RuntimeError": {"explanation":"运行时错误。","solution":"检查代码逻辑并处理意外情况。"},
    "RecursionError": {"explanation":"函数调用自身次数过多（无限循环）。","solution":"确保递归函数有正确的退出条件。"},
    "NoError": "代码未发现错误。"
},
"es": {
    "SyntaxError": {"explanation":"Error de sintaxis (símbolo faltante o incorrecto).","solution":"Verifique su código en busca de símbolos faltantes o mal ubicados como paréntesis o dos puntos."},
    "IndentationError": {"explanation":"Error de sangría (espacios o tabulación incorrectos).","solution":"Revise la sangría; evite mezclar tabulaciones y espacios."},
    "NameError": {"explanation":"Variable o función indefinida utilizada.","solution":"Asegúrese de que la variable o función exista y esté escrita correctamente."},
    "TypeError": {"explanation":"Error de tipo (tipo incorrecto utilizado).","solution":"Verifique los tipos de variables y use tipos compatibles."},
    "ZeroDivisionError": {"explanation":"Error de división por cero.","solution":"Asegúrese de que el denominador no sea cero antes de dividir."},
    "IndexError": {"explanation":"Índice fuera de rango.","solution":"Verifique que los índices estén dentro de la longitud de listas o matrices."},
    "KeyError": {"explanation":"La clave no existe en el diccionario.","solution":"Verifique que la clave exista en el diccionario."},
    "ValueError": {"explanation":"Valor inválido utilizado.","solution":"Proporcione un valor válido para la función o método."},
    "AttributeError": {"explanation":"El objeto no tiene tal atributo o método.","solution":"Verifique que el objeto tenga el atributo o método que está llamando."},
    "ImportError": {"explanation":"Módulo o función no encontrado.","solution":"Verifique si el módulo está instalado y que el nombre sea correcto."},
    "ModuleNotFoundError": {"explanation":"Módulo solicitado no encontrado.","solution":"Asegúrese de que el módulo esté instalado y correctamente nombrado."},
    "OverflowError": {"explanation":"Valor numérico demasiado grande.","solution":"Use números dentro de un rango razonable."},
    "RuntimeError": {"explanation":"Ocurrió un error en tiempo de ejecución.","solution":"Revise la lógica de su código y maneje casos inesperados."},
    "RecursionError": {"explanation":"La función se llamó a sí misma demasiadas veces (bucle infinito).","solution":"Asegúrese de que su función recursiva tenga una condición de salida adecuada."},
    "NoError": "No se encontraron errores en el código."
}

}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Kod Analiz API çalışıyor!"})

@app.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json()

    print("GELEN JSON:", data)  # Debug: gelen veriyi terminalde gösterir

    if not data or "code" not in data:
        return jsonify({"error": "Kod gönderilmedi"}), 400

    code = data["code"]
    lang = data.get("lang", "en").lower()

    # ----------------- Java kodu kontrolü -----------------
    prog_lang = data.get("programming_language", "Python").lower()  # Frontend’den gelen gerçek programlama dili

    if prog_lang == "java":
        try:
            # analyze_java ya dict (başarılı çıktı) ya da list (hatalar) döndürecek
            result = analyze_java(code, timeout=5)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": "Java analizinde iç hata: " + str(e)}), 500

    # ----------------- Python ve diğer işlemler buraya devam eder -----------------

    # ----------------- Python kodu kontrolü -----------------
    syntax_errors = []
    try:
        compile(code, "<string>", "exec")
    except Exception as e:
        error_type = type(e).__name__
        line_no = getattr(e, "lineno", "?")
        msg = str(e)

        error_info = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get(error_type, {})
        explanation = error_info.get("explanation", "No explanation available.")
        solution = error_info.get("solution", "No solution available.")

        syntax_errors.append({
            "error_type": error_type,
            "line": line_no,
            "original_message": msg,
            "explanation": explanation,
            "solution": solution
        })

    if syntax_errors:
        return jsonify(syntax_errors)

    # ----------------- Runtime (çalışma zamanı) kontrolü -----------------
    runtime_result = run_code_safely(code, timeout_sec=3)
    if "error" in runtime_result:
        err_msg = runtime_result["error"]
        error_type = runtime_result.get("error_type", "RuntimeError")

        error_info = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get(error_type, {})
        explanation = error_info.get("explanation", "No explanation available.")
        solution = error_info.get("solution", "No solution available.")

        return jsonify([{
            "error_type": error_type,
            "line": runtime_result.get("line", "?"),
            "original_message": err_msg,
            "explanation": explanation,
            "solution": solution
        }])

        # ----------------- Pylint ile çoklu hata kontrolü -----------------
    errors = []
    temp_filename = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(code)
            temp_filename = temp_file.name

        result = subprocess.run(
            ["pylint", "--output-format=json", temp_filename],
            capture_output=True, text=True
        )

        pylint_output = json.loads(result.stdout) if result.stdout else []

        for item in pylint_output:
            error_type = item.get("type", "error")
            line_no = item.get("line", "?")
            msg = item.get("message", "")
            error_info = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get(error_type, {})
            explanation = error_info.get("explanation", msg)
            solution = error_info.get("solution", "")

            errors.append({
                "error_type": error_type,
                "line": line_no,
                "original_message": msg,
                "explanation": explanation,
                "solution": solution
            })

        if errors:
            return jsonify(errors)
        else:
            no_error_msg = ERROR_TRANSLATIONS.get(lang, ERROR_TRANSLATIONS["en"]).get("NoError", "No errors found in code.")
            return jsonify({"result": no_error_msg})

    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render'ın verdiği PORT değerini al
    app.run(host="0.0.0.0", port=port)
