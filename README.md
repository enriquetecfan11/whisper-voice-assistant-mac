# Whisper Voice Assistant para macOS

Asistente de voz **100% local** para macOS que transcribe tu voz en tiempo real usando [faster-whisper](https://github.com/SYSTRAN/faster-whisper) y ejecuta acciones nativas del sistema.

## Caracteristicas

- **100% local** - Sin conexion a internet, sin enviar datos a servidores externos
- **Transcripcion con Whisper** - Usa `faster-whisper` (optimizado para CPU y GPU)
- **Deteccion de hotword** - Activa el asistente diciendo "Jarvis" (via Porcupine)
- **Modo siempre escuchando** - Sin hotword, grabando continuamente
- **Acciones nativas de macOS**: captura de pantalla, notas de voz, busqueda web, abrir apps
- **Configurable** via `.env`
- **Soporte Apple Silicon y Intel**

## Estructura del proyecto

```
whisper-voice-assistant-mac/
|-- main.py              # Script principal del asistente
|-- actions.py           # Acciones del sistema
|-- config.py            # Configuracion centralizada
|-- requirements.txt     # Dependencias Python
|-- install.sh           # Script de instalacion automatica
|-- .env                 # Variables de entorno (creado en instalacion)
|-- .gitignore
```

## Instalacion rapida

```bash
# 1. Clonar el repositorio
git clone https://github.com/enriquetecfan11/whisper-voice-assistant-mac.git
cd whisper-voice-assistant-mac

# 2. Ejecutar el script de instalacion
bash install.sh
```

El script de instalacion hace automaticamente:
- Verifica Python 3.9+
- Instala Homebrew (si no esta)
- Instala PortAudio via Homebrew
- Crea un entorno virtual Python
- Instala todas las dependencias
- Crea el archivo `.env` de configuracion

## Instalacion manual

```bash
brew install portaudio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
source venv/bin/activate

# Modo siempre escuchando
python main.py

# Modo con hotword (requiere PORCUPINE_ACCESS_KEY en .env)
python main.py --hotword
```

## Comandos de voz

| Comando | Ejemplo | Accion |
|---------|---------|--------|
| `captura` / `screenshot` | "toma una captura" | Captura de pantalla en el Escritorio |
| `anota` / `apunta` | "anota comprar leche" | Guarda nota en `~/Documents/VoiceNotes/` |
| `busca` / `buscar` | "busca recetas veganas" | Abre DuckDuckGo con la busqueda |
| `abre` + app | "abre terminal" | Abre la aplicacion en macOS |

## Configuracion (.env)

```env
WHISPER_MODEL=base          # tiny, base, small, medium, large
WHISPER_LANGUAGE=es
WHISPER_DEVICE=cpu          # cpu o cuda
WHISPER_COMPUTE_TYPE=int8
PORCUPINE_ACCESS_KEY=       # Gratis en https://console.picovoice.ai/
HOTWORD=jarvis
```

## Requisitos

- macOS 12+
- Python 3.9+
- Homebrew
- Microfono
- Para hotword: cuenta gratuita en [Picovoice Console](https://console.picovoice.ai/)

## Licencia

MIT
