# java_runner.py
import tempfile
import os
import subprocess
import re
import shutil
import xml.etree.ElementTree as ET
import resource

# resource limits (saniye / byte)
CPU_TIME_LIMIT = 4       # CPU seconds
ADDRESS_SPACE_LIMIT = 300 * 1024 * 1024  # 300 MB

def _limit_resources():
    # Only works on Unix (Docker Linux). Limits apply to child process.
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (CPU_TIME_LIMIT, CPU_TIME_LIMIT))
        resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_LIMIT, ADDRESS_SPACE_LIMIT))
    except Exception:
        pass

def _run_with_limits(cmd, cwd=None, timeout=6):
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                          timeout=timeout, preexec_fn=_limit_resources)
    return proc

def analyze_java(code: str, timeout: int = 6):
    temp_dir = tempfile.mkdtemp(prefix="java-")
    try:
        # package detection
        pkg_match = re.search(r'^\s*package\s+([\w.]+)\s*;', code, flags=re.M)
        if pkg_match:
            pkg = pkg_match.group(1)
            pkg_path = os.path.join(temp_dir, *pkg.split('.'))
            os.makedirs(pkg_path, exist_ok=True)
            # If public class is present, filename must match it
            class_match = re.search(r'public\s+class\s+([A-Za-z_]\w*)', code)
            classname = class_match.group(1) if class_match else "Main"
            java_file = os.path.join(pkg_path, f"{classname}.java")
        else:
            # no package
            class_match = re.search(r'public\s+class\s+([A-Za-z_]\w*)', code)
            classname = class_match.group(1) if class_match else "Main"
            java_file = os.path.join(temp_dir, f"{classname}.java")

        # write file
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(code)

        # compile with javac -Xlint:all
        compile_cmd = ["javac", "-Xlint:all", java_file]
        try:
            compile_proc = _run_with_limits(compile_cmd, cwd=temp_dir, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {
                "compiled": False,
                "compilation_errors": [{
                    "error_type": "TimeoutError",
                    "line": "?",
                    "original_message": "javac timed out",
                    "explanation": "Derleme zaman aşımına uğradı.",
                    "solution": "Kodu basitleştirin veya timeout'u artırın."
                }]
            }

        if compile_proc.returncode != 0:
            stderr = compile_proc.stderr or compile_proc.stdout or ""
            errors = []
            # örnek: /tmp/java-.../Main.java:3: error: ';' expected
            for line in stderr.splitlines():
                m = re.search(rf'{re.escape(os.path.basename(java_file))}:(\d+):\s*(.*)', line)
                if m:
                    errors.append({
                        "error_type": "CompilationError",
                        "line": int(m.group(1)),
                        "original_message": m.group(2).strip(),
                        "explanation": "Java derleyicisi hata raporu verdi.",
                        "solution": "Hata mesajına göre kodu düzeltin."
                    })
            if not errors:
                errors.append({
                    "error_type": "CompilationError",
                    "line": "?",
                    "original_message": stderr.strip(),
                    "explanation": "Java kodu derlenemedi.",
                    "solution": "Derleyici çıktısını kontrol edin."
                })
            return {"compiled": False, "compilation_errors": errors}

        # derleme başarılı -> checkstyle çalıştır (checkstyle.jar ve config önceden Docker içinde konumlandırılmalı)
        checkstyle_jar = "/usr/local/bin/checkstyle.jar"
        checkstyle_config = "/usr/local/etc/checkstyle/google_checks.xml"
        checkstyle_results = []
        if os.path.exists(checkstyle_jar) and os.path.exists(checkstyle_config):
            # checkstyle xml format output
            cs_cmd = ["java", "-jar", checkstyle_jar, "-c", checkstyle_config, "-f", "xml", java_file]
            try:
                cs_proc = _run_with_limits(cs_cmd, cwd=temp_dir, timeout=timeout)
            except subprocess.TimeoutExpired:
                return {
                    "compiled": True,
                    "compilation_errors": [],
                    "checkstyle": [{
                        "severity": "error",
                        "line": "?",
                        "message": "Checkstyle timeout",
                    }]
                }

            cs_out = cs_proc.stdout or cs_proc.stderr or ""
            # parse xml (Checkstyle XML format)
            try:
                root = ET.fromstring(cs_out)
                for file_el in root.findall('file'):
                    filepath = file_el.get('name')
                    for err in file_el.findall('error'):
                        checkstyle_results.append({
                            "file": filepath,
                            "line": int(err.get('line')) if err.get('line') and err.get('line').isdigit() else "?",
                            "severity": err.get('severity'),
                            "message": err.get('message'),
                            "source": err.get('source')
                        })
            except ET.ParseError:
                # If XML parse fails, return raw output
                checkstyle_results.append({
                    "file": java_file,
                    "line": "?",
                    "severity": "info",
                    "message": cs_out.strip()
                })
        else:
            checkstyle_results.append({
                "file": java_file,
                "line": "?",
                "severity": "warning",
                "message": "Checkstyle veya config bulunamadı (sunucuda yüklü olmalı)."
            })

        return {
            "compiled": True,
            "compilation_errors": [],
            "checkstyle": checkstyle_results
        }

    except Exception as e:
        return {
            "compiled": False,
            "compilation_errors": [{
                "error_type": type(e).__name__,
                "line": "?",
                "original_message": str(e),
                "explanation": "Beklenmeyen hata.",
                "solution": "Sunucu loglarını kontrol edin."
            }]
        }
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
