import os
import json
import csv
import re
import string
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
templates_path = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=templates_path)
app.secret_key = 'bank_secret_key'

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
db = SQLAlchemy(app)

# Training data file path
TRAINING_DATA_FILE = os.path.join(os.path.dirname(__file__), 'training_data.json')

# Load training data
def load_training_data():
    if os.path.exists(TRAINING_DATA_FILE):
        with open(TRAINING_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

training_data = load_training_data()

# Load CSV dataset
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'bankbot', 'milestone 2', 'bank_chatbot_dataset.csv')
USER_DATA_FILE = os.path.join(os.path.dirname(__file__), 'user_data.json')

def load_dataset():
    dataset = []
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for k in row:
                    if row[k] is None:
                        row[k] = ''
                    else:
                        row[k] = row[k].strip()
                dataset.append(row)
    return dataset

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

dataset = load_dataset()
user_data = load_user_data()

# Normalization helper
def normalize_text(s):
    if not s:
        return ''
    s = s.lower().strip()
    s = s.replace("what's", "what is").replace("it's", "it is").replace("i'm", "i am")
    allowed = set(string.ascii_lowercase + string.digits + ' ')
    s = ''.join(ch for ch in s if ch in allowed)
    s = ' '.join(s.split())
    return s

def find_intent_response(user_message):
    if not user_message:
        return None
    message_lower = user_message.strip().lower()
    message_norm = normalize_text(user_message)

    for row in dataset:
        row_text = (row.get('text') or '').strip().lower()
        row_norm = normalize_text(row_text)
        if row_norm and row_norm == message_norm:
            return {
                'intent': row.get('intent', ''),
                'response': row.get('response', ''),
                'entities': row.get('entities', '')
            }

    message_digits = re.findall(r'\d+', user_message)
    digits_concat = ''.join(message_digits)
    for row in dataset:
        entities = (row.get('entities') or '').strip()
        if 'ACCOUNT_NUMBER' in entities or 'MONEY' in entities:
            parts = [p for p in entities.split('|') if ':' in p]
            for p in parts:
                key, val = p.split(':', 1)
                val = val.strip()
                if val and re.search(r'\d+', val):
                    if val in user_message or val in digits_concat or any(val == d for d in message_digits):
                        return {
                            'intent': row.get('intent', ''),
                            'response': row.get('response', ''),
                            'entities': row.get('entities', '')
                        }

    msg_tokens = set(message_norm.split())
    best_row = None
    best_score = 0
    for row in dataset:
        row_text = (row.get('text') or '').strip().lower()
        row_norm = normalize_text(row_text)
        if not row_norm:
            continue
        row_tokens = set(row_norm.split())
        overlap = len(msg_tokens & row_tokens)
        score = overlap
        if score > best_score:
            best_score = score
            best_row = row
    if best_row and best_score >= 1:
        return {
            'intent': best_row.get('intent', ''),
            'response': best_row.get('response', ''),
            'entities': best_row.get('entities', '')
        }

    return None

def extract_entities(text, entities_str):
    entities = {}
    if not entities_str:
        return entities

    for ent in entities_str.split('|'):
        if ':' in ent:
            key, val = ent.split(':', 1)
            key = key.strip().upper()
            val = val.strip()
            if key == 'ACCOUNT_NUMBER' and val:
                entities['account_number'] = val
            elif key == 'MONEY' and val:
                entities['amount'] = val
            elif key == 'PERSON' and val:
                entities['person'] = val

    if 'account_number' not in entities:
        m = re.search(r'\b(\d{6,})\b', text)
        if m:
            entities['account_number'] = m.group(1)
    if 'amount' not in entities:
        m = re.search(r'\b(\d+)\b', text)
        if m:
            entities['amount'] = m.group(1)
    if 'person' not in entities:
        m = re.search(r'\b([A-Za-z]{2,})\b', text)
        if m:
            entities['person'] = m.group(1)

    return entities

def get_intent_color(intent):
    intent_colors = {
        'greet': '#4CAF50',
        'goodbye': '#FF9800',
        'check_balance': '#2196F3',
        'transaction_inquiry': '#9C27B0',
        'loan_inquiry': '#F44336',
        'card_inquiry': '#00BCD4',
        'block_card': '#E91E63',
        'branch_locator': '#795548',
        'transfer_money': '#FF5722',
        'thanks': '#8BC34A',
        'out_of_scope': '#757575'
    }
    return intent_colors.get(intent, '#757575')

# -----------------------------
# Database Model
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), nullable=True, unique=True)
    account_type = db.Column(db.String(50), nullable=True)
    balance = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def home():
    return render_template('home.html')

