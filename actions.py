import os
import subprocess
import datetime
import logging
from config import SCREENSHOT_DIR, NOTES_DIR

logger = logging.getLogger(__name__)


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
    """Abre el navegador con una búsqueda en DuckDuckGo."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"https://duckduckgo.com/?q={encoded}"
    subprocess.run(["open", url])
    logger.info(f"Búsqueda abierta: {query}")
    return f"Buscando: {query}"


def open_app(app_name: str) -> str:
    """Abre una aplicación de macOS."""
    result = subprocess.run(["open", "-a", app_name], capture_output=True)
    if result.returncode == 0:
        return f"Abriendo {app_name}"
    else:
        return f"No se encontró la aplicación: {app_name}"


def run_shell_command(command: str) -> str:
    """Ejecuta un comando de terminal (solo comandos seguros predefinidos)."""
    # Lista blanca de comandos seguros
    SAFE_COMMANDS = ["ls", "pwd", "date", "whoami", "uptime", "df", "free"]
    cmd_parts = command.strip().split()
    if not cmd_parts or cmd_parts[0] not in SAFE_COMMANDS:
        return f"Comando no permitido: {cmd_parts[0] if cmd_parts else 'vacío'}"
    result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=10)
    return result.stdout.strip() or result.stderr.strip()


def process_command(text: str) -> str:
    """
    Procesa el texto transcrito y ejecuta la acción correspondiente.
    Retorna una descripción de la acción tomada.
    """
    text_lower = text.lower().strip()
    logger.info(f"Procesando comando: {text_lower}")

    # Captura de pantalla
    if any(w in text_lower for w in ["captura", "screenshot", "pantalla", "foto"]):
        return take_screenshot()

    # Guardar nota
    elif any(w in text_lower for w in ["anota", "apunta", "nota", "recuerda"]):
        # Extraer el texto a anotar (quitar la palabra de comando)
        note_text = text_lower
        for w in ["anota", "apunta", "nota", "recuerda que", "recuerda"]:
            note_text = note_text.replace(w, "").strip()
        return save_note(note_text if note_text else text)

    # Búsqueda web
    elif any(w in text_lower for w in ["busca", "buscar", "search", "googlea"]):
        query = text_lower
        for w in ["busca", "buscar", "search", "googlea"]:
            query = query.replace(w, "").strip()
        return web_search(query if query else text)

    # Abrir aplicaciones
    elif "abre" in text_lower or "abrir" in text_lower:
        app = text_lower.replace("abre", "").replace("abrir", "").strip()
        APP_MAP = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "terminal": "Terminal",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "spotify": "Spotify",
            "notas": "Notes",
            "calendario": "Calendar",
        }
        app_name = APP_MAP.get(app, app.title())
        return open_app(app_name)

    # Comando no reconocido
    else:
        logger.warning(f"Comando no reconocido: {text_lower}")
        return f"Comando no reconocido: '{text}'"
