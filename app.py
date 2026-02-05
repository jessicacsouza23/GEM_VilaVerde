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

st.set_page_config(page_title="GEM Vila Verde - Gestão Integrada", layout="wide")

# --- ESTADO DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user = None
    st.session_state.perfil = None
if "tela_cadastro" not in st.session_state:
    st.session_state.tela_cadastro = False

# --- DADOS MESTRES (FECHADOS) ---
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

# --- FUNÇÕES ---
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

# --- LOGIN / CADASTRO ---
if not st.session_state.autenticado:
    st.title("🎼 GEM Vila Verde")
    if st.session_state.tela_cadastro:
        with st.container(border=True):
            st.subheader("Criar Nova Conta")
            n_user = st.selectbox("Selecione seu Nome Oficial:", NOMES_PERMITIDOS)
            n_pass = st.text_input("Defina uma Senha:", type="password")
            n_perf = st.selectbox("Seu Perfil:", ["Professora", "Secretaria", "Master"])
            if st.button("Finalizar Cadastro", use_container_width=True):
                if n_pass:
                    res = criar_novo_usuario(n_user, n_pass, n_perf)
                    if res.status_code in [200, 201]:
                        st.success("Cadastro realizado! Faça o login."); st.session_state.tela_cadastro = False; st.rerun()
                    else: st.error("Erro ao cadastrar. Verifique se o usuário já existe no banco.")
                else: st.warning("Senha obrigatória.")
            if st.button("Voltar"): st.session_state.tela_cadastro = False; st.rerun()
    else:
        with st.container(border=True):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                url = f"{SUPABASE_URL}/rest/v1/usuarios?usuario=eq.{u}&senha=eq.{p}&select=*"
                res = requests.get(url, headers=HEADERS).json()
                if res and len(res) > 0:
                    st.session_state.user = res[0]['usuario']; st.session_state.perfil = res[0]['perfil']; st.session_state.autenticado = True; st.rerun()
                else: st.error("Usuário ou senha inválidos.")
            if st.button("Ainda não tenho conta"): st.session_state.tela_cadastro = True; st.rerun()
    st.stop()

# --- INTERFACE ---
st.sidebar.title("🎼 GEM Vila Verde")
st.sidebar.write(f"👤 **{st.session_state.user}**")
visao = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"]) if st.session_state.perfil == "Master" else st.session_state.perfil
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if visao == "Secretaria":
    st.title("📋 Painel da Secretaria")
    tab_chamada, tab_correcao, tab_escala = st.tabs(["📍 Chamada", "✅ Correção de Atividades", "🗓️ Rodízio Automático"])

    with tab_correcao:
        st.subheader("Registro de Atividades (Lição de Casa)")
        c1, c2 = st.columns(2)
        with c1:
            alu_corr = st.selectbox("Aluna:", ALUNAS, key="corr_alu")
            st.multiselect("Materiais Corrigidos:", CATEGORIAS_LICAO)
            st.checkbox("Trouxe a apostila?", key="check_ap")
            st.checkbox("Fez os exercícios de pauta?", key="check_pa")
        with c2:
            st.text_area("Lições Realizadas (OK):", placeholder="O que foi aprovado?", key="corr_ok")
            st.text_area("Pendências (Para Refazer):", placeholder="O que precisa de correção?", key="corr_pend")
        if st.button("Salvar Correção"): st.success("Registro de correção salvo!")

    with tab_escala:
        st.subheader("Gerar Rodízio por Folga")
        data_aula = st.date_input("Data da Aula:", format="DD/MM/YYYY")
        folgas = st.multiselect("Quem está de FOLGA hoje?", PROFESSORAS_LISTA)
        
        if st.button("Publicar Escala Automática", use_container_width=True):
            disponiveis = [p for p in PROFESSORAS_LISTA if p not in folgas]
            if not disponiveis: st.error("Nenhuma professora disponível!")
            else:
                nova_agenda = []
                for i, sala in enumerate(SALAS_RODIZIO):
                    if i < len(disponiveis):
                        mat = "Prática" if "Prática" in sala else ("Teoria" if "Teoria" in sala else "Solfejo")
                        nova_agenda.append({
                            "data": str(data_aula), "professor": disponiveis[i],
                            "materia": mat, "sala": sala, "aluna": ALUNAS[i % len(ALUNAS)]
                        })
                publicar_escala_banco(nova_agenda)
                st.success("Rodízio publicado!"); st.table(pd.DataFrame(nova_agenda)[['professor', 'sala', 'aluna']])

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif visao == "Professora":
    st.title("🎹 Registro de Aula")
    agenda = buscar_agenda_prof(st.session_state.user)
    
    if not agenda:
        st.info("Você não possui escala ativa para hoje ou está de folga.")
    else:
        aula = agenda[-1]
        st.info(f"📍 Sala: **{aula['sala']}** | Aluna: **{aula['aluna']}** | Matéria: **{aula['materia']}**")
        st.divider()

        # FORMULÁRIO DE PRÁTICA (OS 25 ITENS)
        if aula['materia'] == "Prática":
            st.subheader("Formulário de Prática")
            st.selectbox("Lição/Volume Atual *", LICOES_NUM, key="p_v")
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

        # FORMULÁRIO DE TEORIA
        elif aula['materia'] == "Teoria":
            st.subheader("Formulário de Teoria")
            st.selectbox("Módulo/Página *", LICOES_NUM, key="t_v")
            difs_t = [
                "Não assistiu vídeos complementares", "Clave de sol", "Clave de fá", 
                "Não realizou atividades", "Dificuldade na escrita musical", 
                "Divisão rítmica teórica", "Ordem das notas (asc/desc)", 
                "Intervalos", "Armaduras de clave", "Apostila incompleta", 
                "Não estudou nada", "Estudo insatisfatório", "Não apresentou dificuldades"
            ]
            c1, c2 = st.columns(2)
            for i, d in enumerate(difs_t): (c1 if i < 7 else c2).checkbox(d, key=f"t_{i}")

        # FORMULÁRIO DE SOLFEJO
        elif aula['materia'] == "Solfejo":
            st.subheader("Formulário de Solfejo")
            st.selectbox("Lição Solfejo *", LICOES_NUM, key="s_v")
            difs_s = [
                "Não assistiu vídeos", "Afinação (altura das notas)", 
                "Leitura rítmica", "Leitura métrica", "Movimento da mão (compasso)", 
                "Pulsação inconstante", "Uso do metrônomo", "Estuda sem metrônomo", 
                "Clave de sol", "Clave de fá", "Não estudou nada", 
                "Estudo insatisfatório", "Não apresentou dificuldades"
            ]
            c1, c2 = st.columns(2)
            for i, d in enumerate(difs_s): (c1 if i < 7 else c2).checkbox(d, key=f"s_{i}")

        st.divider()
        st.subheader("🏠 Próxima Aula")
        st.text_input("Tarefa de Prática para Casa:", key="casa_p")
        st.text_input("Tarefa de Teoria/Apostila:", key="casa_t")
        st.text_area("Observações Finais da Aula:", key="obs_final")
        if st.button("Finalizar e Salvar Registro"):
            st.balloons(); st.success("Aula registrada com sucesso!")
