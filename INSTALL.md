# Zephyr Agent Deployment Guide

Panduan instalasi Zephyr di berbagai lingkungan (Linux, Termux, Windows WSL).

## 1. Persiapan Awal
Pastikan Anda memiliki Python 3.10 ke atas.

```bash
# Clone repository
git clone https://github.com/ash7x-la/zephyr.git
cd zephyr

# Buat virtual environment (PENTING di Linux/WSL)
python3 -m venv env
source env/bin/activate
```

## 2. Instalasi Dependensi
```bash
pip install -r requirements.txt

# Setup Browser (Untuk fitur Webbrowsing)
playwright install chromium
```

## 3. Konfigurasi Environment
```bash
cp .env.example .env
nano .env # Isi API Key Anda di sini
```

## Tips Khusus Termux (Android)
Agar BrowserTool bisa jalan di Termux, lakukan langkah berikut:
1. `pkg update && pkg upgrade`
2. `pkg install tur-repo`
3. `pkg install chromium`
4. Jalankan Zephyr seperti biasa: `python main.py`

### B. DeepSeek-Free (Local Proxy)
Jika menggunakan opsi "Zephyr Free", pastikan Anda menjalankan proxy di background:
```bash
bash run-zephyr-free.sh
```

---
*Ready for Production.*
