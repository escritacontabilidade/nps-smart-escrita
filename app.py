import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="NPS Smart - Escrita", page_icon="💡")

def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Pega os segredos e transforma em dicionário comum
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # TRATAMENTO DE CHOQUE: Limpa a chave de qualquer caractere invisível ou erro de escape
    pk = creds_dict["private_key"]
    pk = pk.replace("\\n", "\n")  # Converte os \n de texto em quebras reais
    pk = pk.strip().strip('"').strip("'") # Remove aspas ou espaços nas pontas
    
    creds_dict["private_key"] = pk

    try:
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Erro na validação da chave: {e}")
        return None

# --- ESTILO ---
st.markdown("""
<style>
    .stApp { background-color: #F4F6F8; }
    .header-container { background-color: #0E3A5D; padding: 1.5rem; border-radius: 10px; margin-bottom: 20px; }
    .header-title { color: #FFFFFF !important; font-size: 1.8rem; }
    div.stButton > button { background-color: #1F5E8C !important; color: white !important; width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><h1 class="header-title">Pesquisa de Satisfação - Área Smart</h1></div>', unsafe_allow_html=True)

# --- FORMULÁRIO ---
if 'passo' not in st.session_state:
    st.session_state.passo = 1
    st.session_state.respostas = {}

if st.session_state.passo == 1:
    with st.form("etapa1"):
        nome = st.text_input("Seu Nome:")
        empresa = st.text_input("Sua Empresa:")
        nota = st.select_slider("Nota (0-10):", options=list(range(11)), value=10)
        motivo = st.text_area("O que motivou sua nota?")
        if st.form_submit_button("Próximo"):
            if nome and empresa:
                st.session_state.respostas.update({'nome': nome, 'empresa': empresa, 'nota': nota, 'motivo': motivo})
                st.session_state.passo = 2
                st.rerun()
            else:
                st.error("Preencha nome e empresa.")

elif st.session_state.passo == 2:
    with st.form("etapa2"):
        st.subheader("Avaliação por Setor")
        # Pergunta Unificada conforme solicitado:
        n_tec = st.selectbox("Técnico (Contábil e Fiscal)", ["Não uso"] + list(range(11)), index=11)
        n_fol = st.selectbox("Pessoal (Folha)", ["Não uso"] + list(range(11)), index=11)
        n_rec = st.selectbox("Recrutamento e Seleção", ["Não uso"] + list(range(11)), index=11)
        contato = st.radio("Podemos ligar?", ["Sim", "Não"], horizontal=True)
        
        if st.form_submit_button("Finalizar"):
            client = conectar_planilha()
            if client:
                try:
                    sh = client.open_by_key(st.secrets["SHEET_ID"])
                    wks = sh.worksheet("respostas")
                    r = st.session_state.respostas
                    # Adicionado n_rec na lista de salvamento
                    wks.append_row([
                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        r['nome'], r['empresa'], r['nota'], r['motivo'],
                        n_tec, n_fol, n_rec, contato
                    ])
                    st.session_state.passo = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")

elif st.session_state.passo == 3:
    st.balloons()
    st.success("Obrigado! Feedback enviado com sucesso.")
    if st.button("Nova Resposta"):
        st.session_state.passo = 1
        st.rerun()
