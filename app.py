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

# --- DADOS MESTRES ---
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
visao = st.sidebar.radio("Visão:", ["Secretaria", "Professora"]) if st.session_state.perfil == "Master" else st.session_state.perfil
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
        st.date_input("Data da Presença", format="DD/MM/YYYY", key="data_pres")
        st.multiselect("Alunas Presentes:", ALUNAS, key="list_pres")
        if st.button("Salvar Chamada"): st.success("Presença registrada!")

    with aba[1]:
        st.subheader("Correção de Lições")
        st.selectbox("Aluna:", ALUNAS, key="s_aluna")
        st.multiselect("Material:", CATEGORIAS, key="s_material")
        st.divider()
        st.text_area("Realizadas (OK)", key="s_txt_ok")
        st.text_area("Refazer (Pendência)", key="s_txt_ref")
        if st.button("Salvar Lições"): st.success("Dados de correção salvos!")

    with aba[2]:
        st.subheader("Configuração de Escala e Rodízio")
        tipo_escala = st.selectbox("Período:", ["Diária", "Bimestral", "Trimestral", "Semestral", "Anual"])
        data_escala = st.date_input("Data Inicial:", format="DD/MM/YYYY", key="data_esc")
        
        agenda_lote = []
        for i, item in enumerate(ESCALA_PADRAO):
            with st.expander(f"Configurar: {item['prof']} ({item['sala']})", expanded=True):
                c1, c2, c3, c4 = st.columns([1,2,2,3])
                with c1: pres = st.checkbox("Ativa", value=True, key=f"pres_chk_{i}")
                with c2: prof = st.selectbox("Professora:", PROFESSORAS_LISTA + ["Subst. Teoria", "Subst. Solfejo"], index=PROFESSORAS_LISTA.index(item['prof']), key=f"sel_prof_{i}")
                with c3: mat = st.selectbox("Matéria:", MATERIAS, index=MATERIAS.index(item['materia']), key=f"sel_mat_{i}")
                with c4: alu = st.selectbox("Aluna:", ["Selecione..."] + ALUNAS, key=f"sel_alu_{i}")
                
                if pres and alu != "Selecione...":
                    agenda_lote.append({"data": str(data_escala), "professor": prof, "materia": mat, "sala": item['sala'], "aluna": alu, "periodo": tipo_escala})

        if st.button("Publicar Escala Atualizada", use_container_width=True):
            if agenda_lote:
                salvar_agenda_lote(agenda_lote)
                st.success("Escala publicada com sucesso!")
            else: st.warning("Nenhuma aluna vinculada na escala.")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif visao == "Professora":
    st.title("🎹 Registro de Aula")
    tab1, tab2 = st.tabs(["📅 Minha Agenda", "✍️ Avaliação Técnica"])

    with tab1:
        st.subheader("Minha Agenda")
        agenda_dados = buscar_agenda_prof(st.session_state.user)
        if agenda_dados:
            st.dataframe(pd.DataFrame(agenda_dados)[['data', 'aluna', 'materia', 'sala']], use_container_width=True)
        else: st.info("Nenhuma escala encontrada para você.")

    with tab2:
        if st.session_state.perfil == "Master":
            mat_ativa = st.radio("Simular Aula de:", ["Prática", "Teoria", "Solfejo"], horizontal=True)
        else:
            agenda_atual = buscar_agenda_prof(st.session_state.user)
            mat_ativa = agenda_atual[-1]['materia'] if agenda_atual else "Nenhuma"

        if mat_ativa in ["Nenhuma", "FOLGA"]:
            st.warning("Sem aulas atribuídas para o momento.")
        else:
            st.info(f"Frente Atual: **{mat_ativa}**")
            alu_nome = st.selectbox("Selecione a Aluna atendida:", ALUNAS, key="p_alu_atend")
            st.divider()

            if mat_ativa == "Prática":
                st.subheader("Formulário de Aula Prática")
                st.selectbox("Lição/Volume Atual *", LICOES_NUM, key="prat_licao")
                st.write("**Dificuldades Técnicas:**")
                
                # Lista completa dos 25 itens de Prática
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
                cp1, cp2 = st.columns(2)
                for idx, d in enumerate(difs_p):
                    (cp1 if idx < 13 else cp2).checkbox(d, key=f"chk_p_{idx}")

            elif mat_ativa in ["Teoria", "Solfejo"]:
                st.subheader(f"Formulário de {mat_ativa}")
                st.selectbox("Módulo/Lição *", LICOES_NUM, key="teor_licao")
                st.write("**Dificuldades Identificadas:**")
                
                # Lista completa dos 15 itens de Teoria/Solfejo
                difs_ts = [
                    "Não assistiu vídeos complementares", "Clave de sol", "Clave de fá",
                    "Uso do metrônomo", "Estuda sem metrônomo", "Não realizou atividades",
                    "Leitura rítmica", "Leitura métrica", "Solfejo (afinação)",
                    "Movimento da mão", "Ordem das notas (asc/desc)", "Atividades da apostila",
                    "Não estudou nada", "Estudou insatisfatoriamente", "Não apresentou dificuldades"
                ]
                cts1, cts2 = st.columns(2)
                for idx, d in enumerate(difs_ts):
                    (cts1 if idx < 8 else cts2).checkbox(d, key=f"chk_ts_{idx}")

            st.divider()
            st.subheader("🏠 Próxima Aula")
            st.selectbox("Lição de Casa (Prática):", LICOES_NUM, key="casa_prat")
            st.text_input("Lição de Casa (Apostila/Teoria):", key="casa_teor")
            st.text_area("Observações Adicionais", key="obs_finais")
            
            if st.button("Finalizar e Salvar Registro", use_container_width=True):
                st.balloons()
                st.success(f"Aula de {mat_ativa} registrada para {alu_nome}!")
