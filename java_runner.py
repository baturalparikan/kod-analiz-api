# java_runner.py
import tempfile
import os
import subprocess
import re
import shutil

def analyze_java(code: str, timeout: int = 5):
    """
    Verilen Java kodunu geçici bir klasöre yazıp derler ve çalıştırır.
    Derleme hataları veya runtime hatalarını ayrıştırıp JSON-benzeri yapı döner.
    Dönen değer ya {'output': '...'} ya da [ {error obj}, ... ] dizisidir.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # public class NAME var mı kontrol et, yoksa Main kullan
        m = re.search(r'public\s+class\s+([A-Za-z_]\w*)', code)
        class_name = m.group(1) if m else "Main"
        java_file = os.path.join(temp_dir, f"{class_name}.java")

        # Java dosyasını yaz
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(code)

        # javac ile derleme
        compile_proc = subprocess.run(
            ["javac", java_file],
            capture_output=True, text=True, timeout=timeout
        )

        if compile_proc.returncode != 0:
            stderr = compile_proc.stderr or compile_proc.stdout or ""
            errors = []

            # Javac hata formatlarını esnekçe yakalamaya çalış
            for line in stderr.splitlines():
                # Ör: Main.java:3: error: ';' expected
                mline = re.search(rf'{re.escape(os.path.basename(java_file))}:(\d+):\s*(.*)', line)
                if mline:
                    line_no = int(mline.group(1))
                    msg = mline.group(2).strip()
                    errors.append({
                        "error_type": "CompilationError",
                        "line": line_no,
                        "original_message": msg,
                        "explanation": "Java kodunda derleme hatası oluştu.",
                        "solution": "Hata mesajını kontrol edin ve kodu düzeltin."
                    })

            # Eğer ayrıştırılamadıysa tüm stderr'i döndür
            if not errors:
                errors.append({
                    "error_type": "CompilationError",
                    "line": "?",
                    "original_message": stderr.strip(),
                    "explanation": "Java kodu derlenemedi.",
                    "solution": "Derleme hatasını kontrol edin ve kodu düzeltin."
                })

            return errors

        # Derleme başarılı -> sınıfı çalıştır
        run_proc = subprocess.run(
            ["java", "-cp", temp_dir, class_name],
            capture_output=True, text=True, timeout=timeout
        )

        if run_proc.returncode != 0:
            stderr = run_proc.stderr or run_proc.stdout or ""
            first_line = stderr.splitlines()[0] if stderr.splitlines() else ""
            # stacktrace içinde sınıf:line şeklini bulmaya çalış
            line_no = "?"
            for l in stderr.splitlines():
                mm = re.search(rf'\b{re.escape(class_name)}\.java:(\d+)\)', l)
                if mm:
                    line_no = mm.group(1)
                    break

            return [{
                "error_type": "RuntimeError",
                "line": line_no,
                "original_message": first_line.strip() or stderr.strip(),
                "explanation": "Java çalışma zamanı hatası (exception/stacktrace).",
                "solution": "Stacktrace'i inceleyin; hataya neden olan satırı düzeltin."
            }]

        # Her şey yolundaysa stdout döner
        return {"output": run_proc.stdout.strip()}

    except subprocess.TimeoutExpired:
        return [{
            "error_type": "TimeoutError",
            "line": "?",
            "original_message": "Java derleme/çalıştırma zaman aşımına uğradı.",
            "explanation": "Kod belirtilen süre içinde tamamlanmadı.",
            "solution": "Uzun döngüleri/kısıtlı işlemleri gözden geçirin veya timeout'u artırın."
        }]
    except Exception as e:
        return [{
            "error_type": type(e).__name__,
            "line": "?",
            "original_message": str(e),
            "explanation": "Beklenmeyen bir hata oluştu.",
            "solution": "Sunucu günlüklerini kontrol edin."
        }]
    finally:
        # temp dizin temizleme
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
