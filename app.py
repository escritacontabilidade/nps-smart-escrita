import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Pesquisa de Satisfação Setor Smart", page_icon="💡", layout="centered")

# --- SOLUÇÃO DO LOOPING: LIMPEZA DE QUERY PARAMS ---
# O Streamlit Cloud entra em loop tentando ler o ?embed=true repetidamente. 
# Essa linha limpa a intenção de redirecionamento do servidor.
if st.query_params.get("embed") == "true":
    pass 

def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        pk = creds_dict["private_key"].replace("\\n", "\n").strip().strip('"').strip("'")
        creds_dict["private_key"] = pk
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

# --- 2. ESTILO VISUAL E AJUSTE PARA EMBED ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #F4F6F8; }
    .header-container {
        background-color: #0E3A5D;
        padding: 1rem 1.5rem; 
        border-radius: 10px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    .header-title {
        color: #FFFFFF !important;
        font-size: 1.6rem;
        font-weight: bold;
        margin: 0;
    }
    .stSelectbox label, .stSlider label, .stTextInput label, .stTextArea label, .stRadio label {
        color: #0E3A5D !important;
        font-weight: bold;
    }
    div.stButton > button {
        background-color: #1F5E8C !important;
        color: white !important;
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
        border: none;
    }
    .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO VISUAL ---
st.markdown('<div class="header-container"><h1 class="header-title">Pesquisa de Satisfação Setor Smart</h1></div>', unsafe_allow_html=True)

col_logo, col_vazia = st.columns([1, 2])
with col_logo:
    NOME_ARQUIVO_LOGO = "Logo Escrita.png"
    if os.path.exists(NOME_ARQUIVO_LOGO):
        st.image(NOME_ARQUIVO_LOGO, width=180)
    else:
        st.warning("Logo não encontrada.")

st.write("") 

# --- 3. CONTROLE DE FLUXO ---
if 'passo' not in st.session_state:
    st.session_state.passo = 1
    st.session_state.respostas = {}

# --- PASSO 1: IDENTIFICAÇÃO E NPS GERAL ---
if st.session_state.passo == 1:
    with st.form("etapa1"):
        nome = st.text_input("Seu Nome:", placeholder="Ex: João Silva")
        empresa = st.text_input("Nome da sua empresa:", placeholder="Ex: Empresa ABC")
        st.write("---")
        st.markdown("### De 0 a 10, o quanto você recomendaria a Escrita Contabilidade para um amigo?")
        nota_nps = st.select_slider("Nota:", options=list(range(11)), value=10)
        motivo_nps = st.text_area("O que mais motivou a sua nota?", placeholder="Conte-nos brevemente o motivo da sua avaliação...")

        if st.form_submit_button("Próxima Etapa"):
            if nome and empresa:
                st.session_state.respostas.update({
                    'nome': nome, 'empresa': empresa, 'nota_nps': nota_nps, 'motivo_nps': motivo_nps
                })
                st.session_state.passo = 2
                st.rerun()
            else:
                st.error("Por favor, preencha Nome e Empresa.")

# --- PASSO 2: CRITÉRIOS GERAIS ---
elif st.session_state.passo == 2:
    st.subheader("Avaliação Geral de Serviços")
    with st.form("etapa2"):
        c1, c2 = st.columns(2)
        clareza = c1.select_slider("Clareza nas informações:", options=list(range(1, 11)), value=10)
        comunicacao = c1.select_slider("Qualidade da Comunicação:", options=list(range(1, 11)), value=10)
        custo = c1.select_slider("Custo-benefício:", options=list(range(1, 11)), value=10)
        prazos = c2.select_slider("Cumprimento de Prazos:", options=list(range(1, 11)), value=10)
        cordialidade = c2.select_slider("Cordialidade no Atendimento:", options=list(range(1, 11)), value=10)

        if st.form_submit_button("Avaliar Departamentos"):
            st.session_state.respostas.update({
                'clareza': clareza, 'prazos': prazos, 'comunicacao': comunicacao,
                'cordialidade': cordialidade, 'custo': custo
            })
            st.session_state.passo = 3
            st.rerun()

# --- PASSO 3: DEPARTAMENTOS ---
elif st.session_state.passo == 3:
    st.subheader("Avaliação por Setor")
    st.info("Para cada setor, dê uma nota e, se desejar, sugira uma melhoria.")

    with st.form("etapa3"):
        def campo_setor(titulo, subtitulo, chave):
            st.markdown(f"#### {titulo}")
            st.caption(subtitulo)
            col_n, col_m = st.columns([1, 3])
            nota = col_n.selectbox(f"Nota", ["Não uso"] + list(range(11)), index=11, key=f"n_{chave}")
            melhoria = col_m.text_input("O que podemos melhorar? (opcional)", key=f"m_{chave}")
            st.write("---")
            return nota, melhoria

        n_cont_fisc, m_cont_fisc = campo_setor("Setor Contábil / Fiscal", "Lançamentos, conciliações e impostos.", "cont_fisc")
        n_fol, m_fol = campo_setor("Pessoal (Folha)", "Folha de pagamento e rotinas trabalhistas.", "fol")
        n_legal, m_legal = campo_setor("Setor Legal / Societário", "Aberturas e alterações contratuais.", "legal")
        n_fin, m_fin = campo_setor("Setor Financeiro", "Gestão interna e faturamento da Escrita.", "fin")
        n_bpo, m_bpo = campo_setor("Setor BPO Financeiro", "Gestão financeira terceirizada.", "bpo")
        n_recep, m_recep = campo_setor("Recepção", "Atendimento inicial e documentos.", "recep")
        n_estru, m_estru = campo_setor("Estrutura Física", "Instalações e ambiente.", "estru")
        n_cs, m_cs = campo_setor("Sucesso do Cliente (CS)", "Garantia da melhor experiência.", "cs")

        st.markdown("#### Podemos entrar em contato para falar sobre sua avaliação?")
        contato = st.radio("Selecione uma opção:", ["Sim", "Não"], horizontal=True, label_visibility="collapsed")

        if st.form_submit_button("Finalizar e Enviar"):
            client = conectar_planilha()
            if client:
                try:
                    sh = client.open_by_key(st.secrets["SHEET_ID"])
                    wks = sh.worksheet("respostas")
                    r = st.session_state.respostas

                    dados = [
                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        r['nome'], r['empresa'],
                        r['nota_nps'], r['motivo_nps'],
                        r['clareza'], r['prazos'], r['comunicacao'],
                        r['cordialidade'], r['custo'],
                        n_cont_fisc, m_cont_fisc,
                        n_fol, m_fol,
                        n_rec, m_rec,
                        n_legal, m_legal,
                        n_fin, m_fin,
                        n_bpo, m_bpo,
                        n_recep, m_recep,
                        n_estru, m_estru,
                        n_cs, m_cs,
                        contato
                    ]

                    wks.append_row(dados)
                    st.session_state.passo = 4
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- PASSO 4: SUCESSO ---
elif st.session_state.passo == 4:
    st.balloons()
    st.success("Sua pesquisa foi enviada com sucesso! A Escrita Contabilidade agradece sua participação.")
    if st.button("Enviar nova resposta"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
