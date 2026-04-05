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
Pilih versi sesuai perangkat Anda:

### A. Versi PC / WSL (Full Experience)
```bash
pip install -r requirements-full.txt
playwright install chromium
```

### B. Versi Termux (Core Lite) - Tanpa BrowserTool
```bash
pip install -r requirements.txt
```

## 3. Konfigurasi Environment
```bash
cp .env.example .env
nano .env # Isi API Key Anda di sini
```

## Tips Khusus Termux (Android)
Agar Zephyr bisa jalan sempurna di Termux, lakukan langkah berikut:
1. `pkg update && pkg upgrade`
2. `pkg install rust clang binutils` (PENTING: Dibutuhkan untuk build library OpenAI/Pydantic)
3. `pkg install tur-repo`
4. `pkg install chromium`
5. Jalankan Zephyr seperti biasa: `python main.py`

## How to Update
Untuk memperbarui Zephyr ke versi terbaru:
```bash
git pull origin main
pip install -r requirements.txt
```

### B. DeepSeek-Free (Local Proxy)
Jika menggunakan opsi "Zephyr Free", pastikan Anda menjalankan proxy di background:
```bash
bash run-zephyr-free.sh
```

---
*Ready for Production.*
