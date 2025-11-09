# instagram_bot.py - FINAL CON DEBUG + RAG + OLLAMA EN RAILWAY
from flask import Flask, request, jsonify
import requests
import logging
import os
from chatbot import chatbot  # ← Tu función RAG

# === CONFIGURACIÓN DE LOGS (PARA VER TODO EN RENDER) ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# === TUS DATOS DE META (LLÉNALOS) ===
VERIFY_TOKEN = "chocholis"                    # ← Igual que en Meta
IG_USER_ID = "17841405822304914"                           # ← Tu ID de Instagram
ACCESS_TOKEN = "IGAAgweXRBIktBZAFJweFpDcEtGYXRmY2RsNHM4QkJVaTdmQnJzV1pzRURObEdNSTgxam4xX1BYSnZAuejJicDhHWFNINUhNOVAwT0dITlQzNEdFcV93RlBpSHZATalkyQnI0M0d2SUlkNWZAWUng4SVo1YXQxREdyM2JOQkEyU0VnSQZDZD"                # ← Token de 60 días con instagram_manage_messages

# === RUTA PRINCIPAL (PARA VER SI LA APP ESTÁ VIVA) ===
@app.route('/')
def home():
    return "¡Bot vivo! Webhook en /webhook", 200

# === WEBHOOK: GET (verificación) + POST (DMs) ===
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # --- VERIFICACIÓN DE META ---
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        logger.info(f"GET recibido: mode={mode}, token={token}, challenge={challenge}")

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("VERIFICACIÓN EXITOSA")
            return challenge
        else:
            logger.warning("VERIFICACIÓN FALLIDA")
            return 'Forbidden', 403

    elif request.method == 'POST':
        # --- MENSAJE DE INSTAGRAM (DM) ---
        data = request.get_json()
        logger.info(f"POST recibido: {data}")

        if not data:
            logger.error("No hay JSON en el POST")
            return jsonify({"error": "No JSON"}), 400

        try:
            for entry in data.get('entry', []):
                for msg_event in entry.get('messaging', []):
                    sender_id = msg_event.get('sender', {}).get('id')
                    message_text = msg_event.get('message', {}).get('text', '')

                    if not message_text:
                        logger.info("Mensaje sin texto (sticker, imagen, etc.)")
                        continue

                    if sender_id == IG_USER_ID:
                        logger.info("Mensaje de ti mismo, ignorado")
                        continue

                    logger.info(f"DM de {sender_id}: {message_text}")

                    # === RESPUESTA CON RAG ===
                    answer = chatbot(message_text)
                    logger.info(f"Respuesta generada: {answer}")

                    # === ENVÍA RESPUESTA A INSTAGRAM ===
                    send_message(sender_id, answer)

            return jsonify({"status": "ok"}), 200

        except Exception as e:
            logger.error(f"Error procesando POST: {e}")
            return jsonify({"error": str(e)}), 500

# === ENVÍA MENSAJE A INSTAGRAM ===
def send_message(to_id, text):
    url = f"https://graph.instagram.com/v20.0/{IG_USER_ID}/messages"
    payload = {
        "recipient": {"id": to_id},
        "message": {"text": text[:1000]}  # Máx 1000 caracteres
    }
    headers = {"Content-Type": "application/json"}
    params = {"access_token": ACCESS_TOKEN}

    try:
        r = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            logger.info(f"Mensaje enviado a {to_id}")
        else:
            logger.error(f"Error enviando mensaje: {r.status_code} {r.text}")
    except Exception as e:
        logger.error(f"Excepción al enviar: {e}")

# === INICIO EN RENDER ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Iniciando bot en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