# ---------- Register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists! Please login."

        try:
            new_user = User(
                username=username,
                email=email,
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect(url_for('create_account'))
        except Exception as e:
            db.session.rollback()
            return f"An error occurred during registration: {str(e)}"
    return render_template('register.html')

# ---------- Create Account ----------
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        account_number = request.form['account_number']
        account_type = request.form['account_type']
        balance = request.form['balance']  # Get balance from form

        # Check if account number already exists
        existing_account = User.query.filter_by(account_number=account_number).first()
        if existing_account:
            return "Account number already exists! Please use a different account number."

        try:
            user.account_number = account_number
            user.account_type = account_type
            user.balance = float(balance)  # Convert to float before saving
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            return f"An error occurred while creating account: {str(e)}"

    return render_template('create_account.html')


# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password!"
    return render_template('login.html')

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.account_number or not user.account_type:
        return redirect(url_for('create_account'))
    return render_template('dashboard.html', username=user.username, account_number=user.account_number, balance=user.balance)

# ---------- User Details ----------
@app.route('/user_details')
def user_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('user_details.html', user=user)

# ---------- Check Balance ----------
@app.route('/check_balance', methods=['GET', 'POST'])
def check_balance():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    balance = None
    if request.method == 'POST':
        acc_number = request.form['account_number']
        user = User.query.filter_by(account_number=acc_number).first()
        if user:
            balance = user.balance
        else:
            balance = "Account not found!"
    return render_template('check_balance.html', balance=balance)

# ---------- Other Services ----------
@app.route('/other_services')
def other_services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('other_services.html')

# ---------- Bank Bot ----------
@app.route('/bankbot')
def bankbot():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('bankbot.html', username=session['username'])

def append_to_dataset_row(text, intent, response, entities_str=''):
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    file_exists = os.path.exists(DATASET_PATH) and os.path.getsize(DATASET_PATH) > 0

    for row in dataset:
        if row.get('text') == text and row.get('intent') == intent and row.get('entities') == entities_str:
            return False

    with open(DATASET_PATH, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['text','intent','response','entities'])
        writer.writerow([text, intent, response, entities_str])

    dataset.append({'text': text, 'intent': intent, 'response': response, 'entities': entities_str})
    return True

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return {'error': 'Unauthorized'}, 401

    user_message = request.json.get('message', '').strip()
    user = User.query.get(session['user_id'])
    user_id_str = str(session['user_id'])

    if user_id_str not in user_data:
        user_data[user_id_str] = {
            'account_number': user.account_number,
            'balance': user.balance,
            'conversations': []
        }

    result = find_intent_response(user_message)
    intent = 'out_of_scope'
    intent_color = get_intent_color(intent)
    entities = {}
    bot_reply = ''

    if result:
        intent = result.get('intent', 'out_of_scope')
        intent_color = get_intent_color(intent)
        entities = extract_entities(user_message, result.get('entities', ''))
        bot_reply = (result.get('response') or '').strip()
        if not bot_reply:
            if entities.get('amount'):
                bot_reply = f"💰 Your balance is {entities['amount']}."
            else:
                acct = entities.get('account_number', '')
                if acct:
                    for row in dataset:
                        ents = (row.get('entities') or '')
                        if f"ACCOUNT_NUMBER:{acct}" in ents and 'MONEY:' in ents:
                            m = re.search(r'MONEY:(\d+)', ents)
                            if m:
                                bot_reply = f"💰 Your balance is {m.group(1)}."
                                entities['amount'] = m.group(1)
                                break
        if not bot_reply:
            reply_digits = re.findall(r'\d+', user_message)
            if reply_digits:
                bot_reply = f"💰 Your balance is {reply_digits[0]}."
        if bot_reply is None:
            bot_reply = ''

        if entities:
            user_data[user_id_str].update(entities)
            if 'amount' in entities:
                user_data[user_id_str]['last_amount'] = entities['amount']
            if 'person' in entities:
                user_data[user_id_str]['last_recipient'] = entities['person']
            if 'account_number' in entities:
                user_data[user_id_str]['account_number'] = entities['account_number']

        user_data[user_id_str]['conversations'].append({
            'user': user_message,
            'bot': bot_reply,
            'intent': intent
        })
        save_user_data(user_data)

        add_entities = []
        if 'amount' in entities:
            add_entities.append(f"MONEY:{entities['amount']}")
        if 'account_number' in entities:
            add_entities.append(f"ACCOUNT_NUMBER:{entities['account_number']}")
        entities_str = '|'.join(add_entities)

        reply_digits = re.findall(r'\d+', str(bot_reply))
        if not entities_str and reply_digits:
            entities_str = f"MONEY:{reply_digits[0]}"

        if entities_str:
            try:
                append_to_dataset_row(user_message, intent, bot_reply, entities_str)
            except Exception:
                pass
    else:
        bot_reply = "I can only assist with banking questions. Try asking about balance, transfers, loans, or cards."
        intent = "out_of_scope"
        intent_color = get_intent_color(intent)
        user_data[user_id_str]['conversations'].append({
            'user': user_message,
            'bot': bot_reply,
            'intent': intent
        })
        save_user_data(user_data)

    return {
        'reply': bot_reply,
        'intent': intent,
        'intent_color': intent_color
    }

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ---------- Run Server ----------
if __name__ == '__main__':
    app.run(debug=True)
