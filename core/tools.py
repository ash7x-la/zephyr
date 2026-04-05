TOOL_SCHEMAS = {
    "list_dir": {
        "description": "Melihat daftar file dan folder di direktori kerja.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relatif direktori yang ingin dilihat (default: '.')"}
            }
        }
    },
    "read_file": {
        "description": "Membaca isi teks dari sebuah file lokal.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relatif file yang ingin dibaca"}
            },
            "required": ["path"]
        }
    },
    "write_file": {
        "description": "Menulis atau membuat file baru dengan konten tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relatif file tujuan"},
                "content": {"type": "string", "description": "Isi konten yang akan ditulis"}
            },
            "required": ["path", "content"]
        }
    },
    "run_command": {
        "description": "Mengeksekusi perintah terminal bash di lingkungan lokal.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Perintah bash yang akan dijalankan"}
            },
            "required": ["command"]
        }
    },
    "browser_test": {
        "description": "Membuka URL di browser untuk navigasi, testing UI, dan debugging (Logs/DOM). Mendukung aksi interaktif.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL atau path file lokal (misal: file:///path/to/index.html)"},
                "actions": {
                    "type": "array",
                    "description": "Daftar aksi interaktif (opsional)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["click", "fill", "press", "wait"], "description": "Jenis aksi UI"},
                            "selector": {"type": "string", "description": "CSS selector elemen target"},
                            "value": {"type": "string", "description": "Nilai input (untuk fill) atau tombol (untuk press)"}
                        },
                        "required": ["type", "selector"]
                    }
                },
                "get_html": {"type": "boolean", "description": "Set True untuk mengambil kode HTML elemen (Copy UI)"},
                "html_selector": {"type": "string", "description": "CSS selector elemen yang ingin dicopy HTML-nya (default: body)"}
            },
            "required": ["url"]
        }
    },
    "search_browser": {
        "description": "Mencari informasi, referensi UI/kode, atau error debugging di internet menggunakan DuckDuckGo.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Kata kunci pencarian"}
            },
            "required": ["query"]
        }
    }
}
