import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Rodízio por Turmas", layout="wide")

# --- DEFINIÇÃO DAS TURMAS FIXAS ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 (1ª Aula)", "09h35 (2ª Aula)", "10h10 (3ª Aula)", "10h45 (Aula Final)"]

if "config_oficial" not in st.session_state:
    st.session_state.config_oficial = None

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Escala de Teoria/Solfejo por Turma")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_conf, tab_chamada, tab_corr = st.tabs(["⚙️ Definir Professoras", "📍 Chamada", "✅ Correção"])

    with tab_conf:
        st.subheader("Atribuição das Salas Coletivas")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Teoria")
            p_t1 = st.selectbox("Professor Teoria - Turma 1:", PROFESSORAS_LISTA, index=0)
            p_t2 = st.selectbox("Professor Teoria - Turma 2:", PROFESSORAS_LISTA, index=1)
            p_t3 = st.selectbox("Professor Teoria - Turma 3:", PROFESSORAS_LISTA, index=2)
        
        with c2:
            st.markdown("#### 🔊 Solfejo")
            s_t1 = st.selectbox("Professor Solfejo - Turma 1:", PROFESSORAS_LISTA, index=3)
            s_t2 = st.selectbox("Professor Solfejo - Turma 2:", PROFESSORAS_LISTA, index=4)
            s_t3 = st.selectbox("Professor Solfejo - Turma 3:", PROFESSORAS_LISTA, index=5)
            
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA)

        if st.button("🚀 Gerar Grade de Rotação", use_container_width=True):
            # Identifica quem sobrou para as salas de prática 1 a 7
            fixas = [p_t1, p_t2, p_t3, s_t1, s_t2, s_t3]
            profs_pratica = [p for p in PROFESSORAS_LISTA if p not in folgas and p not in fixas]
            
            st.session_state.config_oficial = {
                "teoria": {"Turma 1": p_t1, "Turma 2": p_t2, "Turma 3": p_t3},
                "solfejo": {"Turma 1": s_t1, "Turma 2": s_t2, "Turma 3": s_t3},
                "pratica": profs_pratica,
                "data": datetime.now().strftime("%d/%m/%Y")
            }
            st.success("Escala Publicada! As professoras já podem visualizar seus atendimentos.")

    with tab_chamada:
        st.subheader("📍 Lista de Presença")
        turma_sel = st.selectbox("Turma:", ["Turma 1", "Turma 2", "Turma 3"])
        for aluna in TURMAS[turma_sel]:
            st.checkbox(aluna, key=f"pres_{aluna}")

    with tab_corr:
        st.subheader("✅ Correção de Atividades")
        st.selectbox("Aluna:", [a for lista in TURMAS.values() for a in lista])
        st.multiselect("Materiais:", ["MSA", "Apostila", "Pauta"])
        st.text_area("Observações de Correção:")
        st.button("Salvar")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Diário da Professora")
    
    if not st.session_state.config_oficial:
        st.warning("Aguardando a Secretaria configurar as professoras de cada turma.")
    else:
        conf = st.session_state.config_oficial
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário da Aula:", options=HORARIOS)

        # Lógica de Rotação (Qual turma está onde em cada hora)
        rotacao = {
            HORARIOS[0]: {"Teoria": "Turma 1", "Solfejo": "Turma 2", "Prática": "Turma 3"},
            HORARIOS[1]: {"Teoria": "Turma 2", "Solfejo": "Turma 3", "Prática": "Turma 1"},
            HORARIOS[2]: {"Teoria": "Turma 3", "Solfejo": "Turma 1", "Prática": "Turma 2"},
            HORARIOS[3]: {"Teoria": "Final", "Solfejo": "Final", "Prática": "Final"}
        }

        # Determinar local e aluna
        local = "Folga / Auxílio"
        atend = "---"
        materia = "---"
        turma_da_hora_teoria = rotacao[h_atual]["Teoria"]
        turma_da_hora_solfejo = rotacao[h_atual]["Solfejo"]

        # Verifica se ela é a prof de Teoria da turma que está em aula agora
        if h_atual != HORARIOS[3]:
            if p_nome == conf["teoria"].get(turma_da_hora_teoria):
                local = "Sala 8 (Teoria)"
                atend = turma_da_hora_teoria
                materia = "Teoria"
            elif p_nome == conf["solfejo"].get(turma_da_hora_solfejo):
                local = "Sala 9 (Solfejo)"
                atend = turma_da_hora_solfejo
                materia = "Solfejo"
            elif p_nome in conf["pratica"]:
                idx = conf["pratica"].index(p_nome)
                local = f"Sala {idx + 1} (Prática)"
                turma_prat = rotacao[h_atual]["Prática"]
                atend = TURMAS[turma_prat][idx] if idx < len(TURMAS[turma_prat]) else "Extra"
                materia = "Prática"

        # --- EXIBIÇÃO ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("📍 LOCAL", local)
            st.subheader(f"👤 Atendendo: {atend}")
        with c2:
            st.metric("⏱️ TURNO", h_atual.split(" ")[0])
            st.write(f"📖 **Matéria:** {materia}")

        st.divider()

        # --- FORMULÁRIOS TÉCNICOS ---
        if materia == "Prática":
            st.subheader("Checklist Prática (25 Itens)")
            difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respiração", "Passagem", "Dedilhado", "Nota Apoio", "Dificuldades"]
            cols = st.columns(3)
            for i, d in enumerate(difs): cols[i%3].checkbox(d, key=f"p_{i}")
        elif materia in ["Teoria", "Solfejo"]:
            st.subheader(f"Avaliação de {materia} - {atend}")
            for item in ["Presença", "Participação", "Exercícios", "Vídeos", "Comportamento"]: st.checkbox(item)

        st.text_input("Tarefa para Casa:")
        st.text_area("Observações da Aula:")
        if st.button("Salvar Aula"): st.success("Aula registrada com sucesso!")
