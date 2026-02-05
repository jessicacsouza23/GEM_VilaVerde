import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão Integrada", layout="wide")

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

TODAS_ALUNAS = sorted([aluna for lista in TURMAS.values() for aluna in lista])
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 (H1)", "09h35 (H2)", "10h10 (H3)", "10h45 (Aula Final)"]

# Inicialização do Banco de Dados Persistente na Sessão
if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Sistema de Gestão de Rodízio")
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
        data_sel = st.date_input("Escolha o Sábado para configurar:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        st.info(f"Configurando escala para o dia: **{data_str}**")

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
            
            # GERAÇÃO DA GRADE COM ROTAÇÃO DE ALUNAS ENTRE AS SALAS
            grade_dia = []
            for i in range(7):
                instrutora = prat_disp[i] if i < len(prat_disp) else "Vago"
                # Lógica de Rotação: A aluna i "pula" uma sala a cada horário
                grade_dia.append({
                    "Sala": f"Sala {i+1} (Prática)",
                    "Instrutora": instrutora,
                    "08h45 (H1)": TURMAS["Turma 3"][i],
                    "09h35 (H2)": TURMAS["Turma 1"][(i + 1) % 7],
                    "10h10 (H3)": TURMAS["Turma 2"][(i + 2) % 7]
                })
            
            # Adiciona Teoria e Solfejo na Grade Visual
            grade_dia.append({"Sala": "Sala 8 (Teo)", "Instrutora": "Por Turma", "08h45 (H1)": f"T1 ({pt1})", "09h35 (H2)": f"T2 ({pt2})", "10h10 (H3)": f"T3 ({pt3})"})
            grade_dia.append({"Sala": "Sala 9 (Sol)", "Instrutora": "Por Turma", "08h45 (H1)": f"T2 ({st2})", "09h35 (H2)": f"T3 ({st3})", "10h10 (H3)": f"T1 ({st1})"})

            st.session_state.calendario_anual[data_str] = {
                "tabela": grade_dia,
                "config": {"teoria": {"Turma 1": pt1, "Turma 2": pt2, "Turma 3": pt3},
                           "solfejo": {"Turma 1": st1, "Turma 2": st2, "Turma 3": st3},
                           "pratica": prat_disp}
            }
            st.success(f"Configuração de {data_str} salva com sucesso!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.subheader(f"📋 Grade de Aulas: {data_str}")
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_chamada:
        st.subheader("📍 Chamada Unificada")
        for aluna in TODAS_ALUNAS:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(aluna)
            c2.checkbox("P", key=f"p_{aluna}_{data_str}")
            c3.checkbox("J", key=f"j_{aluna}_{data_str}")
        st.button("💾 Salvar Chamada do Dia")

    with tab_corr:
        st.subheader("✅ FORMULÁRIO DE CORREÇÃO (SECRETARIA)")
        sel_alu = st.selectbox("Selecionar Aluna para Vistoria:", TODAS_ALUNAS)
        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("Materiais Conferidos:", ["MSA (Verde)", "MSA (Preto)", "Caderno Pauta", "Apostila", "Folhas Avulsas"])
            st.radio("Apostila em mãos?", ["Sim", "Não", "Esqueceu"], horizontal=True)
        with c2:
            st.radio("Vídeos da Semana?", ["Sim", "Não", "Incompleto"], horizontal=True)
            st.radio("Exercícios de Pauta?", ["Sim", "Não", "Incompleto"], horizontal=True)
        st.text_area("Notas da Secretaria (Pendências/Aprovações):")
        st.button("Salvar Registro de Correção")

    with tab_admin:
        st.subheader("⚠️ Administração do Sistema")
        if st.button("🗑️ LIMPAR TODOS OS DADOS (RESET TOTAL)", use_container_width=True):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Área da Instrutora")
    data_aula = st.date_input("Data da Aula:", value=datetime.now())
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str not in st.session_state.calendario_anual:
        st.warning(f"Nenhum rodízio planejado para {d_str}. Peça para a Secretaria gerar a escala.")
    else:
        info_dia = st.session_state.calendario_anual[d_str]
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Selecione o Horário Atual:", options=HORARIOS)

        # Lógica de Horários por Matéria
        rot_logic = {
            HORARIOS[0]: {"teo": "Turma 1", "sol": "Turma 2", "prat": "Turma 3"},
            HORARIOS[1]: {"teo": "Turma 2", "sol": "Turma 3", "prat": "Turma 1"},
            HORARIOS[2]: {"teo": "Turma 3", "sol": "Turma 1", "prat": "Turma 2"},
            HORARIOS[3]: {"teo": "Geral", "sol": "Geral", "prat": "Fim"}
        }

        sala, atendendo, mat = "Não alocada", "---", "---"
        
        if h_atual != HORARIOS[3]:
            conf = info_dia["config"]
            # Identifica se a professora está em Teoria, Solfejo ou Prática
            if p_nome == conf["teoria"].get(rot_logic[h_atual]["teo"]):
                sala, atendendo, mat = "Sala 8 (Teoria)", rot_logic[h_atual]["teo"], "Teoria"
            elif p_nome == conf["solfejo"].get(rot_logic[h_atual]["sol"]):
                sala, atendendo, mat = "Sala 9 (Solfejo)", rot_logic[h_atual]["sol"], "Solfejo"
            elif p_nome in conf["pratica"]:
                idx = conf["pratica"].index(p_nome)
                sala, mat = f"Sala {idx+1} (Prática)", "Prática"
                # Puxa a aluna rotacionada da tabela salva no banco
                atendendo = info_dia["tabela"][idx][h_atual]

        st.info(f"📍 **Local:** {sala} | 👤 **Atendendo Agora:** {atendendo}")
        st.divider()

        # --- FORMULÁRIO 1: AULA PRÁTICA (25 ITENS) ---
        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO DE AULA PRÁTICA")
            st.selectbox("Lição/Página Atual:", [str(i) for i in range(1,41)] + ["Apostila"])
            difs = ["Não estudou nada", "Estudo insatisfatório", "Não assistiu os vídeos",
                    "Dificuldade rítmica", "Nomes figuras rítmicas", "Adentrando às teclas",
                    "Postura (costas/ombros/braços)", "Punho alto/baixo", "Não senta no centro",
                    "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                    "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo",
                    "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Atividades apostila",
                    "Articulação ligada/semiligada", "Respirações", "Respirações passagem",
                    "Recurso de dedilhado", "Nota de apoio", "Não apresentou dificuldades"]
            cols = st.columns(2)
            for i, d in enumerate(difs): (cols[0] if i < 13 else cols[1]).checkbox(d, key=f"pra_{i}")

        # --- FORMULÁRIO 2: AULA TEÓRICA ---
        elif mat == "Teoria":
            st.subheader(f"📋 FORMULÁRIO DE AULA TEÓRICA - {atendendo}")
            c1, c2 = st.columns(2)
            with c1:
                st.checkbox("Módulo MSA", key="t1")
                st.checkbox("Exercícios de Pauta", key="t2")
                st.checkbox("Aplicação de Teste", key="t3")
            with c2:
                st.checkbox("Leitura de Notas", key="t4")
                st.checkbox("Intervalos/Armaduras", key="t5")
                st.checkbox("Comportamento", key="t6")

        # --- FORMULÁRIO 3: AULA DE SOLFEJO (EXPANDIDO) ---
        elif mat == "Solfejo":
            st.subheader(f"📋 FORMULÁRIO DE AULA DE SOLFEJO - {atendendo}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Rítmica**")
                st.checkbox("Linguagem Rítmica", key="s1")
                st.checkbox("Pulsação Constante", key="s2")
                st.checkbox("Respeito Metrônomo", key="s3")
            with col2:
                st.markdown("**Melódica**")
                st.checkbox
