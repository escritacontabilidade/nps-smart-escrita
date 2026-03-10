import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import base64
import json

# 1. Configuração da Página
st.set_page_config(page_title="NPS Smart - Escrita", page_icon="💡")

# 2. Conexão Blindada (Base64)
def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Lê o texto blindado do Secrets
        blob = st.secrets["CHAVE_BASE64"]
        # Converte de volta para o formato original do Google
        info = json.loads(base64.b64decode(blob).decode("utf-8"))
        
        credentials = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

# 3. Estilo Visual (CSS)
st.markdown("""
<style>
    .stApp { background-color: #F4F6F8; }
    .header-container { background-color: #0E3A5D; padding: 1.5rem; border-radius: 10px; margin-bottom: 20px; }
    .header-title { color: #FFFFFF !important; font-size: 1.8rem; text-align: left; }
    div.stButton > button { background-color: #1F5E8C !important; color: white !important; width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 4. Cabeçalho
st.markdown('<div class="header-container"><h1 class="header-title">Pesquisa de Satisfação - Área Smart</h1></div>', unsafe_allow_html=True)

# 5. Lógica do Formulário
if 'passo' not in st.session_state:
    st.session_state.passo = 1
    st.session_state.respostas = {}

if st.session_state.passo == 1:
    with st.form("etapa1"):
        nome = st.text_input("Seu Nome:")
        empresa = st.text_input("Sua Empresa:")
        nota = st.select_slider("De 0 a 10, recomendaria a Área Smart?", options=list(range(11)), value=10)
        motivo = st.text_area("O que motivou sua nota?")
        
        if st.form_submit_button("Próximo"):
            if nome and empresa:
                st.session_state.respostas.update({'nome': nome, 'empresa': empresa, 'nota': nota, 'motivo': motivo})
                st.session_state.passo = 2
                st.experimental_rerun()
            else:
                st.error("Preencha nome e empresa.")

elif st.session_state.passo == 2:
    with st.form("etapa2"):
        st.subheader("Avaliação por Setor")
        n_tec = st.selectbox("Setor Técnico", ["Não uso"] + list(range(11)), index=11)
        n_fol = st.selectbox("Folha de Pagamento", ["Não uso"] + list(range(11)), index=11)
        contato = st.radio("Podemos ligar?", ["Sim", "Não"], horizontal=True)
        
        if st.form_submit_button("Finalizar"):
            client = conectar_planilha()
            if client:
                try:
                    sh = client.open_by_key(st.secrets["SHEET_ID"])
                    wks = sh.worksheet("respostas")
                    r = st.session_state.respostas
                    wks.append_row([
                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        r['nome'], r['empresa'], r['nota'], r['motivo'],
                        n_tec, n_fol, contato
                    ])
                    st.session_state.passo = 3
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")

elif st.session_state.passo == 3:
    st.balloons()
    st.success("Obrigado! Feedback enviado com sucesso.")
    if st.button("Nova Resposta"):
        st.session_state.passo = 1
        st.experimental_rerun()
