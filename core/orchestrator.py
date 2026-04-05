import json
import re
import platform
import datetime
import os
import asyncio
from core.tools import TOOL_SCHEMAS
from utils.system_bridge import list_dir, read_file, write_file, run_command, search_browser
from core.browser_tool import run_browser_test
from core.logger import Logger

class Orchestrator:
    def __init__(self, client):
        self.client = client
        self.available_tools = {
            "list_dir": list_dir,
            "read_file": read_file,
            "write_file": write_file,
            "run_command": run_command,
            "browser_test": run_browser_test,
            "search_browser": search_browser
        }

        self.history: list[dict[str, str]] = []
        self._load_session()
        
    def _load_session(self):
        try:
            if os.path.exists("sessions/current_session.json"):
                with open("sessions/current_session.json", "r") as f:
                    self.history = json.load(f)
                Logger.debug("[SYSTEM] Memori sesi sebelumnya berhasil dimuat.")
        except Exception as e:
            Logger.debug(f"[SYSTEM] Gagal memuat sesi: {e}")

    def _save_session(self):
        try:
            os.makedirs("sessions", exist_ok=True)
            with open("sessions/current_session.json", "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            Logger.debug(f"[SYSTEM] Gagal menyimpan sesi: {e}")

    def _resilient_json_parse(self, raw_action):
        """Mencoba memperbaiki JSON LLM yang umum (truncation, invalid escapes)."""
        # Find the JSON part
        json_search = re.search(r"(\{.*\})", raw_action, re.DOTALL)
        if json_search:
            s = json_search.group(1).strip()
        else:
            s = raw_action.strip()

        # Try direct parse
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            try:
                # brute force attempt to fix truncation (string missing quote and brace)
                return json.loads(s + '"}')
            except:
                try:
                    # just missing brace
                    return json.loads(s + '}')
                except:
                    # missing two braces
                    try:
                        return json.loads(s + '}}')
                    except:
                        pass
        
        # Try fixing common backslash errors (if not already fixed)
        # Replacing raw \ with \\ unless followed by valid chars
        s = re.sub(r'\\(?![\\"/bfnrtu])', r'\\\\', s)
        try:
            return json.loads(s)
        except:
            return None
        
    def _load_identity(self):
        """Membaca file SOUL, MEMORY, dan USER untuk konteks jangka panjang."""
        paths = ["SOUL.md", "MEMORY.md", "USER.md"]
        context = ""
        for p in paths:
            if os.path.exists(p):
                with open(p, "r") as f:
                    context += f"\n### {p}\n" + f.read() + "\n"
        return context

    def _log_transaction(self, request, result):
        """Mencatat aktivitas harian ke folder memory/."""
        os.makedirs("memory", exist_ok=True)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        path = f"memory/{today}.md"
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        log_entry = f"## [{timestamp}] Task Execution\n"
        log_entry += f"- **Request:** {request}\n"
        log_entry += f"- **Status:** {result.get('status')}\n"
        if result.get('tools'):
            log_entry += f"- **Tools Used:** {', '.join(result['tools'])}\n"
        log_entry += "\n---\n"
        
        with open(path, "a") as f:
            f.write(log_entry)

    def _build_metadata(self):
        os_name = platform.system()
        current_time = datetime.datetime.now().strftime("%A, %B %d, %Y - %H:%M:%S")
        cwd = os.getcwd()
        return f"\n<ADDITIONAL_METADATA>\nLocal Time: {current_time}\nUser OS: {os_name}\nWorking Dir: {cwd}\n</ADDITIONAL_METADATA>"

    async def run(self, user_request, is_retry=False):
        if not is_retry:
            self._sanitize_history()
            self._trim_history()
        
        meta = self._build_metadata()
        identity = self._load_identity()
        
        system_prompt = f"""Kamu adalah Autonomous Agentic AI (Zephyr).
Kamu memiliki akses ke sistem lokal melalui tools. Gunakan pola ReAct (Thought -> Action -> Observation).

{identity}

TOOLS TERSEDIA:
{json.dumps(TOOL_SCHEMAS, indent=2)}

ATURAN REAKT (WAJIB):
1. Setiap langkah, keluarkan <thought>...</thought> berisi alasanmu.
2. Jika butuh tool, keluarkan <action>{{"tool_code": "nama_tool", "parameters": {{...}}}}</action>.
3. **MAX 50 BARIS**: DILARANG menulis >50 baris kode dalam satu <action>. Jika perlu, bagi menjadi beberapa file atau beberapa tahap pemanggilan.
4. **JSON VALID**: Gunakan double quotes. Escape backslashes (`\\`) dan quotes (`\"`) di dalam string parameters.
8. **SACRED PORT 8000 (DILARANG KERAS)**: Kamu DILARANG menghentikan proses pada port 8000 menggunakan `kill`, `fuser`, atau `pkill` apa pun alasannya. Ini adalah jantung koneksi Anda; jika dimatikan, Anda akan kehilangan kesadaran (timeout).
9. **COPY UI (NEW)**: Kamu bisa meniru UI/UX website apapun dengan menggunakan `browser_test(url, get_html=True)`. Ambil struktur HTML-nya, pelajari CSS-nya, dan terapkan ke project lokal.
10. **MISI OTONOM (100% SELF-DRIVEN)**: Jangan bertanya "apakah boleh", langsung eksekusi. Jangan berhenti sebelum ada bukti (logs/screenshots) bahwa fitur sudah 100% stabil.
11. **LANGUAGE & TECH**: Gunakan Bahasa Indonesia (Chat) & Inggris (Code). **DILARANG KERAS** menggunakan Bahasa Mandarin. Gunakan React/Vite/Tailwind untuk web tasks.

{meta}"""

        if not self.history:
            self.history.append({"role": "system", "content": system_prompt})
        else:
            self.history[0] = {"role": "system", "content": system_prompt}
        
        if not is_retry:
            # Paksa ReAct dengan pengingat di akhir pesan user
            prompt_with_force = user_request + "\n\n(IMPORTANT: Start your response with <thought> explaining your plan.)"
            self.history.append({"role": "user", "content": prompt_with_force})
        
        self._trim_history()

        max_iterations = 1000 
        
        for i in range(max_iterations):
            yield {"type": "status", "content": f"Iterasi {i+1}..."}
            self._trim_history()
            
            full_response = ""
            thought_buffer = ""
            is_thinking = False
            
            # Streaming from Client
            async for chunk in self.client.chat_stream(self.history):
                full_response += chunk
                
                # Live Reasoning Detection (Case-Insensitive)
                if not is_thinking:
                    # Look for <thought> or Thought: or reasoning start
                    if re.search(r"<thought>|thought:", full_response, re.I):
                        is_thinking = True
                
                # Real-time Streaming for UI (Directly showing AI words)
                display_content = full_response
                # Hentikan tampilan di box analisis jika sudah masuk ke <action> atau <final_answer>
                stop_match = re.search(r"<action|<final_answer|Action:", display_content, re.I)
                if stop_match:
                    display_content = display_content[:stop_match.start()]

                display_content = re.sub(r"<thought>|</thought>|thought:", "", display_content, flags=re.I | re.DOTALL).strip()
                # Hapus blok <observation> jika ada bocor ke output AI
                display_content = re.sub(r"<observation>.*?</observation>", "", display_content, flags=re.I | re.DOTALL).strip()
                display_content = re.sub(r"observation:\s*\{.*?\}", "", display_content, flags=re.I | re.DOTALL).strip()
                
                if display_content != thought_buffer:
                    thought_buffer = display_content
                    yield {"type": "thought", "content": thought_buffer}

            if not full_response:
                if not is_retry:
                    Logger.info("AI return empty response. Retrying with trimmed history...")
                    # Lebih agresif memotong history sebelum retry
                    self._trim_history(max_chars=15000)
                    async for ev in self.run(user_request, is_retry=True):
                        yield ev
                    return
                else:
                    yield {"type": "error", "content": "AI return empty response after retry. Possible session timeout or API error."}
                    break

            # End of streaming for this turn
            response = full_response
            
            # Cek jika butuh tool (Action)
            action_match = re.search(r"<action>(.*?)</action>", response, re.DOTALL | re.IGNORECASE)
            if not action_match:
                action_match = re.search(r"<action>(.*)", response, re.DOTALL | re.IGNORECASE)
                
            if action_match:
                yield {"type": "status", "content": "Executing tool..."}
                try:
                    raw_action = action_match.group(1).strip()
                    action_json = self._resilient_json_parse(raw_action)
                    
                    if not action_json:
                        raise ValueError("JSON format error.")
                        
                    tool_name = action_json.get("tool_code") or action_json.get("tool")
                    params = action_json.get("parameters", {})
                    
                    if tool_name in self.available_tools:
                        yield {"type": "action", "tool": tool_name, "params": params}
                        
                        # RUN THE TOOL
                        func = self.available_tools[tool_name]
                        if asyncio.iscoroutinefunction(func):
                            observation = await func(**params)
                        else:
                            observation = func(**params)
                        
                        obs_str = json.dumps(observation, indent=2)
                        
                        # Anti-Injection Sanitization
                        for tag in ["<thought>", "</thought>", "<action>", "</action>"]:
                            obs_str = obs_str.replace(tag, f"[STRIPPED_{tag.strip('<>/').upper()}]")
                        
                        # yield observation specifically for UI status monitoring, not for chat area
                        yield {"type": "observation", "tool": tool_name, "content": obs_str}
                        
                        if response:
                            self.history.append({"role": "assistant", "content": response})
                        self.history.append({"role": "user", "content": f"<observation>{obs_str}</observation>"})
                        continue
                except Exception as e:
                    err_msg = f"Tool Error: {str(e)}"
                    self.history.append({"role": "user", "content": f"<observation>{err_msg}</observation>"})
                    yield {"type": "error", "content": err_msg}
                    continue

            # Jika tidak ada action, berarti tugas selesai
            yield {"type": "final_answer", "content": response}
            if response:
                self.history.append({"role": "assistant", "content": response})
            self._save_session()
            break

    def _trim_history(self, max_msgs=16, max_chars=30000):
        """Memastikan history tetap dalam batas konteks model (Limit pesan & karakter)"""
        self._sanitize_history()
        
        # 1. Limit message count (Default 16)
        if len(self.history) > max_msgs:
            system_msg = self.history[0]
            self.history = [system_msg] + self.history[-(max_msgs-1):]
            Logger.debug(f"History di-trim berdasarkan jumlah pesan (Max {max_msgs}).")

        # 2. Limit character total (Safety Limit for proxies)
        total_chars = sum(len(str(m.get("content", ""))) for m in self.history)
        if total_chars > max_chars:
            # Tetap simpan System Message
            system_msg = self.history[0]
            other_msgs = self.history[1:]
            
            # Buang pesan tertua (tapi bukan system) sampai di bawah limit
            while other_msgs and sum(len(str(m.get("content", ""))) for m in other_msgs) > (max_chars - 5000):
                other_msgs.pop(0)
            
            self.history = [system_msg] + other_msgs
            Logger.debug(f"History di-trim berdasarkan karakter (Limit {max_chars}).")

    def _sanitize_history(self):
        """Membersihkan history dari pesan kosong, rusak, atau DUPLIKAT."""
        if not self.history:
            return
        
        sanitized = []
        last_role = None
        last_content = None
        for msg in self.history:
            role = msg.get("role")
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                # Hindari pesan berturut-turut yang identik dari role yang sama (Duplikasi)
                if role == last_role and content == last_content:
                    continue
                sanitized.append(msg)
                last_role = role
                last_content = content

        self.history = sanitized
