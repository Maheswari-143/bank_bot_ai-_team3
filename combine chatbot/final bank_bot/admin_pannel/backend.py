from flask import Flask, request, jsonify, session
import json, os
from datetime import datetime
app = Flask(__name__)
app.secret_key = "bank_secret_key"

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
QUERIES_CSV = os.path.join(DATA_DIR, 'user_queries.csv')

@app.route('/predict', methods=['POST'])
def predict():
    payload = request.json or {}
    query = payload.get('query','')

    intent = 'unknown'
    if 'balance' in query.lower():
        intent = 'check_balance'
    elif 'transfer' in query.lower() or 'send' in query.lower():
        intent = 'transfer_money'

    confidence = 0.85

    exists = os.path.exists(QUERIES_CSV)
    with open(QUERIES_CSV, 'a', encoding='utf-8') as f:
        if not exists:
            f.write('query,intent,confidence,date\n')
        f.write(f'"{query}",{intent},{confidence},{datetime.utcnow().isoformat()}\n')

    return jsonify({'intent': intent, 'confidence': confidence})



