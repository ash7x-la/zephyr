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
        if content:
            self.visible = True
            clean = content.replace("<thought>", "").replace("</thought>", "").strip()
            self.update(f"[bold #fab387]ANALISIS ZEPHYR:[/bold #fab387]\n[italic #9399b2]{clean}[/italic #9399b2]")
        else:
            self.visible = False
            self.update("")

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
        padding: 1 2;
        scrollbar-gutter: stable;
    }
    ChatMessage {
        width: 100%;
        height: auto;
        margin: 1 0;
        padding: 1 2;
        border-left: solid #313244;
        background: #181825;
    }
    ChatMessage.-user {
        background: #1e1e2e;
        color: #cdd6f4;
        border-left: solid #89b4fa;
    }
    ChatMessage.-ai {
        background: #11111b;
        color: #bac2de;
        border-left: solid #a6e3a1;
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
        width: 100%;
        height: auto;
        min-height: 2;
        max-height: 20;
        margin: 0 0 1 0;
        padding: 1 2;
        border-right: dashed #fab387;
        border-left: dashed #fab387;
        background: #1e1e2e;
        color: #9399b2;
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
        welcome_txt = f"""[bold #89b4fa]ZEPHYR HYBRID[/bold #89b4fa]
Provider Selection:

1. [bold #a6e3a1]Gemini CLI[/bold #a6e3a1] (`gemini` lokal)
2. [bold #f9e2af]Gemini SDK[/bold #f9e2af] (Official API)
3. [bold #89b4fa]OpenRouter Hub[/bold #89b4fa] (Qwen/DeepSeek/GPT-4)
4. [bold #94e2d5]Claude Direct[/bold #94e2d5] (Anthropic API)
5. [bold #cba6f7]Zephyr Free[/bold #cba6f7] (Local Reverse Proxy)

[italic #9399b2]Ketik nomor atau tekan ENTER untuk Default ({Config.DEFAULT_MODEL})[/italic #9399b2]"""
        chat.mount(ChatMessage(render(welcome_txt), "system"))

    def _finalize_setup(self, choice):
        mapping = {
            "1": "google/gemini-cli-proxy",
            "2": "google/gemini-2.0-flash-001",
            "3": "qwen/qwen3.6-plus:free",
            "4": "anthropic/claude-3.5-sonnet",
            "5": "deepseek-free/deepseek-chat"
        }
        model = mapping.get(choice, Config.DEFAULT_MODEL)
        self._init_session(model)

    def _finalize_default(self):
        self._init_session(Config.DEFAULT_MODEL)

    def _init_session(self, model):
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
        clean_text = re.sub(r"<?thought>?(.*?)</?thought>?", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        clean_text = re.sub(r"<?action>?(.*?)</?action>?", "", clean_text, flags=re.DOTALL | re.IGNORECASE).strip()
        
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
        reasoning = ReasoningBox()
        chat.mount(reasoning)
        chat.scroll_end()
        
        # Set initial content
        reasoning.content = "Sedang menganalisis permintaan..."
        
        try:
            async for event in self.orchestrator.run(user_text):
                ev_type = event.get("type")
                
                if ev_type == "thought":
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
                    # Tetap simpan reasoning sampai ada input baru jika mau,
                    # atau sembunyikan setelah ada jeda kecil.
                    # Tapi untuk otonomi, lebih baik disembunyikan saat jawaban muncul.
                    reasoning.content = "" # Sembunyikan
                    self.add_ai_message(event.get("content", ""))
                    
        except Exception as e:
            self.add_ai_message(f"[System] Crash: {str(e)}")
        finally:
            self.is_computing = False
            reasoning.content = ""
            self.update_status()

if __name__ == "__main__":
    app = DeepSeekApp()
    app.run()