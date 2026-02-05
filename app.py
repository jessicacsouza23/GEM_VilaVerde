import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema Completo", layout="wide")

# --- BANCO DE DADOS MESTRE ---
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
st.title("🎼 GEM Vila Verde - Rodízio Universal (Todas as Salas)")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_admin = st.tabs(["🗓️ Planejar Sábados", "📍 Chamada Geral", "⚠️ Administração"])

    with tab_gerar:
        st.subheader("Configuração de Rodízio Semanal")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # Define o deslocamento para que nada se repita na semana seguinte
        offset_semana = (data_sel.day // 7) % 9  # Rodízio entre as 9 salas (1-7 Prática, 8 Teo, 9 Sol)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Responsáveis Teoria")
            pt1 = st.selectbox("Prof. Teoria H1:", PROFESSORAS_LISTA, index=0, key=f"pt1_{data_str}")
            pt2 = st.selectbox("Prof. Teoria H2:", PROFESSORAS_LISTA, index=1, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Prof. Teoria H3:", PROFESSORAS_LISTA, index=2, key=f"pt3_{data_str}")
        with c2:
            st.markdown("#### 🔊 Responsáveis Solfejo")
            st1 = st.selectbox("Prof. Solfejo H1:", PROFESSORAS_LISTA, index=3, key=f"st1_{data_str}")
            st2 = st.selectbox("Prof. Solfejo H2:", PROFESSORAS_LISTA, index=4, key=f"st2_{data_str}")
            st3 = st.selectbox("Prof. Solfejo H3:", PROFESSORAS_LISTA, index=5, key=f"st3_{data_str}")
        
        folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button("🚀 Gerar Grade com Salas de Teoria e Solfejo Rotativas", use_container_width=True):
            # Mapeamento de quem ocupa as salas coletivas por horário
            coletivas = {
                HORARIOS_LABELS[0]: {"Teoria": pt1, "Solfejo": st1},
                HORARIOS_LABELS[1]: {"Teoria": pt2, "Solfejo": st2},
                HORARIOS_LABELS[2]: {"Teoria": pt3, "Solfejo": st3}
            }
            
            # Professoras disponíveis para Prática (quem não está nas coletivas nem de folga)
            def get_prat(h):
                ocup = [pt1, pt2, pt3, st1, st2, st3] if h == "all" else [coletivas[h]["Teoria"], coletivas[h]["Solfejo"]]
                return [p for p in PROFESSORAS_LISTA if p not in ocup and p not in folgas]

            grade_dia = []
            # Lista de todas as alunas (simplificada para o exemplo do rodízio)
            lista_rodizio = TURMAS["Turma 3"] # Você pode ajustar para mesclar as turmas

            for i, aluna in enumerate(lista_rodizio):
                slots = {}
                for h_idx, h_label in enumerate(HORARIOS_LABELS[:3]):
                    # A sala rotaciona entre 1 e 9
                    sala_num = (i + offset_semana + h_idx) % 9 + 1
                    
                    if sala_num == 8:
                        slots[h_label] = f"Sala 8 (Teoria) | Prof. {coletivas[h_label]['Teoria']}"
                    elif sala_num == 9:
                        slots[h_label] = f"Sala 9 (Solfejo) | Prof. {coletivas[h_label]['Solfejo']}"
                    else:
                        profs_p = get_prat(h_label)
                        prof_p = profs_p[i % len(profs_p)] if profs_p else "Vago"
                        slots[h_label] = f"Sala {sala_num} (Prática) | Prof. {prof_p}"
                
                grade_dia.append({"Aluna": aluna, **slots})

            st.session_state.calendario_anual[data_str] = {
                "tabela": grade_dia,
                "config": {"teoria": {HORARIOS_LABELS[0]: pt1, HORARIOS_LABELS[1]: pt2, HORARIOS_LABELS[2]: pt3},
                           "solfejo": {HORARIOS_LABELS[0]: st1, HORARIOS_LABELS[1]: st2, HORARIOS_LABELS[2]: st3}}
            }
            st.success("Rodízio Gerado!")

        if data_str in st.session_state.calendario_anual:
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_admin:
        if st.button("🗑️ RESET TOTAL"):
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

        # Rastreamento Dinâmico
        for linha in info["tabela"]:
            if f"Prof. {p_nome}" in linha.get(h_atual, ""):
                atendendo = linha["Aluna"]
                sala_full = linha[h_atual].split(" | ")[0]
                sala = sala_full
                mat = "Teoria" if "Sala 8" in sala_full else "Solfejo" if "Sala 9" in sala_full else "Prática"

        st.info(f"📍 **Local:** {sala} | 👤 **Atendendo:** {atendendo} | 📖 **Matéria:** {mat}")
        
        # --- FORMULÁRIOS COMPLETOS ---
        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO PRÁTICA (25 ITENS)")
            difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respirações", "Passagem", "Dedilhado", "Nota Apoio", "Técnica", "Sem dificuldades"]
            cols = st.columns(2)
            for i, d in enumerate(difs): (cols[0] if i < 13 else cols[1]).checkbox(d, key=f"pra_{i}")
        elif mat == "Teoria":
            st.subheader("📋 FORMULÁRIO TEORIA (SALA 8)")
            for t in ["MSA", "Exercícios", "Pauta", "Teoria Aplicada"]: st.checkbox(t)
        elif mat == "Solfejo":
            st.subheader("📋 FORMULÁRIO SOLFEJO (SALA 9)")
            for s in ["Linguagem Rítmica", "Afinação", "Compasso", "Metrônomo"]: st.checkbox(s)

        st.text_input("🏠 Lição de Casa:")
        st.button("Salvar Aula")
