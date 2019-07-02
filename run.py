from flask import Flask, request
from core import b
import os

app = Flask(__name__)

@app.route('/{}'.format(b.token), methods=['POST']) #Telegram should be connected to this hook
def webhook():
    b.check(request.get_json())
    return 'ok', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))