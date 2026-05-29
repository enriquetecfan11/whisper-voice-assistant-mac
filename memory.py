import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Archivo donde se guarda la memoria persistente
MEMORY_FILE = Path(os.path.expanduser("~/.jarvis_memory.json"))


def _load() -> dict:
    """Carga la memoria desde disco. Devuelve dict vacio si no existe."""
    if not MEMORY_FILE.exists():
        return {"facts": [], "user": {}, "updated_at": None}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"No se pudo cargar la memoria: {e}")
        return {"facts": [], "user": {}, "updated_at": None}


def _save(data: dict) -> None:
    """Guarda la memoria en disco."""
    data["updated_at"] = datetime.now().isoformat()
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Memoria guardada en {MEMORY_FILE}")
    except IOError as e:
        logger.error(f"No se pudo guardar la memoria: {e}")


def remember(fact: str) -> None:
    """
    Guarda un hecho libre sobre el usuario o el contexto.
    Ejemplo: remember("El usuario se llama Enrique y trabaja en DevOps")
    """
    data = _load()
    entry = {
        "fact": fact.strip(),
        "timestamp": datetime.now().isoformat()
    }
    # Evitar duplicados exactos
    existing_facts = [f["fact"] for f in data["facts"]]
    if fact.strip() not in existing_facts:
        data["facts"].append(entry)
        _save(data)
        logger.info(f"Memoria: recordado -> '{fact}'")
    else:
        logger.debug(f"Memoria: ya existe -> '{fact}'")


def set_user_info(key: str, value: str) -> None:
    """
    Guarda informacion estructurada del usuario.
    Ejemplo: set_user_info("nombre", "Enrique")
    set_user_info("ciudad", "Torrejon de Ardoz")
    set_user_info("trabajo", "DevOps engineer")
    """
    data = _load()
    data["user"][key] = {
        "value": value.strip(),
        "updated_at": datetime.now().isoformat()
    }
    _save(data)
    logger.info(f"Memoria usuario: {key} = '{value}'")


def get_memory_as_text() -> str:
    """
    Devuelve toda la memoria como texto plano para inyectar en el system prompt.
    Formato optimizado para que el LLM lo entienda bien.
    """
    data = _load()
    lines = []

    if data["user"]:
        lines.append("Informacion conocida del usuario:")
        for key, info in data["user"].items():
            lines.append(f"- {key}: {info['value']}")

    if data["facts"]:
        lines.append("Hechos recordados de conversaciones anteriores:")
        for entry in data["facts"][-20:]:  # Solo los ultimos 20 para no saturar el contexto
            lines.append(f"- {entry['fact']}")

    if not lines:
        return ""

    return "\n".join(lines)


def get_summary() -> str:
    """Resumen legible de lo que hay en memoria (para responder al usuario)."""
    data = _load()
    total_facts = len(data["facts"])
    total_user = len(data["user"])

    if total_facts == 0 and total_user == 0:
        return "No recuerdo nada todavia. Cuentame cosas sobre ti."

    parts = []
    if data["user"]:
        for key, info in data["user"].items():
            parts.append(f"tu {key} es {info['value']}")
    if data["facts"]:
        for entry in data["facts"][-5:]:  # Solo los 5 ultimos
            parts.append(entry["fact"])

    return "Se que " + ", ".join(parts) + "."


def forget_all() -> None:
    """Borra toda la memoria persistente."""
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()
        logger.info("Memoria borrada completamente")
    else:
        logger.info("No habia memoria que borrar")
