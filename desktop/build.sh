#!/usr/bin/env bash
# ============================================================
#  Gera o executável do Mapa de Carga Horária (Linux / macOS).
#  Requisitos: Python 3.10+ com tkinter.
#    - Ubuntu/Debian: sudo apt install python3-tk
#    - Fedora:        sudo dnf install python3-tkinter
#    - macOS:         tkinter já vem no Python do python.org
#  Resultado: dist/MapaCargaHoraria
# ============================================================
set -e
cd "$(dirname "$0")"

echo "[1/3] Instalando dependências de build..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "[2/3] Gerando executável com PyInstaller..."
python3 -m PyInstaller --noconfirm mapa.spec

echo "[3/3] Concluído!"
echo "Executável gerado em: dist/MapaCargaHoraria"
