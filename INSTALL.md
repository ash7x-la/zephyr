# Zephyr Agent Deployment Guide

Panduan instalasi cepat untuk menjalankan Zephyr di berbagai lingkungan (Linux, Termux, Windows WSL).

## 1. Persiapan Awal
Pastikan Anda memiliki Python 3.10 ke atas dan `pip` terinstall.

```bash
# Clone repository
git clone <repo-url>
cd deepseek_agent_assistant

# Buat virtual environment (Direkomendasikan)
python3 -m venv env
source env/bin/activate
```

## 2. Instalasi Dependensi
```bash
pip install -r requirements.txt

# Install Playwright Browser (Untuk Browser Tool)
playwright install chromium
```

## 3. Konfigurasi Environment
Salin file `.env.example` menjadi `.env` dan isi API Key Anda.
```bash
cp .env.example .env
nano .env
```

## 4. Menjalankan Zephyr
```bash
python3 main.py
```

## Tips Khusus Lingkungan

### A. Termux (Android)
Untuk menjalankan di Termux, Anda perlu menginstall Chromium secara manual:
```bash
pkg update && pkg upgrade
pkg install tur-repo
pkg install chromium
```
Zephyr akan otomatis mendeteksi path Chromium di Termux.

### B. DeepSeek-Free (Local Proxy)
Jika menggunakan opsi "Zephyr Free", pastikan Anda menjalankan proxy di background:
```bash
bash run-zephyr-free.sh
```

---
*Ready for Production.*
