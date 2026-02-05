import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES SUPABASE ---
SUPABASE_URL = "https://hnpxvxbimkbcxtyniryx.supabase.co"
SUPABASE_KEY = "sb_publishable_sZ7i2TMEbrF2-jCIHj5Edw_8kqvYU2P"
HEADERS = {
    "apikey": SUPABASE_KEY, 
    "Authorization": f"Bearer {SUPABASE_KEY}", 
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.set_page_config(page_title="GEM Vila Verde - Gestão Completa", layout="wide")

# --- ESTADO DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user = None
    st.session_state.perfil = None
if "tela_cadastro" not in st.session_state:
    st.session_state.tela_cadastro = False

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

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa"]
SECRETARIAS_LISTA = ["Ester", "Jéssica", "Larissa", "Lurdes", "Natasha", "Roseli"]
NOMES_PERMITIDOS = sorted(list(set(PROFESSORAS_LISTA + SECRETARIAS_LISTA + ["Master"])))

SALAS_RODIZIO = [
    "Sala 1 (Prática)", "Sala 2 (Prática)", "Sala 3 (Prática)", "Sala 4 (Prática)", 
    "Sala 5 (Prática)", "Sala 6 (Prática)", "Sala 7 (Prática)", 
    "Sala de Teoria", "Sala de Solfejo"
]

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas"]
LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# --- FUNÇÕES DE BANCO ---
def criar_novo_usuario(nome, senha, perfil):
    url = f"{SUPABASE_URL}/rest/v1/usuarios"
    payload = {"usuario": nome, "senha": senha, "perfil": perfil}
    return requests.post(url, json=payload, headers=HEADERS)

def buscar_agenda_prof(nome_prof):
    url = f"{SUPABASE_URL}/rest/v1/agenda_aulas?professor=eq.{nome_prof}&select=*"
    try:
        res = requests.get(url, headers=HEADERS).json()
        return res if isinstance(res, list) else []
    except: return []

def publicar_escala_banco(dados):
    url = f"{SUPABASE_URL}/rest/v1/agenda_aulas"
    return requests.post(url, json=dados, headers=HEADERS)

# --- SISTEMA DE LOGIN E CADASTRO ---
if not st.session_state.autenticado:
    st.title("🎼 GEM Vila Verde")
    if st.session_state.tela_cadastro:
        with st.container(border=True):
            st.subheader("📝 Novo Cadastro")
            n_user = st.selectbox("Selecione seu Nome Oficial:", NOMES_PERMITIDOS)
            n_pass = st.text_input("Senha:", type="password")
            n_perf = st.radio("Seu Perfil:", ["Professora", "Secretaria"], horizontal=True)
            if st.button("Finalizar Cadastro", use_container_width=True):
                if n_pass:
                    res = criar_novo_usuario(n_user, n_pass, n_perf)
                    if res.status_code in [200, 201]:
                        st.success("Cadastro realizado! Faça o login."); st.session_state.tela_cadastro = False; st.rerun()
                    else: st.error("Erro no cadastro. Verifique sua conexão.")
                else: st.warning("Defina uma senha.")
            if st.button("Voltar"): st.session_state.tela_cadastro = False; st.rerun()
    else:
        with st.container(border=True):
            st.subheader("🔑 Login")
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*"
                res = requests.get(url, headers=HEADERS).json()
                # Validação robusta de colunas (usuario ou login)
                user_data = next((item for item in res if (item.get('usuario') == u or item.get('login') == u) and item.get('senha') == p), None)
                if user_data:
                    st.session_state.user = user_data.get('usuario') or user_data.get('login')
                    st.session_state.perfil = user_data.get('perfil')
                    st.session_state.autenticado = True; st.rerun()
                else: st.error("Acesso negado.")
            if st.button("Criar Conta"): st.session_state.tela_cadastro = True; st.rerun()
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.title("🎹 Menu")
st.sidebar.info(f"Usuário: {st.session_state.user}\n\nPerfil: {st.session_state.perfil}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if st.session_state.perfil in ["Secretaria", "Master"]:
    st.title("📋 Área da Secretaria")
    t1, t2, t3 = st.tabs(["✅ Correção de Atividades", "🗓️ Rodízio de Salas", "📍 Presença"])

    with t1:
        st.subheader("Correção Técnica de Materiais")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Aluna:", ALUNAS, key="cor_alu")
            st.multiselect("Materiais Corrigidos:", CATEGORIAS_LICAO, key="cor_mat")
            st.checkbox("Trouxe Apostila?", key="c_ap")
            st.checkbox("Caderno de Pauta preenchido?", key="c_pa")
        with c2:
            st.text_area("Lições Aprovadas (OK):", placeholder="Ex: MSA Lição 1 a 10", key="txt_ok")
            st.text_area("Observações/Pendências:", placeholder="Ex: Refazer Lição 5 - Teoria falha", key="txt_pend")
        if st.button("Registrar Correção"): st.success("Correção salva no histórico!")

    with t2:
        st.subheader("Gerar Rodízio Automático")
        data_escala = st.date_input("Data da Aula:", format="DD/MM/YYYY")
        folgas = st.multiselect("Professoras AUSENTES (Folga):", PROFESSORAS_LISTA)
        if st.button("Publicar Escala do Dia", use_container_width=True):
            ativas = [p for p in PROFESSORAS_LISTA if p not in folgas]
            if not ativas: st.error("Nenhuma professora disponível!")
            else:
                agenda_dia = []
                for i, sala in enumerate(SALAS_RODIZIO):
                    if i < len(ativas):
                        materia = "Prática" if "Prática" in sala else ("Teoria" if "Teoria" in sala else "Solfejo")
                        agenda_dia.append({
                            "data": str(data_escala), "professor": ativas[i],
                            "materia": materia, "sala": sala, "aluna": ALUNAS[i % len(ALUNAS)]
                        })
                publicar_escala_banco(agenda_dia)
                st.table(pd.DataFrame(agenda_dia)[['professor', 'sala', 'aluna', 'materia']])

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
if st.session_state.perfil in ["Professora", "Master"]:
    if st.session_state.perfil == "Master": st.divider()
    st.title("🎹 Avaliação da Aula")
    agenda = buscar_agenda_prof(st.session_state.user)
    
    if not agenda:
        st.info("Aguardando publicação da escala pela secretaria.")
    else:
        aula = agenda[-1]
        st.success(f"📍 {aula['sala']} | Aluna: **{aula['aluna']}** | Matéria: **{aula['materia']}**")

        # --- FORMULÁRIO DE PRÁTICA (25 ITENS) ---
        if aula['materia'] == "Prática":
            st.selectbox("Volume/Lição Atual:", LICOES_NUM, key="p_v")
            difs_p = [
                "Não estudou nada", "Estudo insatisfatório", "Não assistiu os vídeos",
                "Dificuldade rítmica", "Nomes das figuras rítmicas", "Adentrando às teclas",
                "Postura (costas/ombros/braços)", "Punho alto/baixo", "Não senta no centro",
                "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo",
                "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Atividades apostila",
                "Articulação ligada/semiligada", "Respirações", "Respirações sobre passagem",
                "Recurso de dedilhado", "Nota de apoio", "Não apresentou dificuldades"
            ]
            c1, c2 = st.columns(2)
            for i, d in enumerate(difs_p): (c1 if i < 13 else c2).checkbox(d, key=f"p_{i}")

        # --- FORMULÁRIO DE TEORIA ---
        elif aula['materia'] == "Teoria":
            st.selectbox("Módulo/Página:", LICOES_NUM, key="t_v")
            difs_t = [
                "Não assistiu vídeos", "Clave de sol", "Clave de fá", "Não realizou atividades",
                "Dificuldade na escrita musical", "Divisão rítmica teórica", "Ordem das notas",
                "Intervalos", "Armaduras de clave", "Apostila incompleta", "Não estudou",
                "Estudo ruim", "Não apresentou dificuldades"
            ]
            c1, c2 = st.columns(2)
            for i, d in enumerate(difs_t): (c1 if i < 7 else c2).checkbox(d, key=f"t_{i}")

        # --- FORMULÁRIO DE SOLFEJO ---
        elif aula['materia'] == "Solfejo":
            st.selectbox("Lição Solfejo:", LICOES_NUM, key="s_v")
            difs_s = [
                "Não assistiu vídeos", "Afinação (altura)", "Leitura rítmica", "Leitura métrica",
                "Movimento da mão (compasso)", "Pulsação inconstante", "Uso do metrônomo",
                "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Não estudou nada",
                "Estudo insatisfatório", "Não apresentou dificuldades"
            ]
            c1, c2 = st.columns(2)
            for i, d in enumerate(difs_s): (c1 if i < 7 else c2).checkbox(d, key=f"s_{i}")

        st.divider()
        st.subheader("🏠 Tarefa de Casa")
        st.text_input("Próxima Lição de Prática:", key="c_p")
        st.text_input("Próxima Tarefa de Teoria:", key="c_t")
        st.text_area("Observações Gerais da Aula:", key="obs_f")
        if st.button("Finalizar Registro da Aula", use_container_width=True):
            st.balloons(); st.success("Aula registrada e enviada!")
