
import streamlit as st
import pandas as pd
import os, json
from datetime import datetime

GRADIENT = 'linear-gradient(90deg, #e6f2ff 0%, #cce6ff 50%, #b3dbff 100%)'
CARD_BG = '#ffffff'
ACCENT = '#2b7bd3'

st.set_page_config(page_title="BankBot Assistant — Admin Panel", page_icon="🏦", layout='wide')

st.markdown(f"""
<style>
:root{{--accent: {ACCENT}; --card: {CARD_BG};}}
.header-container{{background: {GRADIENT}; padding: 28px 32px; border-radius: 12px; box-shadow: 0 6px 18px rgba(43,123,211,0.08); margin-bottom: 18px;}}
.header-title{{font-size: 40px; font-weight: 700; color: #072b57; margin: 0;}}
.header-sub{{color: #2f597f; margin-top:6px; font-size:14px;}}
.stButton>button{{border-radius:8px;}}
.card{{background: var(--card); border-radius:10px; padding:18px; box-shadow: 0 6px 18px rgba(43,123,211,0.05);}}
.metric-number{{font-size:34px; font-weight:700; color: #072b57;}}
.small-muted{{color:#6b859b;}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container">'
            '<div style="display:flex;align-items:center;gap:16px;">'
            '<div style="font-size:36px;">🏦</div>'
            '<div>'
            '<h1 class="header-title">BankBot Assistant — Admin Panel</h1>'
            '<div class="header-sub">Admin console for managing training data, FAQs and user queries</div>'
            '</div>'
            '</div>'
            '</div>', unsafe_allow_html=True)

CRED_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
def load_credentials():
    if os.path.exists(CRED_FILE):
        return json.load(open(CRED_FILE))
    return {"admin_user":"admin","admin_pass":"admin123"}
creds = load_credentials()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None

if not st.session_state['logged_in']:
    st.markdown('---')
    st.subheader('🔐 Admin Login')
    user = st.text_input('Username')
    pwd = st.text_input('Password', type='password')
    if st.button('Login'):
        if user == creds.get('admin_user') and pwd == creds.get('admin_pass'):
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.experimental_rerun()
        else:
            st.error('Invalid credentials. (Demo uses admin/admin123)')
    st.stop()

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
training_path = os.path.join(DATA_DIR, 'training.json')
faq_path = os.path.join(DATA_DIR, 'faq.json')
queries_path = os.path.join(DATA_DIR, 'user_queries.csv')

if os.path.exists(training_path):
    training = json.load(open(training_path))
else:
    training = {"intents": []}

if os.path.exists(faq_path):
    faq = json.load(open(faq_path))
else:
    faq = []

if os.path.exists(queries_path):
    df_queries = pd.read_csv(queries_path)
else:
    df_queries = pd.DataFrame(columns=['query','intent','confidence','date'])

st.sidebar.title('Navigation')
page = st.sidebar.radio('Go to', ['Dashboard','Training Data','User Queries','FAQs','Analytics','Settings','Logout'])

if page == 'Logout':
    if st.sidebar.button('Confirm logout'):
        st.session_state['logged_in'] = False
        st.session_state['user'] = None
        st.experimental_rerun()
    st.stop()

if page == 'Dashboard':
    st.write('<div class="card">', unsafe_allow_html=True)
    cols = st.columns([1,1,1,1])
    cols[0].markdown('<div class="small-muted">Total Queries</div><div class="metric-number">{}</div>'.format(len(df_queries)), unsafe_allow_html=True)
    cols[1].markdown('<div class="small-muted">Success Rate</div><div class="metric-number">{}</div>'.format('94.2%'), unsafe_allow_html=True)
    cols[2].markdown('<div class="small-muted">Intents</div><div class="metric-number">{}</div>'.format(len(training.get('intents',[]))), unsafe_allow_html=True)
    cols[3].markdown('<div class="small-muted">Entity Types</div><div class="metric-number">{}</div>'.format(42), unsafe_allow_html=True)
    st.write('</div>', unsafe_allow_html=True)
    st.markdown('### Recent Queries')
    if df_queries.empty:
        st.info('No queries logged yet.')
    else:
        st.dataframe(df_queries.tail(20))

elif page == 'Training Data':
    st.header('📝 Training Data Editor')
    with st.form('training_form', clear_on_submit=True):
        new_intent = st.text_input('New intent name')
        new_examples = st.text_area('Example phrases (comma-separated)')
        submitted = st.form_submit_button('Add Intent')
        if submitted and new_intent:
            training.setdefault('intents', []).append({'intent': new_intent, 'examples': [e.strip() for e in new_examples.split(',') if e.strip()]})
            json.dump(training, open(training_path, 'w'), indent=2)
            st.success('Intent added and saved to data/training.json')
    st.subheader('Existing intents')
    for i, it in enumerate(training.get('intents', [])):
        st.write(f"{i+1}. **{it.get('intent')}** — {', '.join(it.get('examples', []))}")

elif page == 'User Queries':
    st.header('💬 User Queries')
    st.markdown('Download or preview recent user queries collected by the system.')
    if not df_queries.empty:
        st.download_button('Download queries CSV', df_queries.to_csv(index=False), file_name='user_queries_dataset.csv')
        st.dataframe(df_queries)
    else:
        st.info('Dataset is empty. You can upload or use the sample CSV.')
    uploaded = st.file_uploader('Upload a CSV of queries to replace current dataset', type=['csv'])
    if uploaded:
        df_new = pd.read_csv(uploaded)
        df_new.to_csv(queries_path, index=False)
        st.success('Saved uploaded queries to data/user_queries.csv')
        st.experimental_rerun()

elif page == 'FAQs':
    st.header('❓ FAQ Manager')
    with st.form('faq_form', clear_on_submit=True):
        q = st.text_input('Question')
        a = st.text_area('Answer')
        ok = st.form_submit_button('Add FAQ')
        if ok and q:
            faq.append({'q':q, 'a':a})
            json.dump(faq, open(faq_path, 'w'), indent=2)
            st.success('FAQ saved to data/faq.json')
    if faq:
        for i, f in enumerate(faq):
            st.write(f"{i+1}. Q: **{f.get('q')}**\nA: {f.get('a')}")

elif page == 'Analytics':
    st.header('📈 Analytics Dashboard')
    st.line_chart(pd.DataFrame({'queries':[5,10,30,50,80,130]}))
    st.write('This is demo analytics. Connect to a real DB for production.')

elif page == 'Settings':
    st.header('⚙️ Settings')
    st.write('Admin settings (demo)')
    if st.checkbox('Show credentials file path'):
        st.write(CRED_FILE)
