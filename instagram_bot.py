# instagram_bot.py - Bot oficial IG API
from flask import Flask, request, jsonify
import requests
from chatbot import chatbot  # TU CHATBOT EXISTENTE
import os

app = Flask(__name__)

# === TUS DATOS (los tienes en la imagen) ===
APP_ID = "2305098013286987"
APP_SECRET = "42b8e793202f0538a0d0f"
VERIFY_TOKEN = "chocholis"  # Inventa uno
IG_USER_ID = "17841477868557815"  # Lo obtienes en el Paso 3

# === WEBHOOK ===
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verificación de Meta
        if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return 'Forbidden', 403

    if request.method == 'POST':
        data = request.get_json()
        print("Mensaje recibido:", data)

        for entry in data.get('entry', []):
            for messaging in entry.get('messaging', []):
                sender_id = messaging['sender']['id']
                message_text = messaging.get('message', {}).get('text')

                if message_text and sender_id != IG_USER_ID:
                    print(f"Usuario {sender_id}: {message_text}")
                    
                    # TU CHATBOT
                    respuesta = chatbot(message_text)
                    
                    # Enviar respuesta
                    send_message(sender_id, respuesta)

        return jsonify({"status": "ok"})

# === ENVIAR MENSAJE ===
def send_message(recipient_id, text):
    url = f"https://graph.instagram.com/v20.0/{IG_USER_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": get_long_lived_token()
    }
    r = requests.post(url, json=payload)
    print("Respuesta enviada:", r.status_code, r.text)

# === OBTENER TOKEN LARGO (60 días) ===
def get_long_lived_token():
    # Usa tu token corto de "Generar identificador" y cámbialo por uno largo
    short_token = "IGAAgweXRBIktBZAFJweFpDcEtGYXRmY2RsNHM4QkJVaTdmQnJzV1pzRURObEdNSTgxam4xX1BYSnZAuejJicDhHWFNINUhNOVAwT0dITlQzNEdFcV93RlBpSHZATalkyQnI0M0d2SUlkNWZAWUng4SVo1YXQxREdyM2JOQkEyU0VnSQZDZD"  # Del paso siguiente
    url = "https://graph.instagram.com/access_token"
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": APP_SECRET,
        "access_token": short_token
    }
    r = requests.get(url, params=params)
    return r.json().get('access_token')

# === INICIO CON NGROK ===
if __name__ == "__main__":
    from pyngrok import ngrok
    
    print("BOT ACTIVO")
    
    # Abre túnel público
    public_url = ngrok.connect(5000, "http")
    webhook_url = f"{public_url}/webhook"
    
    print(f"URL del webhook: {webhook_url}")
    print("CÓPIALA Y PÉGALA EN EL PANEL DE META")
    print("Presiona Ctrl+C para detener")
    
    # Inicia Flask
    app.run(port=5000, debug=False)