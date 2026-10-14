#!/bin/bash
# 맥에서 PhotoSort.app 을 만든다. 결과: dist/PhotoSort.app
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -r requirements-build.txt
python3 -m PyInstaller --noconfirm --clean --windowed --name PhotoSort --icon assets/icon.icns \
  --collect-all tkinterdnd2 main.py
echo "완료: $(pwd)/dist/PhotoSort.app"
