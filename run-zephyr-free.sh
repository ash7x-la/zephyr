#!/bin/bash
# Helper script to run DeepSeek-Free-API for Antigravity Hybrid (Auto-Detect Version)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TARGET_NAME="DeepSeek-Free-API-master"

echo "🔍 Mencari direktori proxy $TARGET_NAME..."

# List lokasi pencarian dari yang paling mungkin (Child, Sibling, Cousin)
SEARCH_PATHS=(
    "$SCRIPT_DIR/$TARGET_NAME"
    "$SCRIPT_DIR/../$TARGET_NAME"
    "$SCRIPT_DIR/../../$TARGET_NAME"
    "$HOME/Documents/kerja/$TARGET_NAME"
    "$HOME/Documents/$TARGET_NAME"
    "$HOME/$TARGET_NAME"
)

PROXY_DIR=""
for p in "${SEARCH_PATHS[@]}"; do
    if [ -d "$p" ]; then
        PROXY_DIR="$p"
        echo "✅ Ketemu di: $PROXY_DIR"
        break
    fi
done

# Fallback: Pencarian mendalam jika belum ketemu
if [ -z "$PROXY_DIR" ]; then
    echo "⚠️ Lokasi standar tidak ditemukan. Sedang mencari di folder Documents (maxdepth 3)..."
    PROXY_DIR=$(find "$HOME/Documents" -maxdepth 3 -type d -name "$TARGET_NAME" -print -quit 2>/dev/null)
    
    if [ -n "$PROXY_DIR" ]; then
        echo "✅ Ketemu lewat pencarian: $PROXY_DIR"
    fi
fi

if [ -z "$PROXY_DIR" ]; then
    echo "❌ ERROR: $TARGET_NAME tidak ditemukan di mana pun."
    echo "Pastikan folder proxy ada dan beri nama '$TARGET_NAME'."
    exit 1
fi

cd "$PROXY_DIR"

echo "📦 Memeriksa dependensi..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies (npm install)..."
    npm install
fi

echo "🔨 Building project (npm run build)..."
npm run build

echo "🚀 Menjalankan DeepSeek-Free-API pada port 8000..."
npm run start
