import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Rotação Universal", layout="wide")

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
st.title("🎼 GEM Vila Verde - Gestão de Ciclos Dinâmicos")
perfil = st.sidebar.radio("Navegação de Perfil:", ["Secretaria", "Professora"])

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
        # Usamos o dia para criar uma semente de rotação (semana 1 é diferente da semana 2)
        semana_offset = data_sel.day % 7 

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Teoria (Sala 8)")
            pt1 = st.selectbox("Prof. T1:", PROFESSORAS_LISTA, index=0, key=f"pt1_{data_str}")
            pt2 = st.selectbox("Prof. T2:", PROFESSORAS_LISTA, index=1, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Prof. T3:", PROFESSORAS_LISTA, index=2, key=f"pt3_{data_str}")
        with c2:
            st.markdown("#### 🔊 Solfejo (Sala 9)")
            st1 = st.selectbox("Prof. S1:", PROFESSORAS_LISTA, index=3, key=f"st1_{data_str}")
            st2 = st.selectbox("Prof. S2:", PROFESSORAS_LISTA, index=4, key=f"st2_{data_str}")
            st3 = st.selectbox("Prof. S3:", PROFESSORAS_LISTA, index=5, key=f"st3_{data_str}")
        
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button(f"🚀 Gerar Grade com Rotação de Matéria e Sala", use_container_width=True):
            fixas_dia = [pt1, pt2, pt3, st1, st2, st3]
            prat_disp = [p for p in PROFESSORAS_LISTA if p not in folgas and p not in fixas_dia]
            # Shuffle baseado na data para garantir que a ordem das professoras de prática mude toda semana
            random.seed(data_sel.toordinal())
            random.shuffle(prat_disp)
            
            # ROTAÇÃO DE MATÉRIA POR TURMA (Teoria -> Solfejo -> Prática)
            # A cada semana, a Turma 1 começa em uma matéria diferente
            ordem_materias = {
                "Turma 1": [HORARIOS_LABELS[semana_offset % 3], HORARIOS_LABELS[(semana_offset + 1) % 3], HORARIOS_LABELS[(semana_offset + 2) % 3]],
                "Turma 2": [HORARIOS_LABELS[(semana_offset + 1) % 3], HORARIOS_LABELS[(semana_offset + 2) % 3], HORARIOS_LABELS[semana_offset % 3]],
                "Turma 3": [HORARIOS_LABELS[(semana_offset + 2) % 3], HORARIOS_LABELS[semana_offset % 3], HORARIOS_LABELS[(semana_offset + 1) % 3]]
            }

            grade_dia = []
            for i in range(7):
                instrutora_base = prat_disp[i] if i < len(prat_disp) else "Vago"
                
                # Aluna fixa a linha, mas a SALA e a PROFESSORA mudam de acordo com o horário (i + offset)
                grade_dia.append({
                    "Aluna": TURMAS["Turma 3"][i],
                    HORARIOS_LABELS[0]: f"Sala {(i + semana_offset)%7 + 1} | Prof. {prat_disp[(i + semana_offset)%len(prat_disp)] if prat_disp else 'Vago'}",
                    HORARIOS_LABELS[1]: f"Sala {(i + semana_offset + 1)%7 + 1} | Prof. {prat_disp[(i + semana_offset + 1)%len(prat_disp)] if prat_disp else 'Vago'}",
                    HORARIOS_LABELS[2]: f"Sala {(i + semana_offset + 2)%7 + 1} | Prof. {prat_disp[(i + semana_offset + 2)%len(prat_disp)] if prat_disp else 'Vago'}"
                })

            st.session_state.calendario_anual[data_str] = {
                "tabela": grade_dia,
                "config": {
                    "teoria": {ordem_materias["Turma 1"][0]: pt1, ordem_materias["Turma 2"][0]: pt2, ordem_materias["Turma 3"][0]: pt3},
                    "solfejo": {ordem_materias["Turma 1"][1]: st1, ordem_materias["Turma 2"][1]: st2, ordem_materias["Turma 3"][1]: st3},
                    "ordem": ordem_materias
                }
            }
            st.success("Nova Grade Gerada!")

        if data_str in st.session_state.calendario_anual:
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_admin:
        if st.button("🔥 LIMPAR BANCO"):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Diário da Instrutora")
    data_aula = st.date_input("Data:", value=datetime.now())
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        info = st.session_state.calendario_anual[d_str]
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário:", options=HORARIOS_LABELS)
        
        atendendo, sala, mat = "---", "---", "---"

        # 1. Busca na Teoria/Solfejo
        if p_nome == info["config"]["teoria"].get(h_atual):
            sala, atendendo, mat = "Sala 8", "Turma Teoria", "Teoria"
        elif p_nome == info["config"]["solfejo"].get(h_atual):
            sala, atendendo, mat = "Sala 9", "Turma Solfejo", "Solfejo"
        else:
            # 2. Busca na Prática (Onde a professora está agora?)
            for linha in info["tabela"]:
                if f"Prof. {p_nome}" in linha.get(h_atual, ""):
                    atendendo = linha["Aluna"]
                    sala = linha[h_atual].split(" | ")[0]
                    mat = "Prática"

        st.info(f"📍 **{sala}** | 👤 **Atendendo:** {atendendo} | 📖 **Matéria:** {mat}")
        st.divider()

        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO DE PRÁTICA (25 ITENS)")
            difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respiração", "Passagem", "Dedilhado", "Nota Apoio", "Dificuldade Técnica", "Sem dificuldades"]
            c1, c2 = st.columns(2)
            for i, d in enumerate(difs): (c1 if i < 13 else c2).checkbox(d, key=f"p_{i}")
        elif mat == "Teoria":
            st.subheader("📋 FORMULÁRIO DE TEORIA")
            for t in ["MSA", "Exercícios Pauta", "Aplicação de Teste"]: st.checkbox(t, key=f"t_{t}")
        elif mat == "Solfejo":
            st.subheader("📋 FORMULÁRIO DE SOLFEJO")
            for s in ["Linguagem Rítmica", "Pulsação", "Afinação", "Marcação Manual"]: st.checkbox(s, key=f"s_{s}")

        st.button("💾 Salvar Atendimento")
