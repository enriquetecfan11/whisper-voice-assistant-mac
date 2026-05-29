#!/bin/bash
# =================================================
# Script de instalación - Whisper Voice Assistant
# Compatible con macOS (Apple Silicon y Intel)
# =================================================

set -e

echo "================================================="
echo " Whisper Voice Assistant - Instalación"
echo "================================================="

# Verificar que estamos en macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "ERROR: Este script solo funciona en macOS"
    exit 1
fi

# Verificar Python 3.9+
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"
if python3 -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)"; then
    echo "Python $PYTHON_VERSION - OK"
else
    echo "ERROR: Se requiere Python 3.9 o superior. Tienes $PYTHON_VERSION"
    echo "Instala Python desde: https://www.python.org/downloads/"
    exit 1
fi

# Verificar Homebrew (necesario para portaudio)
if ! command -v brew &> /dev/null; then
    echo "Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew - OK"
fi

# Instalar PortAudio (requerido por PyAudio)
echo "Instalando PortAudio..."
brew install portaudio

# Crear entorno virtual
echo "Creando entorno virtual Python..."
python3 -m venv venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
echo "Instalando dependencias Python..."
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "Creando archivo .env de configuración..."
    cat > .env << 'EOF'
# Configuración de Whisper
WHISPER_MODEL=base
WHISPER_LANGUAGE=es
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# Configuración de Hotword (opcional)
# Obtén tu clave gratuita en: https://console.picovoice.ai/
PORCUPINE_ACCESS_KEY=
HOTWORD=jarvis

# Modo siempre escuchando (sin hotword)
ALWAYS_LISTEN=false

# Logging
LOG_LEVEL=INFO
LOG_TRANSCRIPTIONS=true
EOF
    echo "Archivo .env creado. Edita las variables si necesitas configurar el hotword."
else
    echo ".env ya existe, omitiendo creación."
fi

# Crear directorio de notas de voz
mkdir -p ~/Documents/VoiceNotes

echo ""
echo "================================================="
echo " Instalación completada!"
echo "================================================="
echo ""
echo "Para iniciar el asistente:"
echo "  source venv/bin/activate"
echo "  python main.py              # Siempre escuchando"
echo "  python main.py --hotword    # Activado por hotword"
echo ""
echo "Comandos de voz disponibles:"
echo "  'captura' / 'screenshot'    -> Captura de pantalla"
echo "  'anota' / 'apunta' + texto  -> Guardar nota"
echo "  'busca' + consulta          -> Buscar en DuckDuckGo"
echo "  'abre' + aplicación         -> Abrir app de macOS"
echo ""
