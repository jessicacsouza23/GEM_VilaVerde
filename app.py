import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES SUPABASE ---
SUPABASE_URL = "https://hnpxvxbimkbcxtyniryx.supabase.co"
SUPABASE_KEY = "sb_publishable_sZ7i2TMEbrF2-jCIHj5Edw_8kqvYU2P"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

st.set_page_config(page_title="GEM Vila Verde - Gestão Integrada", layout="wide")

# --- ESTADO DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user = None
    st.session_state.perfil = None

# --- DADOS MESTRES (LISTAS OFICIAIS) ---
ALUNAS = [
    "Amanda S. - Parque do Carmo II", "Ana Marcela S. - Vila Verde", "Caroline C. - Vila Ré",
    "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá Velha", "Gabrielly V. - Vila Verde",
    "Heloísa R. - Vila Verde", "Ingrid M. - Parque do Carmo II", "Júlia Cristina - União de Vila Nova",
    "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá Velha", "Mellina S. - Jardim Lígia",
    "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", "Rebeca R. - Vila Ré",
    "Rebecca A. - Vila Verde", "Rebeka S. - Jardim Lígia", "Sarah S. - Vila Verde",
    "Stephany O. - Vila Curuçá Velha", "Vitória A. - Vila Verde", "Vitória Bella T. - Vila Verde"
]

# LISTA OFICIAL PARA CRIAÇÃO DE USUÁRIOS (Trava de Segurança)
NOMES_PERMITIDOS = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Secretaria", "Subst. Teoria", "Subst. Solfejo", "Master"]

CATEGORIAS = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
SALAS = ["Sala 1", "Sala 2", "Sala 3", "Sala 4", "Teoria Coletiva"]
PROFESSORAS_LISTA = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha"]
MATERIAS = ["Prática", "Teoria", "Solfejo", "FOLGA"]
LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

ESCALA_PADRAO = [
    {"prof": "Ester", "materia": "Prática", "sala": "Sala 1"},
    {"prof": "Jéssica", "materia": "Prática", "sala": "Sala 2"},
    {"prof": "Larissa", "materia": "Teoria", "sala": "Teoria Coletiva"},
    {"prof": "Lourdes", "materia": "Solfejo", "sala": "Sala 3"},
    {"prof": "Natasha", "materia": "Prática", "sala": "Sala 4"},
]

# --- FUNÇÕES ---
def salvar_agenda_lote(dados):
    url = f"{SUPABASE_URL}/rest/v1/agenda_aulas"
    return requests.post(url, json=dados, headers=HEADERS)

def buscar_agenda_prof(nome_prof):
    url = f"{SUPABASE_URL}/rest/v1/agenda_aulas?professor=eq.{nome_prof}&select=*"
    try:
        res = requests.get(url, headers=HEADERS).json()
        return res if isinstance(res, list) else []
    except: return []

def criar_novo_usuario(nome, senha, perfil):
    url = f"{SUPABASE_URL}/rest/v1/usuarios"
    payload = {"usuario": nome, "senha": senha, "perfil": perfil}
    return requests.post(url, json=payload, headers=HEADERS)

# --- LOGIN ---
if not st.session_state.autenticado:
    st.title("🎼 GEM Vila Verde")
    with st.container(border=True):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            url = f"{SUPABASE_URL}/rest/v1/usuarios?usuario=eq.{u}&senha=eq.{p}&select=*"
            res = requests.get(url, headers=HEADERS).json()
            if res and isinstance(res, list) and len(res) > 0:
                st.session_state.user = res[0].get('usuario', u)
                st.session_state.perfil = res[0].get('perfil', 'Professora')
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.title("🎼 GEM Vila Verde")
st.sidebar.write(f"👤 **{st.session_state.user}**")

opcoes_menu = ["Secretaria", "Professora"]
if st.session_state.perfil == "Master":
    opcoes_menu.append("Configurações Master")
    visao = st.sidebar.radio("Navegação:", opcoes_menu)
else:
    visao = st.session_state.perfil

if st.sidebar.button("Sair / Logout"):
    st.session_state.autenticado = False
    st.rerun()

# ==========================================
#          MÓDULO CONFIGURAÇÕES MASTER
# ==========================================
if visao == "Configurações Master":
    st.title("⚙️ Gerenciamento de Acessos (Master)")
    
    with st.container(border=True):
        st.subheader("Criar Novo Usuário")
        st.write("Selecione um nome da lista oficial para gerar um acesso.")
        
        with st.form("form_criacao_user"):
            # Trava: Só permite nomes da NOMES_PERMITIDOS
            nome_selecionado = st.selectbox("Escolha a Instrutora/Responsável:", NOMES_PERMITIDOS)
            senha_nova = st.text_input("Defina a Senha de Acesso:", type="password")
            perfil_novo = st.selectbox("Nível de Acesso:", ["Professora", "Secretaria", "Master"])
            
            if st.form_submit_button("Gerar Acesso"):
                if senha_nova:
                    res = criar_novo_usuario(nome_selecionado, senha_nova, perfil_novo)
                    if res.status_code in [200, 201]:
                        st.success(f"Acesso criado para {nome_selecionado} com sucesso!")
                    else:
                        st.error("Erro: Este usuário já possui cadastro ou houve falha na conexão.")
                else:
                    st.warning("Por favor, defina uma senha.")

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
elif visao == "Secretaria":
    st.title("📋 Painel da Secretaria")
    aba = st.tabs(["📍 Presença", "✅ Lições", "🗓️ Escalas e Rodízios"])

    with aba[2]:
        st.subheader("Configuração de Escala por Período
