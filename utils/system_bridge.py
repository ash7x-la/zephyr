import os
import subprocess
import json
import httpx
import urllib.parse
import re
from core.logger import Logger
from core.config import Config

def list_dir(path=".", **kwargs):
    try:
        current_path = os.path.abspath(path)
        items = os.listdir(current_path)
        return {"status": "success", "data": items}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_file(path, **kwargs):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "success", "data": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def write_file(path, content, **kwargs):
    try:
        # PENTING: Pastikan folder tujuan ada
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success", "message": f"File {path} berhasil ditulis."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_command(command, **kwargs):
    try:
        # SAFETY GUARDRAIL: Prevent suicidal AI actions
        cmd_lower = command.lower()
        
        # 1. Block known patterns targeting the proxy port
        if "8000" in cmd_lower and ("kill" in cmd_lower or "fuser" in cmd_lower or "pkill" in cmd_lower):
            return {"status": "error", "message": "[SYSTEM BLOCKED] CRITICAL! Dilarang keras menghentikan proses pada port 8000. Itu adalah nyawa (Proxy API) Zephyr Assistant!"}
        
        # 2. Block generic pkill/killall representing high risk
        if "pkill " in cmd_lower or "killall " in cmd_lower:
            return {"status": "error", "message": "[SYSTEM BLOCKED] Penggunaan pkill atau killall dilarang karena berisiko mematikan agent secara keseluruhan."}

        # 3. Deep PID protection (check if target PIDs belong to port 8000)
        pids_in_cmd = re.findall(r"\b\d{2,7}\b", command)
        if pids_in_cmd and "kill" in cmd_lower:
            try:
                # Find PIDs using port 8000
                proxy_pids_raw = subprocess.check_output("lsof -t -i:8000", shell=True, text=True).strip()
                proxy_pids = proxy_pids_raw.split("\n") if proxy_pids_raw else []
                for pid in pids_in_cmd:
                    if pid in proxy_pids:
                        return {"status": "error", "message": f"[SYSTEM BLOCKED] PID {pid} terdeteksi sebagai Proxy API (Port 8000). DILARANG MEMBUNUH LAYANAN INI."}
            except:
                pass # lsof might fail if no process on 8000

        Logger.info(f"Mengeksekusi perintah: {command}")
        
        # Cegah proses background bikin subprocess.run bengong nungguin pipe STDOUT
        cmd_strip = command.strip()
        if cmd_strip.endswith("&") and ">" not in cmd_strip:
            command = cmd_strip[:-1] + " > /dev/null 2>&1 &"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "message": result.stderr if result.returncode != 0 else f"Command '{command}' success.",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired as e:
        # Jika timeout (30s) tapi mungkin berhasil jalan di background
        out_msg = e.stdout if e.stdout else ""
        return {"status": "success", "message": f"Command timed out after 30s. Jika ini adalah server, kemungkinan sudah berjalan di background. Output: {out_msg}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def search_browser(query, **kwargs):
    import re
    try:
        Logger.info(f"Mencari web: {query}")
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        
        # Gunakan httpx dengan trust_env=False untuk mengabaikan proxy sistem yang mungkin mati
        with httpx.Client(trust_env=False, timeout=20.0) as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
            response = client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        titles = re.findall(r'<h2 class="result__title">.*?<a[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        
        results = []
        for i in range(min(len(titles), len(snippets), 7)):
            t = re.sub(r'<[^>]+>', '', titles[i]).strip()
            s = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            if t and s:
                results.append(f"### {t}\n{s}")
            
        if not results:
            # Fallback if the standard regex fails (DDG sometimes changes classes)
            if "ddg-captcha" in html.lower():
                return {"status": "error", "message": "Pencarian diblokir oleh Captcha DuckDuckGo. Coba ganti query atau tunggu sebentar."}
            return {"status": "success", "data": "Tidak ada hasil ditemukan. Coba gunakan kata kunci yang lebih umum."}
            
        return {"status": "success", "data": "\n\n".join(results)}
    except Exception as e:
        Logger.debug(f"Search failed: {str(e)}")
        return {"status": "error", "message": f"Koneksi Search Refused/Gagal: {str(e)}"}
