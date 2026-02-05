import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Rotação Total", layout="wide")

# --- BANCO DE DADOS FIXO ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

TODAS_ALUNAS = sorted([aluna for lista in TURMAS.values() for aluna in lista])
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS_LABELS = ["08h45 (H1)", "09h35 (H2)", "10h10 (H3)", "10h45 (Aula Final)"]

if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Sistema de Rotação Dinâmica")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_admin = st.tabs(["🗓️ Planejar Sábados", "📍 Chamada", "⚠️ Administração"])

    with tab_gerar:
        st.subheader("Configuração do Sábado")
        data_sel = st.date_input("Selecione a Data:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Sala 8 - Teoria")
            pt1 = st.selectbox("Prof. Teoria - T1:", PROFESSORAS_LISTA, index=0, key=f"pt1_{data_str}")
            pt2 = st.selectbox("Prof. Teoria - T2:", PROFESSORAS_LISTA, index=1, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Prof. Teoria - T3:", PROFESSORAS_LISTA, index=2, key=f"pt3_{data_str}")
        with c2:
            st.markdown("#### 🔊 Sala 9 - Solfejo")
            st1 = st.selectbox("Prof. Solfejo - T1:", PROFESSORAS_LISTA, index=3, key=f"st1_{data_str}")
            st2 = st.selectbox("Prof. Solfejo - T2:", PROFESSORAS_LISTA, index=4, key=f"st2_{data_str}")
            st3 = st.selectbox("Prof. Solfejo - T3:", PROFESSORAS_LISTA, index=5, key=f"st3_{data_str}")
        
        folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button("🚀 Gerar Rodízio Dinâmico", use_container_width=True):
            fixas = [pt1, pt2, pt3, st1, st2, st3]
            prat_disp = [p for p in PROFESSORAS_LISTA if p not in folgas and p not in fixas]
            random.shuffle(prat_disp)
            
            # LÓGICA DE CARROSSEL: A professora muda de sala (índice) a cada horário
            # As alunas ficam paradas em suas colunas virtuais
            grade_dia = []
            for i in range(7):
                grade_dia.append({
                    "Aluna (Referência)": TURMAS["Turma 3"][i],
                    "08h45 (H1)": f"Sala {i+1} - {prat_disp[i] if i < len(prat_disp) else 'Vago'}",
                    "09h35 (H2)": f"Sala {(i+1)%7 + 1} - {prat_disp[(i+1)%len(prat_disp)] if prat_disp else 'Vago'}",
                    "10h10 (H3)": f"Sala {(i+2)%7 + 1} - {prat_disp[(i+2)%len(prat_disp)] if prat_disp else 'Vago'}"
                })
            
            st.session_state.calendario_anual[data_str] = {
                "tabela": grade_dia,
                "config": {"teoria": {HORARIOS_LABELS[0]: pt1, HORARIOS_LABELS[1]: pt2, HORARIOS_LABELS[2]: pt3},
                           "solfejo": {HORARIOS_LABELS[0]: st2, HORARIOS_LABELS[1]: st3, HORARIOS_LABELS[2]: st1}}
            }
            st.success("Rodízio Gerado!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_admin:
        if st.button("🔥 LIMPAR BANCO DE DADOS"):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Portal da Instrutora")
    data_aula = st.date_input("Data:", value=datetime.now())
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário:", options=HORARIOS_LABELS)
        
        info = st.session_state.calendario_anual[d_str]
        atendendo, sala, mat = "---", "---", "---"

        # Busca dinâmica: Onde esta professora está alocada neste horário?
        for linha in info["tabela"]:
            if p_nome in linha.get(h_atual, ""):
                atendendo = linha["Aluna (Referência)"]
                sala = linha[h_atual].split(" - ")[0]
                mat = "Prática"

        # Verifica Teoria/Solfejo
        if p_nome == info["config"]["teoria"].get(h_atual): sala, atendendo, mat = "Sala 8", "Turma Correspondente", "Teoria"
        if p_nome == info["config"]["solfejo"].get(h_atual): sala, atendendo, mat = "Sala 9", "Turma Correspondente", "Solfejo"

        st.info(f"📍 **Local:** {sala} | 👤 **Atendendo:** {atendendo}")

        # --- FORMULÁRIOS COMPLETOS ---
        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO PRÁTICA (25 ITENS)")
            difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respiração", "Passagem", "Dedilhado", "Nota Apoio", "Dificuldade Técnica", "Sem dificuldades"]
            cols = st.columns(2)
            for i, d in enumerate(difs): (cols[0] if i < 13 else cols[1]).checkbox(d, key=f"p_{i}")
        elif mat == "Teoria":
            st.subheader("📋 FORMULÁRIO TEORIA")
            for t in ["MSA", "Pauta", "Exercícios", "Comportamento"]: st.checkbox(t)
        elif mat == "Solfejo":
            st.subheader("📋 FORMULÁRIO SOLFEJO")
            for s in ["Linguagem Rítmica", "Afinação", "Mão", "Metrônomo", "Postura"]: st.checkbox(s)

        st.text_area("Observações:")
        st.button("Salvar Aula")
