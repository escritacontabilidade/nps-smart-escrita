import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NPS Smart - Escrita", page_icon="💡", layout="centered")

def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Limpeza da chave para evitar erro de PEM
        pk = creds_dict["private_key"].replace("\\n", "\n").strip().strip('"').strip("'")
        creds_dict["private_key"] = pk
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

# --- 2. ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #F4F6F8; }
    .header-container { background-color: #0E3A5D; padding: 1.5rem; border-radius: 10px; margin-bottom: 20px; }
    .header-title { color: #FFFFFF !important; font-size: 1.8rem; font-weight: bold; }
    .stSelectbox label, .stSlider label, .stTextInput label, .stTextArea label { color: #0E3A5D !important; font-weight: bold; }
    div.stButton > button { background-color: #1F5E8C !important; color: white !important; width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    hr { border: 0; border-top: 1px solid #dce1e6; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><h1 class="header-title">Pesquisa de Satisfação - Área Smart</h1></div>', unsafe_allow_html=True)

# --- 3. CONTROLE DE FLUXO ---
if 'passo' not in st.session_state:
    st.session_state.passo = 1
    st.session_state.respostas = {}

# --- PASSO 1: IDENTIFICAÇÃO E NPS GERAL ---
if st.session_state.passo == 1:
    with st.form("etapa1"):
        nome = st.text_input("Seu Nome:")
        empresa = st.text_input("Sua Empresa:")
        st.write("---")
        nota_nps = st.select_slider("De 0 a 10, o quanto recomendaria a Área Smart?", options=list(range(11)), value=10)
        motivo_nps = st.text_area("O que motivou sua nota?")
        
        if st.form_submit_button("Próximo: Avaliação Geral"):
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
        
        if st.form_submit_button("Próximo: Avaliar Departamentos"):
            st.session_state.respostas.update({
                'clareza': clareza, 'prazos': prazos, 'comunicacao': comunicacao, 
                'cordialidade': cordialidade, 'custo': custo
            })
            st.session_state.passo = 3
            st.rerun()

# --- PASSO 3: DEPARTAMENTOS (O MAIS IMPORTANTE) ---
elif st.session_state.passo == 3:
    st.subheader("Avaliação por Departamento")
    st.info("Para cada setor, dê uma nota e, se desejar, sugira uma melhoria.")
    
    with st.form("etapa3"):
        def campo_setor(titulo, chave):
            st.markdown(f"**{titulo}**")
            col_n, col_m = st.columns([1, 3])
            nota = col_n.selectbox(f"Nota", ["Não uso"] + list(range(11)), index=11, key=f"n_{chave}")
            melhoria = col_m.text_input("O que podemos melhorar?", key=f"m_{chave}", placeholder="Opcional")
            st.write("---")
            return nota, melhoria

        n_cont, m_cont = campo_setor("Contábil / Fiscal", "cont")
        n_fol, m_fol = campo_setor("Pessoal (Folha)", "fol")
        n_rec, m_rec = campo_setor("Recrutamento", "rec")
        n_smart, m_smart = campo_setor("Setor Smart", "smart")
        n_legal, m_legal = campo_setor("Setor Legal / Societário", "legal")
        n_fin, m_fin = campo_setor("Setor Financeiro", "fin")
        n_bpo, m_bpo = campo_setor("Setor BPO Financeiro", "bpo")
        n_recep, m_recep = campo_setor("Recepção", "recep")
        n_estru, m_estru = campo_setor("Estrutura Física", "estru")
        n_cs, m_cs = campo_setor("Sucesso do Cliente (CS)", "cs")

        contato = st.radio("Podemos entrar em contato para falar sobre sua avaliação?", ["Sim", "Não"], horizontal=True)

        if st.form_submit_button("Finalizar e Enviar Pesquisa"):
            client = conectar_planilha()
            if client:
                try:
                    sh = client.open_by_key(st.secrets["SHEET_ID"])
                    wks = sh.worksheet("respostas")
                    r = st.session_state.respostas
                    
                    # MONTAGEM EXATA DAS 31 COLUNAS
                    dados = [
                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"), # 1
                        r['nome'], r['empresa'],                      # 2, 3
                        r['nota_nps'], r['motivo_nps'],               # 4, 5
                        r['clareza'], r['prazos'], r['comunicacao'],  # 6, 7, 8
                        r['cordialidade'], r['custo'],                # 9, 10
                        n_cont, m_cont,                               # 11, 12
                        n_fol, m_fol,                                 # 13, 14
                        n_rec, m_rec,                                 # 15, 16
                        n_smart, m_smart,                             # 17, 18
                        n_legal, m_legal,                             # 19, 20
                        n_fin, m_fin,                                 # 21, 22
                        n_bpo, m_bpo,                                 # 23, 24
                        n_recep, m_recep,                             # 25, 26
                        n_estru, m_estru,                             # 27, 28
                        n_cs, m_cs,                                   # 29, 30
                        contato                                       # 31
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
        st.session_state.passo = 1
        st.rerun()
