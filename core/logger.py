class Logger:
    _callback = None
    _info_cb = None
    
    @classmethod
    def set_callback(cls, cb):
        cls._callback = cb

    @classmethod
    def set_info_callback(cls, cb):
        cls._info_cb = cb
        
    @staticmethod
    def debug(msg):
        """Hanya untuk terminal/internal, tidak muncul di TUI secara default."""
        print(f"[DEBUG] {msg}")
            
    @staticmethod
    def info(msg):
        """Muncul di TUI sebagai pesan sistem resmi."""
        if Logger._info_cb:
            Logger._info_cb(msg)
        else:
            print(f"[INFO] {msg}")

    @staticmethod
    def warning(msg):
        """Log peringatan, muncul di TUI."""
        if Logger._info_cb:
            Logger._info_cb(f"[WARNING] {msg}")
        else:
            print(f"[WARNING] {msg}")
            
    @staticmethod
    def error(msg):
        if Logger._info_cb:
            Logger._info_cb(f"[ERROR] {msg}")
        else:
            print(f"[ERROR] {msg}")
            
    @staticmethod
    def ai_reply(msg):
        if Logger._callback:
            Logger._callback(msg)
        else:
            print(f"\nZephyr:\n{msg}\n")
