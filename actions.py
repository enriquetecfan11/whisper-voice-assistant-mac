import os
import re
import subprocess
import datetime
import logging
import urllib.parse
from config import SCREENSHOT_DIR, NOTES_DIR

logger = logging.getLogger(__name__)

# Mapa completo de apps: palabras clave -> nombre real en macOS
APP_MAP = {
    # Navegadores
    "safari": "Safari",
    "chrome": "Google Chrome",
    "firefox": "Firefox",
    "brave": "Brave Browser",
    # Productividad
    "notas": "Notes",
    "notes": "Notes",
    "nota": "Notes",
    "calendario": "Calendar",
    "calendar": "Calendar",
    "recordatorios": "Reminders",
    "reminders": "Reminders",
    "mail": "Mail",
    "correo": "Mail",
    "mensajes": "Messages",
    "messages": "Messages",
    "facetime": "FaceTime",
    # Desarrollo
    "terminal": "Terminal",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "visual studio": "Visual Studio Code",
    "xcode": "Xcode",
    "cursor": "Cursor",
    # Multimedia
    "spotify": "Spotify",
    "musica": "Music",
    "music": "Music",
    "podcasts": "Podcasts",
    "fotos": "Photos",
    "photos": "Photos",
    "quicktime": "QuickTime Player",
    # Sistema
    "finder": "Finder",
    "preferencias": "System Preferences",
    "ajustes": "System Settings",
    "system settings": "System Settings",
    "monitor de actividad": "Activity Monitor",
    "activity monitor": "Activity Monitor",
    # Otros
    "slack": "Slack",
    "discord": "Discord",
    "zoom": "Zoom",
    "notion": "Notion",
    "obsidian": "Obsidian",
    "figma": "Figma",
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
}


def take_screenshot() -> str:
    """Hace una captura de pantalla y la guarda en el Escritorio."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SCREENSHOT_DIR, f"captura_{timestamp}.png")
    result = subprocess.run(["screencapture", "-x", filename], capture_output=True)
    if result.returncode == 0:
        logger.info(f"Captura guardada en: {filename}")
        return f"Captura guardada en: {filename}"
    else:
        logger.error("Error al hacer captura de pantalla")
        return "Error al hacer la captura"


def save_note(text: str) -> str:
    """Guarda una nota de voz en un archivo de texto."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(NOTES_DIR, f"nota_{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(text)
    logger.info(f"Nota guardada en: {filename}")
    return f"Nota guardada en: {filename}"


def web_search(query: str) -> str:
    """Abre el navegador con una busqueda en DuckDuckGo."""
    encoded = urllib.parse.quote(query)
    url = f"https://duckduckgo.com/?q={encoded}"
    subprocess.run(["open", url])
    return f"Buscando: {query}"


def open_app(app_name: str) -> str:
    """Abre una aplicacion de macOS por nombre."""
    result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
    if result.returncode == 0:
        logger.info(f"Abierta app: {app_name}")
        return f"Abriendo {app_name}"
    else:
        logger.warning(f"App no encontrada: {app_name}")
        return f"No encontre la aplicacion: {app_name}"


def _extract_app_name(text: str) -> str:
    """Extrae el nombre de la app del texto usando el APP_MAP."""
    text_lower = text.lower()

    # Buscar coincidencia exacta en el mapa (de la mas larga a la mas corta)
    for key in sorted(APP_MAP.keys(), key=len, reverse=True):
        if key in text_lower:
            return APP_MAP[key]

    # Fallback: intentar extraer la ultima palabra/frase tras verbos de apertura
    match = re.search(
        r'(?:abre|abrir|lanza|lanzar|inicia|iniciar|abre la aplicacion de|abre la app de)\s+(.+)',
        text_lower
    )
    if match:
        app_raw = match.group(1).strip()
        # Limpiar articulos y preposiciones
        for noise in ["la aplicacion de", "la app de", "la", "el", "de"]:
            app_raw = app_raw.replace(noise, "").strip()
        return app_raw.title()

    return ""


def process_command(text: str) -> str:
    """
    Detecta el tipo de comando y lo ejecuta.
    Retorna string con el resultado de la accion.
    """
    text_lower = text.lower().strip()
    logger.info(f"Procesando comando: {text_lower}")

    # Captura de pantalla
    if any(w in text_lower for w in ["captura", "screenshot", "foto de pantalla"]):
        return take_screenshot()

    # Guardar nota
    if any(w in text_lower for w in ["anota", "apunta", "guarda una nota"]):
        note_text = text_lower
        for w in ["anota que", "anota", "apunta que", "apunta", "guarda una nota de", "guarda una nota"]:
            note_text = note_text.replace(w, "").strip()
        return save_note(note_text or text)

    # Busqueda web
    if any(w in text_lower for w in ["busca", "buscar", "search", "googlea"]):
        query = text_lower
        for w in ["busca en internet", "busca", "buscar", "search", "googlea"]:
            query = query.replace(w, "").strip()
        return web_search(query or text)

    # Abrir aplicacion
    if any(w in text_lower for w in ["abre", "abrir", "lanza", "inicia", "abre la", "abrir la"]):
        app_name = _extract_app_name(text)
        if app_name:
            return open_app(app_name)
        return "No entendi que aplicacion quieres abrir."

    return f"Comando no reconocido: '{text}'"
