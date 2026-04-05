import sys
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Label
from textual.containers import VerticalScroll
from textual import events, work
from textual.reactive import reactive

from clients.universal_client import UniversalClient
from core.orchestrator import Orchestrator
from core.logger import Logger
from core.config import Config
from rich.text import Text
from rich.markup import render

class ChatMessage(Static):
    def __init__(self, content: str | Text, role: str):
        super().__init__(content)
        self.add_class(f"-{role}")

class ChatArea(VerticalScroll):
    pass

class ActivityMonitor(Static):
    SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self):
        super().__init__("", id="activity-monitor")
        self._idx = 0
        self._msg = ""
        self._timer = None

    def start(self, msg: str = "Zephyr sedang berpikir..."):
        self._msg = msg
        self._tick()
        if self._timer is None:
            self._timer = self.set_interval(0.08, self._tick)

    def set_message(self, msg: str):
        self._msg = msg

    def stop(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._msg = ""
        self.update("")
        self._idx = 0

    def _tick(self):
        if not self._msg:
            return
        char = self.SPINNER[self._idx % len(self.SPINNER)]
        self.update(f"[bold #89b4fa]{char}[/bold #89b4fa] {self._msg}")
        self._idx += 1

class ReasoningBox(Static):
    """Widget untuk menampilkan 'Thought' AI secara real-time."""
    content = reactive("")

    def __init__(self):
        super().__init__("")
        self.add_class("reasoning-box")
        self.content = ""
        self.visible = False

    def watch_content(self, content: str):
        content_stripped = content.strip()
        if content_stripped:
            self.set_class(True, "-visible")
            clean = content_stripped.replace("<thought>", "").replace("</thought>", "").strip()
            self.update(f"[bold #fab387]ANALISIS ZEPHYR:[/bold #fab387]\n[italic #9399b2]{clean}[/italic #9399b2]")
        else:
            self.set_class(False, "-visible")
            self.update("")
            self.display = False # Paksa sembunyi total

class DeepSeekApp(App):
    current_model = reactive(Config.DEFAULT_MODEL)
    is_selecting = reactive(True)
    is_computing = reactive(False)
    custom_status = reactive("")
    
    models_list = []

    CSS = """
    Screen {
        background: #0d0d12;
    }
    #top-header {
        width: 100%;
        padding: 1 2;
        color: #89b4fa;
        text-style: bold;
        background: #0d0d12;
        border-bottom: solid #1e1e2e;
    }
    #status-bar {
        width: 100%;
        padding: 0 2;
        height: 1;
        color: #9399b2;
        background: #0d0d12;
        text-style: italic;
    }
    Input {
        dock: bottom;
        margin: 0;
        padding: 0 1;
        border: none;
        border-top: solid #1e1e2e;
        background: #0d0d12;
        color: #cdd6f4;
    }
    Input:focus {
        border-top: solid #89b4fa;
    }
    ChatArea {
        height: 1fr;
        padding: 0 1 3 1;
        scrollbar-gutter: stable;
    }
    ChatMessage {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0 2;
        border-left: solid #313244;
        background: #181825;
    }
    ChatMessage.-user {
        background: #1e1e2e;
        color: #cdd6f4;
        border-left: solid #89b4fa;
        margin-top: 1;
        padding: 1 2;
    }
    ChatMessage.-ai {
        background: transparent;
        color: #bac2de;
        border: none;
        padding: 0 2;
        margin-top: 1;
    }
    ChatMessage.-system {
        background: transparent;
        border: none;
        color: #6c7086;
        padding: 0 1;
        margin: 0;
        text-style: italic;
    }
    #activity-monitor {
        width: 100%;
        height: auto;
        min-height: 1;
        padding: 0 2;
        color: #89b4fa;
        background: #11111b;
        text-style: italic;
        border-top: solid #1e1e2e;
    }
    .reasoning-box {
        display: none;
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0 2;
        background: transparent;
        color: #9399b2;
        border: none;
    }
    .reasoning-box.-visible {
        display: block;
        padding: 1 2;
        margin-top: 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.orchestrator = None
        self.client = None
        
    def compose(self) -> ComposeResult:
        yield Label(" Zephyr 2026.04 - Agentic Mode Active.", id="top-header")
        yield Label(f" connected | idle | model: {Config.DEFAULT_MODEL}", id="status-bar")
        yield ChatArea(id="chat-area")
        yield ActivityMonitor()
        yield Input(id="user-input", placeholder="Pilih [1-4] atau ENTER untuk Default...")

    def update_status(self):
        try:
            bar = self.query_one("#status-bar", Label)
            state = "BUSY" if self.is_computing else "IDLE"
            bar.update(f" CONNECTED | {state} | Model: {self.current_model}")
            
            monitor = self.query_one(ActivityMonitor)
            if self.is_computing:
                monitor.start("Zephyr sedang berpikir...")
            else:
                monitor.stop()
        except: pass

    def on_mount(self) -> None:
        Logger.set_callback(self.add_ai_message)
        Logger.set_info_callback(self.update_info)
        
        chat = self.query_one("#chat-area", ChatArea)
        
        # Cek apakah user punya MODEL_MAPPING di config.json
        if Config.MODEL_MAPPING:
            # User sudah konfigurasi provider — tampilkan menu
            lines = ["[bold #89b4fa]ZEPHYR HYBRID[/bold #89b4fa]", "Provider Selection:", ""]
            for key in sorted(Config.MODEL_MAPPING.keys()):
                label = Config.MODEL_LABELS.get(key, Config.MODEL_MAPPING[key])
                model = Config.MODEL_MAPPING[key]
                color = ["#a6e3a1", "#f9e2af", "#89b4fa", "#94e2d5", "#cba6f7"][int(key)-1 if key.isdigit() and 1<=int(key)<=5 else 0]
                lines.append(f"{key}. [bold {color}]{label}[/bold {color}] ({model})")
            
            if Config.DEFAULT_MODEL:
                lines.append("")
                lines.append(f"[italic #9399b2]Ketik nomor atau tekan ENTER untuk Default ({Config.DEFAULT_MODEL})[/italic #9399b2]")
            else:
                lines.append("")
                lines.append("[italic #9399b2]Ketik nomor untuk memilih provider.[/italic #9399b2]")
            
            welcome_txt = "\n".join(lines)
            chat.mount(ChatMessage(render(welcome_txt), "system"))
        elif Config.DEFAULT_MODEL:
            # Tidak ada menu, tapi ada DEFAULT_MODEL — langsung konek
            self._init_session(Config.DEFAULT_MODEL)
        else:
            # Tidak ada config sama sekali
            chat.mount(ChatMessage(render("[bold #f38ba8]ERROR: Tidak ada model yang dikonfigurasi.[/bold #f38ba8]\nSilakan isi DEFAULT_MODEL dan/atau MODEL_MAPPING di config.json Anda."), "system"))

    def _finalize_setup(self, choice):
        mapping = Config.MODEL_MAPPING
        model = mapping.get(choice, Config.DEFAULT_MODEL)
        if model:
            self._init_session(model)
        else:
            self.add_ai_message("[ERROR] Nomor tersebut tidak dikonfigurasi dan DEFAULT_MODEL kosong.")

    def _finalize_default(self):
        if Config.DEFAULT_MODEL:
            self._init_session(Config.DEFAULT_MODEL)
        else:
            self.add_ai_message("[ERROR] DEFAULT_MODEL tidak diisi di config.json.")

    def _init_session(self, model):
        if not model:
            self.add_ai_message("[ERROR] Model tidak ditemukan. Isi config.json Anda.")
            return
            
        self.current_model = model
        try:
            self.client = UniversalClient()
            self.client.active_model = self.current_model
            self.orchestrator = Orchestrator(self.client)
            self.is_selecting = False
            self.update_status()
            
            inp = self.query_one("#user-input", Input)
            inp.placeholder = "Ketik perintah proyek..."
            
            chat = self.query_one("#chat-area", ChatArea)
            msg = Text.from_markup(f"[SYSTEM] Session Active: [bold #a6e3a1]{model}[/bold #a6e3a1]")
            chat.mount(ChatMessage(msg, "system"))
        except Exception as e:
            self.add_ai_message(f"Fatal Error: {e}")

    def update_info(self, msg: str):
        # Redirect progress to ActivityMonitor, but mount ERRORS and CONFIG to chat
        try:
            if msg.startswith("[ERROR]") or msg.startswith("[CONFIG]"):
                chat = self.query_one("#chat-area", ChatArea)
                prefix = "[ERROR] " if msg.startswith("[ERROR]") else "[CONFIG] "
                color = "#f38ba8" if msg.startswith("[ERROR]") else "#fab387"
                
                content = msg[len(prefix):].strip()
                txt = Text.assemble(Text.from_markup(f"[bold {color}]{prefix}[/bold {color}] "), Text(content))
                chat.mount(ChatMessage(txt, "system"))
                chat.scroll_end(animate=False)
            else:
                monitor = self.query_one(ActivityMonitor)
                monitor.set_message(msg)
        except:
            pass

    def add_ai_message(self, text: str):
        import re
        chat = self.query_one("#chat-area", ChatArea)
        
        # UI Safety Net: Bersihkan tag sisa (thought/action) yang mungkin lolos
        # Mendukung multiline (?s), case-insensitive (?i), dan unclosed tags (|$ atau .*?)
        clean_text = re.sub(r"(?si)<thought>.*?(?:</thought>|$)", "", text).strip()
        clean_text = re.sub(r"(?si)<action>.*?(?:</action>|$)", "", clean_text).strip()
        
        if clean_text:
            chat.mount(ChatMessage(Text(clean_text), "ai"))
            chat.scroll_end(animate=False)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text and not self.is_selecting: return
            
        inp = self.query_one("#user-input", Input)
        inp.value = ""
        
        if self.is_selecting:
            if user_text in ["1", "2", "3", "4", "5"]:
                self._finalize_setup(user_text)
            elif user_text == "":
                self._finalize_default()
            else:
                self.add_ai_message("[System] Masukkan 1-5 atau ENTER.")
            return

        chat = self.query_one("#chat-area", ChatArea)
        chat.mount(ChatMessage(Text(user_text), "user"))
        chat.scroll_end()
        
        if user_text.lower() in ["/clear", "/reset"]:
            self.orchestrator.history = []
            if os.path.exists("sessions/current_session.json"):
                os.remove("sessions/current_session.json")
            self.add_ai_message("[System] Memori sesi telah dihapus. Mulai percakapan baru.")
            return
        
        self.is_computing = True
        self.update_status()
        self.run_orchestrator(user_text)

    @work
    async def run_orchestrator(self, user_text: str):
        chat = self.query_one("#chat-area", ChatArea)
        reasoning = None
        
        try:
            async for event in self.orchestrator.run(user_text):
                ev_type = event.get("type")
                
                if ev_type == "thought":
                    if reasoning is None:
                        reasoning = ReasoningBox()
                        chat.mount(reasoning)
                        chat.scroll_end()
                    reasoning.content = event.get("content", "")
                
                elif ev_type == "status":
                    self.update_info(event.get("content", ""))
                
                elif ev_type == "action":
                    tool = event.get("tool")
                    self.update_info(f"Menggunakan tool: {tool}...")
                
                elif ev_type == "observation":
                    tool = event.get("tool")
                    obs = event.get("content", "")
                    self.update_info(f"[OK] {tool} selesai.")
                    # PENTING: Dilarang menampilkan 'obs' ke add_ai_message di sini agar TUI bersih.

                elif ev_type == "error":
                    self.update_info(f"[ERROR] {event.get('content')}")
                
                elif ev_type == "final_answer":
                    # Biarkan reasoning.content tetap berisi agar terlihat di history turn ini
                    self.add_ai_message(event.get("content", ""))
                    
        except Exception as e:
            self.add_ai_message(f"[System] Crash: {str(e)}")
        finally:
            self.is_computing = False
            self.update_status()

if __name__ == "__main__":
    app = DeepSeekApp()
    app.run()