import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema de Rodízio", layout="wide")

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
st.title("🎼 GEM Vila Verde - Gestão de Rodízio")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_corr, tab_admin = st.tabs([
        "🗓️ Planejar Sábados", "📍 Chamada Geral", "✅ Correção (Secretaria)", "⚠️ Administração"
    ])

    with tab_gerar:
        st.subheader("Configuração de Rodízio Semanal")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # Deslocamento baseado no dia para garantir que a aluna mude de sala toda semana
        # Ex: Sábado dia 07 (offset 0), Sábado dia 14 (offset 1)
        offset_sala = (data_sel.day // 7) % 7

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Sala 8 - Teoria")
            pt1 = st.selectbox("Prof. T1 (H1):", PROFESSORAS_LISTA, index=0, key=f"pt1_{data_str}")
            pt2 = st.selectbox("Prof. T2 (H2):", PROFESSORAS_LISTA, index=1, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Prof. T3 (H3):", PROFESSORAS_LISTA, index=2, key=f"pt3_{data_str}")
        with c2:
            st.markdown("#### 🔊 Sala 9 - Solfejo")
            st1 = st.selectbox("Prof. S1 (H1):", PROFESSORAS_LISTA, index=3, key=f"st1_{data_str}")
            st2 = st.selectbox("Prof. S2 (H2):", PROFESSORAS_LISTA, index=4, key=f"st2_{data_str}")
            st3 = st.selectbox("Prof. S3 (H3):", PROFESSORAS_LISTA, index=5, key=f"st3_{data_str}")
        
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button(f"🚀 Gerar Escala com Rotação de Salas para {data_str}", use_container_width=True):
            # Quem está ocupada com Teoria/Solfejo em cada horário?
            ocupadas_h1 = [pt1, st1] + folgas
            ocupadas_h2 = [pt2, st2] + folgas
            ocupadas_h3 = [pt3, st3] + folgas

            # Lista de professoras disponíveis para PRÁTICA em cada horário
            disp_h1 = [p for p in PROFESSORAS_LISTA if p not in ocupadas_h1]
            disp_h2 = [p for p in PROFESSORAS_LISTA if p not in ocupadas_h2]
            disp_h3 = [p for p in PROFESSORAS_LISTA if p not in ocupadas_h3]

            grade_dia = []
            for i in range(7):
                # Cálculo da Sala: Muda a cada sábado (offset_sala) e a cada horário (+h_idx)
                sala_h1 = f"Sala {(i + offset_sala) % 7 + 1}"
                sala_h2 = f"Sala {(i + offset_sala + 1) % 7 + 1}"
                sala_h3 = f"Sala {(i + offset_sala + 2) % 7 + 1}"

                # Atribuição de Professora de Prática (Se houver disponível)
                prof_h1 = disp_h1[i] if i < len(disp_h1) else "Vago"
                prof_h2 = disp_h2[i] if i < len(disp_h2) else "Vago"
                prof_h3 = disp_h3[i] if i < len(disp_h3) else "Vago"

                grade_dia.append({
                    "Ref. Aluna": TURMAS["Turma 3"][i],
                    "08h45 (H1)": f"{sala_h1} | Prof. {prof_h1}",
                    "09h35 (H2)": f"{sala_h2} | Prof. {prof_h2}",
                    "10h10 (H3)": f"{sala_h3} | Prof. {prof_h3}"
                })
            
            st.session_state.calendario_anual[data_str] = {
                "tabela": grade_dia,
                "config": {
                    "teoria": {HORARIOS_LABELS[0]: pt1, HORARIOS_LABELS[1]: pt2, HORARIOS_LABELS[2]: pt3},
                    "solfejo": {HORARIOS_LABELS[0]: st1, HORARIOS_LABELS[1]: st2, HORARIOS_LABELS[2]: st3}
                }
            }
            st.success("Rodízio Universal Gerado!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.write("**Grade de Prática (Alunas Rotacionando entre Salas e Professoras)**")
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_admin:
        if st.button("🗑️ RESETAR SISTEMA"):
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
        info = st.session_state.calendario_anual[d_str]
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário:", options=HORARIOS_LABELS)
        
        atendendo, sala, mat = "---", "---", "---"

        # 1. Verifica se está na Teoria ou Solfejo
        if p_nome == info["config"]["teoria"].get(h_atual):
            sala, atendendo, mat = "Sala 8", "Turma Correspondente", "Teoria"
        elif p_nome == info["config"]["solfejo"].get(h_atual):
            sala, atendendo, mat = "Sala 9", "Turma Correspondente", "Solfejo"
        else:
            # 2. Se não, busca em qual Sala de Prática ela foi alocada
            for linha in info["tabela"]:
                if f"Prof. {p_nome}" in linha.get(h_atual, ""):
                    atendendo = linha["Ref. Aluna"]
                    sala = linha[h_atual].split(" | ")[0]
                    mat = "Prática"

        st.info(f"📍 **Local:** {sala} | 👤 **Atendimento:** {atendendo} | 📖 **Matéria:** {mat}")
        st.divider()

        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO DE AULA PRÁTICA (25 ITENS)")
            difs = ["Não estudou nada", "Estudo insatisfatório", "Não assistiu os vídeos",
                    "Dificuldade rítmica", "Nomes figuras rítmicas", "Adentrando às teclas",
                    "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos arredondados",
                    "Pedal", "Pé esquerdo", "Metrônomo", "Clave de sol", "Clave de fá", 
                    "Apostila", "Articulação", "Respiração", "Passagem de dedos", 
                    "Dedilhado", "Nota de apoio", "Técnica", "Sem dificuldades"]
            cols = st.columns(2)
            for i, d in enumerate(difs): (cols[0] if i < 13 else cols[1]).checkbox(d, key=f"pra_{i}")
        
        elif mat == "Teoria":
            st.subheader("📋 FORMULÁRIO TEORIA")
            st.checkbox("Módulo MSA", key="t1")
            st.checkbox("Pauta/Exercícios", key="t2")
            
        elif mat == "Solfejo":
            st.subheader("📋 FORMULÁRIO SOLFEJO")
            st.checkbox("Linguagem Rítmica", key="s1")
            st.checkbox("Afinação Melódica", key="s2")

        st.text_input("🏠 Lição para Casa:")
        st.button("Salvar Registro")
