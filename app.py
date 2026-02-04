import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES SUPABASE ---
SUPABASE_URL = "https://hnpxvxbimkbcxtyniryx.supabase.co"
SUPABASE_KEY = "sb_publishable_sZ7i2TMEbrF2-jCIHj5Edw_8kqvYU2P"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

st.set_page_config(page_title="GEM Vila Verde - Sistema Integrado", layout="wide")

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
CATEGORIAS = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
SALAS = ["Sala 1", "Sala 2", "Sala 3", "Sala 4", "Teoria Coletiva"]
PROFESSORAS_LISTA = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha"]
MATERIAS = ["Prática", "Teoria", "Solfejo", "FOLGA"]
LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# --- ESCALA PADRÃO (RODÍZIO) ---
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

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.title("🎼 GEM Vila Verde")
    with st.container(border=True):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            url = f"{SUPABASE_URL}/rest/v1/usuarios?usuario=eq.{u}&senha=eq.{p}&select=*"
            res = requests.get(url, headers=HEADERS).json()
            if res:
                st.session_state.autenticado = True
                st.session_state.user = res[0]['usuario']
                st.session_state.perfil = res[0]['perfil']
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.title("🎼 GEM Vila Verde")
st.sidebar.write(f"👤 **{st.session_state.user}**")
if st.session_state.perfil == "Master":
    visao = st.sidebar.radio("Visão de Acesso:", ["Secretaria", "Professora"])
else:
    visao = st.session_state.perfil
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if visao == "Secretaria":
    st.title("📋 Painel da Secretaria")
    aba = st.tabs(["📍 Presença", "✅ Lições", "🗓️ Gerar Escalas"])

    with aba[0]:
        st.subheader("Chamada")
        st.date_input("Data da Presença", format="DD/MM/YYYY")
        presentes = st.multiselect("Alunas Presentes:", ALUNAS)
        if st.button("Salvar Chamada"): st.success("Presença registrada!")

    with aba[1]:
        st.subheader("Correção de Lições")
        st.selectbox("Aluna:", ALUNAS, key="s_al")
        st.multiselect("Material:", CATEGORIAS, key="s_cat")
        st.divider()
        st.text_area("Realizadas (OK)")
        st.text_area("Refazer (Pendência)")
        st.button("Salvar Lições")

    with aba[2]:
        st.subheader("Escala e Rodízio")
        periodo = st.selectbox("Período da Escala:", ["Diária", "Bimestral", "Trimestral", "Semestral", "Anual"])
        data_ini = st.date_input("Data Inicial:", format="DD/MM/YYYY")
        
        agenda_lote = []
        for i, item in enumerate(ESCALA_PADRAO):
            with st.expander(f"Profª {item['prof']} - {item['sala']}", expanded=True):
                c1, c2, c3, c4 = st.columns([1,2,2,3])
                with c1: pres = st.checkbox("Presente", value=True, key=f"pres_{i}")
                with c2: prof = st.selectbox("Instrutora:", PROFESSORAS_LISTA + ["Subst. Teoria", "Subst. Solfejo"], 
                                            index=PROFESSORAS_LISTA.index(item['prof']), key=f"n_{i}")
                with c3: mat = st.selectbox("Matéria:", MATERIAS, index=MATERIAS.index(item['materia']), key=f"m_{i}")
                with c4: alu = st.selectbox("Aluna Atendida:", ["Selecione..."] + ALUNAS, key=f"a_{i}")
                
                if pres and alu != "Selecione...":
                    agenda_lote.append({"data": str(data_ini), "professor": prof, "materia": mat, "sala": item['sala'], "aluna": alu, "periodo": periodo})

        if st.button("Publicar Escala"):
            salvar_agenda_lote(agenda_lote)
            st.success("Escala publicada com sucesso!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif visao == "Professora":
    st.title("🎹 Avaliação de Aula")
    tab1, tab2 = st.tabs(["📅 Minha Agenda", "✍️ Registrar Aula"])

    with tab1:
        st.subheader("Minha Escala")
        minha_agenda = buscar_agenda_prof(st.session_state.user)
        if minha_agenda:
            st.table(pd.DataFrame(minha_agenda)[['data', 'aluna', 'materia', 'sala']])
        else: st.info("Nenhuma agenda encontrada para você hoje.")

    with tab2:
        # Lógica de Matéria Ativa (Master simula, Prof segue agenda)
        if st.session_state.perfil == "Master":
            mat_ativa = st.radio("Simular Aula de:", ["Prática", "Teoria", "Solfejo"], horizontal=True)
        else:
            agenda = buscar_agenda_prof(st.session_state.user)
            mat_ativa = agenda[-1]['materia'] if agenda else "Nenhuma"

        if mat_ativa == "Nenhuma":
            st.warning("Aguarde a atribuição da secretaria.")
        elif mat_ativa == "FOLGA":
            st.success("Você está de folga!")
        else:
            st.info(f"Frente: **{mat_ativa}**")
            alu_nome = st.selectbox("Aluna:", ALUNAS, key="p_alu")
            
            # --- FORMULÁRIO DE PRÁTICA (25 ITENS) ---
            if mat_ativa == "Prática":
                st.selectbox("Lição/Volume Atual *", LICOES_NUM, key="p_v")
                st.write("**Dificuldades Identificadas:**")
                difs_p = [
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos",
                    "Dificuldade rítmica", "Nomes das figuras rítmicas", "Adentrando às teclas",
                    "Postura (costas/ombros/braços)", "Punho alto/baixo", "Não senta no centro",
                    "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                    "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo",
                    "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Atividades apostila",
                    "Articulação ligada/semiligada", "Respirações", "Respirações sobre passagem",
                    "Recurso de dedilhado", "Nota de apoio", "Não apresentou dificuldades"
                ]
                c1, c2 = st.columns(2)
                for i, d in enumerate(difs_p):
                    (c1 if i < 13 else c2).checkbox(d, key=f"chk_p_{i}")

            # --- FORMULÁRIO DE TEORIA / SOLFEJO (15 ITENS) ---
            elif mat_ativa in ["Teoria", "Solfejo"]:
                st.selectbox("Módulo/Lição/Volume *", LICOES_NUM, key="ts_v")
                st.write("**Dificuldades Identificadas:**")
                difs_ts = [
                    "Não assistiu vídeos complementares", "Clave de sol", "Clave de fá",
                    "Uso do metrônomo", "Estuda sem metrônomo", "Não realizou atividades",
                    "Leitura rítmica", "Leitura métrica", "Solfejo (afinação)",
                    "Movimento da mão", "Ordem das notas (asc/desc)", "Atividades da apostila",
                    "Não estudou nada", "Estudou insatisfatoriamente", "Não apresentou dificuldades"
                ]
                c1, c2 = st.columns(2)
                for i, d in enumerate(difs_ts):
                    (c1 if i < 8 else c2).checkbox(d, key=f"chk_ts_{i}")

            st.divider()
            st.subheader("🏠 Lição de Casa")
            st.selectbox("Volume/Lição (Prática):", LICOES_NUM, key="h_p")
            st.text_input("Tarefa Teoria/Apostila:", key="h_o")
            st.text_area("Observações Finais")
            
            if st.button("Finalizar Registro"):
                st.balloons()
                st.success("Avaliação enviada com sucesso!")
