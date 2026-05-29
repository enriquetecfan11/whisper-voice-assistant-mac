import logging
import subprocess
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_SYSTEM_PROMPT, TTS_VOICE, TTS_RATE

logger = logging.getLogger(__name__)

# Historial de conversacion (mantiene contexto entre turnos)
_conversation_history = []


def ask_groq(user_text: str) -> str:
    """
    Envia el texto del usuario a la API de Groq y devuelve la respuesta del LLM.
    Mantiene historial de conversacion para contexto.
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY no configurada en .env")
        return "No tengo configurada la API de Groq. Revisa el archivo .env"

    client = Groq(api_key=GROQ_API_KEY)

    # Anadir mensaje del usuario al historial
    _conversation_history.append({
        "role": "user",
        "content": user_text
    })

    # Construir mensajes con system prompt + historial
    messages = [{"role": "system", "content": GROQ_SYSTEM_PROMPT}] + _conversation_history

    try:
        logger.info(f"Enviando a Groq ({GROQ_MODEL}): '{user_text}'")
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=300,  # Respuestas cortas para TTS
        )
        assistant_reply = response.choices[0].message.content.strip()

        # Guardar respuesta en el historial
        _conversation_history.append({
            "role": "assistant",
            "content": assistant_reply
        })

        # Limitar historial a los ultimos 10 turnos (5 usuario + 5 asistente)
        if len(_conversation_history) > 20:
            _conversation_history.pop(0)
            _conversation_history.pop(0)

        logger.info(f"Respuesta Groq: '{assistant_reply}'")
        return assistant_reply

    except Exception as e:
        logger.error(f"Error llamando a Groq: {e}")
        return "Ha ocurrido un error al consultar la inteligencia artificial."


def speak(text: str) -> None:
    """
    Convierte texto a voz usando el comando 'say' de macOS.
    No bloquea el proceso principal.
    """
    if not text:
        return
    try:
        logger.info(f"TTS: '{text}'")
        subprocess.run(
            ["say", "-v", TTS_VOICE, "-r", str(TTS_RATE), text],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error en TTS: {e}")
    except FileNotFoundError:
        logger.error("Comando 'say' no encontrado. Solo disponible en macOS.")


def clear_history() -> None:
    """Limpia el historial de conversacion."""
    _conversation_history.clear()
    logger.info("Historial de conversacion limpiado")
