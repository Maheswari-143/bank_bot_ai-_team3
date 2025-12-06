import streamlit as st
import pandas as pd
import os, json
from datetime import datetime

# ------------------ Paths ------------------
BASE_DIR = os.path.dirname(__file__)
CRED_FILE = os.path.join(BASE_DIR, 'credentials.json')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

training_path = os.path.join(DATA_DIR, 'training.json')
faq_path = os.path.join(DATA_DIR, 'faq.json')
queries_path = os.path.join(DATA_DIR, 'user_queries.csv')

# ------------------ Auto Login (Skip UI) ------------------
st.session_state['logged_in'] = True  
st.session_state['user'] = "admin"     # Default admin display name

# ------------------ Load Data ------------------
training = json.load(open(training_path)) if os.path.exists(training_path) else {"intents":[]}
faq = json.load(open(faq_path)) if os.path.exists(faq_path) else []
df_queries = pd.read_csv(queries_path) if os.path.exists(queries_path) else pd.DataFrame(columns=['query','intent','confidence','date'])

# ------------------ Admin Panel ------------------
st.sidebar.title('Navigation')
page = st.sidebar.radio('Go to', ['Dashboard','Training Data','User Queries','FAQs','Analytics','Settings','Logout'])

if page == 'Logout':
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['action'] = None
    st.experimental_rerun()

# DASHBOARD
if page == 'Dashboard':
    st.title("🏦 Admin Dashboard")
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
            training.setdefault('intents', []).append({
                'intent': new_intent,
                'examples': [e.strip() for e in new_examples.split(',') if e.strip()]
            })
            json.dump(training, open(training_path, 'w'), indent=2)
            st.success('Intent added and saved to data/training.json')

    st.subheader('Existing intents')
    for i, it in enumerate(training.get('intents', [])):
        st.write(f"{i+1}. **{it.get('intent')}** — {', '.join(it.get('examples', []))}")

elif page == 'User Queries':
    st.header('💬 User Queries')
    if not df_queries.empty:
        st.download_button('Download CSV', df_queries.to_csv(index=False), file_name='queries.csv')
        st.dataframe(df_queries)
    else:
        st.info('No user queries found.')

elif page == 'FAQs':
    st.header('❓ FAQ Manager')
    with st.form('faq_form', clear_on_submit=True):
        q = st.text_input('Question')
        a = st.text_area('Answer')
        ok = st.form_submit_button('Add FAQ')
        if ok and q:
            faq.append({'q':q, 'a':a})
            json.dump(faq, open(faq_path, 'w'), indent=2)
            st.success('FAQ saved.')

    if faq:
        for i, f in enumerate(faq):
            st.write(f"{i+1}. Q: **{f.get('q')}**\nA: {f.get('a')}")

elif page == 'Analytics':
    st.header('📈 Analytics Dashboard')
    st.line_chart(pd.DataFrame({'queries':[5,10,30,50,80,130]}))

elif page == 'Settings':
    st.header('⚙️ Settings')
    st.write("Admin Settings Page")
    if st.checkbox("Show Credentials File"):
        st.write(CRED_FILE)
