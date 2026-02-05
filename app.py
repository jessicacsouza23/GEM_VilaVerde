import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema Oficial", layout="wide")

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
perfil = st.sidebar.radio("Navegação de Perfil:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_corr, tab_admin = st.tabs([
        "🗓️ Planejar Sábados", "📍 Chamada Geral", "✅ Correção (Secretaria)", "⚠️ Administração"
    ])

    with tab_gerar:
        st.subheader("Configuração de Rodízio por Data")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
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
        
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button(f"🚀 Gerar e Salvar Escala de {data_str}", use_container_width=True):
            fixas = [pt1, pt2, pt3, st1, st2, st3]
            prat_disp = [p for p in PROFESSORAS_LISTA if p not in folgas and p not in fixas]
            random.shuffle(prat_disp)
            
            # LÓGICA DE ROTAÇÃO: Criação da Tabela com alunas mudando de sala
            grade_dia = []
            for i in range(7):
                instrutora = prat_disp[i] if i < len(prat_disp) else "Vago"
                # Rotação: H1(T3), H2(T1 deslocada), H3(T2 deslocada)
                grade_dia.append({
                    "Sala": f"Sala {i+1} (Prática)",
                    "Instrutora": instrutora,
                    "08h45 (H1)": TURMAS["Turma 3"][i],
                    "09h35 (H2)": TURMAS["Turma 1"][(i + 1) % 7],
                    "10h10 (H3)": TURMAS["Turma 2"][(i + 2) % 7]
                })
            
            # Adiciona Teoria e Solfejo
            grade_dia.append({"Sala": "Sala 8 (Teo)", "Instrutora": "Múltiplas", "08h45 (H1)": f"T1 ({pt1})", "09h35 (H2)": f"T2 ({pt2})", "10h10 (H3)": f"T3 ({pt3})"})
            grade_dia.append({"Sala": "Sala 9 (Sol)", "Instrutora": "Múltiplas", "08h45 (H1)": f"T2 ({st2})", "09h35 (H2)": f"T3 ({st3})", "10h10 (H3)": f"T1 ({st1})"})

            st.session_state.calendario_anual[data_str] = {
                "tabela": grade_dia,
                "config": {"teoria": {"Turma 1": pt1, "Turma 2": pt2, "Turma 3": pt3},
                           "solfejo": {"Turma 1": st1, "Turma 2": st2, "Turma 3": st3},
                           "pratica": prat_disp}
            }
            st.success(f"Escala de {data_str} salva!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_chamada:
        st.subheader("📍 Chamada Unificada")
        for aluna in TODAS_ALUNAS:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(aluna)
            c2.checkbox("P", key=f"p_{aluna}_{data_str}")
            c3.checkbox("J", key=f"j_{aluna}_{data_str}")
        st.button("💾 Salvar Chamada", key="save_chamada")

    with tab_corr:
        st.subheader("✅ CORREÇÃO (SECRETARIA)")
        sel_alu = st.selectbox("Aluna:", TODAS_ALUNAS)
        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("Materiais:", ["MSA Verde", "MSA Preto", "Pauta", "Apostila"])
            st.radio("Trouxe Apostila?", ["Sim", "Não"], horizontal=True)
        with c2:
            st.radio("Vídeos?", ["Sim", "Não"], horizontal=True)
            st.radio("Exercícios?", ["Sim", "Não"], horizontal=True)
        st.button("Salvar Registro de Correção")

    with tab_admin:
        st.subheader("⚠️ Administração")
        if st.button("🗑️ RESET TOTAL DO BANCO"):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Portal da Instrutora")
    data_aula = st.date_input("Data da Aula:", value=datetime.now(), key="prof_date")
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str not in st.session_state.calendario_anual:
        st.warning(f"Rodízio não planejado para {d_str}.")
    else:
        info_dia = st.session_state.calendario_anual[d_str]
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário Atual:", options=HORARIOS_LABELS)

        # Lógica para Teoria e Solfejo (Por Turma)
        rot_logic = {
            HORARIOS_LABELS[0]: {"teo": "Turma 1", "sol": "Turma 2"},
            HORARIOS_LABELS[1]: {"teo": "Turma 2", "sol": "Turma 3"},
            HORARIOS_LABELS[2]: {"teo": "Turma 3", "sol": "Turma 1"},
            HORARIOS_LABELS[3]: {"teo": "Geral", "sol": "Geral"}
        }

        sala, atendendo, mat = "Não alocada", "---", "---"
        
        if h_atual != HORARIOS_LABELS[3]:
            conf = info_dia["config"]
            # 1. Busca em Teoria/Solfejo
            if p_nome == conf["teoria"].get(rot_logic[h_atual]["teo"]):
                sala, atendendo, mat = "Sala 8 (Teoria)", rot_logic[h_atual]["teo"], "Teoria"
            elif p_nome == conf["solfejo"].get(rot_logic[h_atual]["sol"]):
                sala, atendendo, mat = "Sala 9 (Solfejo)", rot_logic[h_atual]["sol"], "Solfejo"
            
            # 2. Busca nas salas de Prática (CORREÇÃO DA ROTAÇÃO AQUI)
            elif p_nome in conf["pratica"]:
                idx_prof = conf["pratica"].index(p_nome)
                sala = f"Sala {idx_prof+1} (Prática)"
                mat = "Prática"
                # Acessa a linha correta da tabela salva e a coluna do horário atual
                atendendo = info_dia["tabela"][idx_prof][h_atual]

        st.info(f"📍 **Local:** {sala} | 👤 **Atendendo Agora:** {atendendo}")
        st.divider()

        if mat == "Prática":
            st.subheader("📋 AULA PRÁTICA (25 ITENS)")
            difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respiração", "Passagem", "Dedilhado", "Nota Apoio", "Sem dificuldades"]
            cols = st.columns(2)
            for i, d in enumerate(difs): (cols[0] if i < 13 else cols[1]).checkbox(d, key=f"pchk_{i}")
        elif mat == "Teoria":
            st.subheader(f"📋 FORMULÁRIO TEORIA - {atendendo}")
            for t in ["MSA", "Pauta", "Exercícios"]: st.checkbox(t, key=f"tchk_{t}")
        elif mat == "Solfejo":
            st.subheader(f"📋 FORMULÁRIO SOLFEJO - {atendendo}")
            for s in ["Rítmica", "Melódica", "Mão", "Pulsação"]: st.checkbox(s, key=f"schk_{s}")

        st.text_input("Próxima Lição:")
        st.button("Salvar Aula")
