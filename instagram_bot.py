from flask import Flask, request, jsonify
import requests
from chatbot import chatbot
import os

app = Flask(__name__)

# === TUS DATOS (LLÉNALOS) ===
VERIFY_TOKEN = "chocholis"
IG_USER_ID = "17841405822304914"
ACCESS_TOKEN = "IGAAgweXRBIktBZAFJweFpDcEtGYXRmY2RsNHM4QkJVaTdmQnJzV1pzRURObEdNSTgxam4xX1BYSnZAuejJicDhHWFNINUhNOVAwT0dITlQzNEdFcV93RlBpSHZATalkyQnI0M0d2SUlkNWZAWUng4SVo1YXQxREdyM2JOQkEyU0VnSQZDZD" 

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if (request.args.get('hub.mode') == 'subscribe' and
            request.args.get('hub.verify_token') == VERIFY_TOKEN):
            return request.args.get('hub.challenge')
        return 'Forbidden', 403

    if request.method == 'POST':
        data = request.get_json()
        print("DM recibido:", data)
        for entry in data.get('entry', []):
            for msg in entry.get('messaging', []):
                sender = msg['sender']['id']
                text = msg.get('message', {}).get('text')
                if text and sender != IG_USER_ID:
                    print(f"Usuario {sender}: {text}")
                    answer = chatbot(text)
                    send_message(sender, answer)
        return jsonify({"status": "ok"})

def send_message(to_id, text):
    url = f"https://graph.instagram.com/v20.0/{IG_USER_ID}/messages"
    payload = {
        "recipient": {"id": to_id},
        "message": {"text": text},
        "access_token": ACCESS_TOKEN
    }
    r = requests.post(url, json=payload)
    print("Respuesta enviada:", r.status_code)

# === INICIO EN RENDER ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)