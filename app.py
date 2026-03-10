import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="NPS Smart - Escrita", page_icon="💡")

st.markdown("""
<style>
    .stApp { background-color: #F4F6F8; }
    label, p, span { color: #0E3A5D !important; font-weight: bold; }
    .header-container { 
        background-color: #0E3A5D; 
        padding: 1.5rem; 
        border-radius: 10px; 
        text-align: left;
        margin-bottom: 20px;
    }
    .header-title { color: #FFFFFF !important; margin-top: 10px; font-size: 1.8rem; }
    div.stButton > button { 
        background-color: #1F5E8C !important; 
        color: white !important; 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def conectar_planilha():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(credentials)

with st.container():
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="header-title">Pesquisa de Satisfação - Área Smart</h1></div>', unsafe_allow_html=True)

if 'passo' not in st.session_state:
    st.session_state.passo = 1
    st.session_state.respostas = {}

if st.session_state.passo == 1:
    with st.form("etapa1"):
        nome = st.text_input("Seu Nome:")
        empresa = st.text_input("Sua Empresa:")
        st.write("---")
        st.markdown("### De 0 a 10, o quanto você recomendaria a **Área Smart** da Escrita para um parceiro?")
        nota_smart = st.select_slider("Sua Nota:", options=list(range(11)), value=10)
        motivo = st.text_area("O que mais motivou sua nota?")

        if st.form_submit_button("Próximo"):
            if not nome or not empresa:
                st.error("Por favor, preencha seu nome e empresa.")
            elif nota_smart < 7 and not motivo.strip():
                st.error("Por favor, nos conte o que podemos melhorar.")
            else:
                st.session_state.respostas.update({
                    'nome': nome,
                    'empresa': empresa,
                    'nota_smart': nota_smart,
                    'motivo': motivo
                })
                st.session_state.passo = 2
                st.rerun()

elif st.session_state.passo == 2:
    with st.form("etapa2"):
        st.subheader("Avaliação por Setor")

        def criar_campo(label, desc):
            st.write(f"**{label}**")
            st.caption(desc)
            col1, col2 = st.columns([1, 3])
            opcoes = ["Não uso"] + list(range(11))
            n = col1.selectbox("Nota", opcoes, index=11, key=f"n_{label}")
            t = col2.text_input("Sugestão (opcional)", key=f"t_{label}")
            st.divider()
            return n, t

        n_tec, t_tec = criar_campo("Setor Técnico (Contábil e Fiscal)", "Entrega de impostos e obrigações.")
        n_fol, t_fol = criar_campo("Pessoal (Folha)", "Folha de pagamento e rotinas.")
        n_rec, t_rec = criar_campo("Recrutamento", "Processos seletivos.")

        contato = st.radio("Podemos te ligar sobre sua nota?", ["Sim", "Não"], horizontal=True)

        if st.form_submit_button("Finalizar"):
            try:
                client = conectar_planilha()
                sh = client.open_by_key(st.secrets["SHEET_ID"])
                wks = sh.worksheet("respostas")

                r = st.session_state.respostas
                linha = [
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    r["nome"],
                    r["empresa"],
                    r["nota_smart"],
                    r["motivo"],
                    n_tec, t_tec,
                    n_fol, t_fol,
                    n_rec, t_rec,
                    contato
                ]

                wks.append_row(linha)
                st.session_state.passo = 3
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao salvar: {type(e).__name__}: {e}")

elif st.session_state.passo == 3:
    st.balloons()
    st.success("Obrigado! Sua opinião faz a área Smart crescer.")
    if st.button("Enviar nova resposta"):
        st.session_state.passo = 1
        st.session_state.respostas = {}
        st.rerun()
