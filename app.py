import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema 2026", layout="wide", page_icon="🎼")

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão de Aulas e Rodízio")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_correcao, tab_admin = st.tabs([
        "🗓️ Planejar Sábado", "📍 Chamada", "✅ Correção de Atividades", "⚠️ Administração"
    ])

    with tab_gerar:
        st.subheader("Planejamento do Rodízio")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        offset_semana = (data_sel.day // 7) % 7

        st.markdown("#### 👩‍🏫 Escala de Instrutoras (H2 até H4)")
        c1, c2 = st.columns(2)
        with c1:
            st.info("📚 Sala 8 - Teoria")
            pt2 = st.selectbox("Instrutora Teoria H2 (T1):", PROFESSORAS_LISTA, index=0, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Instrutora Teoria H3 (T2):", PROFESSORAS_LISTA, index=1, key=f"pt3_{data_str}")
            pt4 = st.selectbox("Instrutora Teoria H4 (T3):", PROFESSORAS_LISTA, index=2, key=f"pt4_{data_str}")
        with c2:
            st.info("🔊 Sala 9 - Solfejo/MSA")
            st2 = st.selectbox("Instrutora Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3, key=f"st2_{data_str}")
            st3 = st.selectbox("Instrutora Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4, key=f"st3_{data_str}")
            st4 = st.selectbox("Instrutora Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5, key=f"st4_{data_str}")
        
        folgas = st.multiselect("Instrutoras de FOLGA hoje:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button("🚀 Gerar e Mostrar Grade na Tela", use_container_width=True):
            escala_final = []
            fluxo = {
                HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
            }

            for t_nome, alunas in TURMAS.items():
                for i, aluna in enumerate(alunas):
                    agenda = {"Aluna": aluna, "Turma": t_nome}
                    agenda[HORARIOS_LABELS[0]] = "⛪ IGREJA | Solfejo Coletivo"
                    for h_idx in [1, 2, 3]:
                        h_label = HORARIOS_LABELS[h_idx]
                        config = fluxo[h_label]
                        if config["Teo"] == t_nome: agenda[h_label] = f"📚 SALA 8 | Teoria ({config['ITeo']})"
                        elif config["Sol"] == t_nome: agenda[h_label] = f"🔊 SALA 9 | Solfejo ({config['ISol']})"
                        else:
                            profs_ocup = [config["ITeo"], config["ISol"]] + folgas
                            profs_p = [p for p in PROFESSORAS_LISTA if p not in profs_ocup]
                            sala_p = (i + offset_semana + h_idx) % 7 + 1
                            instr_p = profs_p[i % len(profs_p)] if profs_p else "Vago"
                            agenda[h_label] = f"🎹 SALA {sala_p} | Prática ({instr_p})"
                    escala_final.append(agenda)
            st.session_state.calendario_anual[data_str] = {"tabela": escala_final}
            st.success(f"Grade gerada para {data_str}!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.subheader(f"📊 Visualização do Rodízio - {data_str}")
            df_display = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.dataframe(df_display, use_container_width=True)

    with tab_chamada:
        st.subheader("📍 Chamada de Alunas")
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"👤 {aluna}")
            col_b.checkbox("Presente", key=f"pres_chamada_{aluna}")

    with tab_correcao:
        st.subheader("✅ Formulário de Correção de Atividades")
        alu_c = st.selectbox("Selecione a aluna para correção:", sorted([a for l in TURMAS.values() for a in l]), key="sel_alu_corr")
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("📖 Caderno de Pauta", key="check_pauta")
            st.checkbox("📙 Apostila de Teoria", key="check_apostila")
        with col2:
            st.checkbox("🎵 MSA (Exercícios)", key="check_msa")
            st.checkbox("🎥 Assistiu Vídeos", key="check_video")
        st.text_area("Observações da Correção:", key="obs_correcao")
        st.button("Salvar Correção", key="btn_save_corr")

    with tab_admin:
        if st.button("🔥 LIMPAR HISTÓRICO"):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Diário de Classe")
    data_aula = st.date_input("Data:", value=datetime.now(), key="date_prof")
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        instrutora_sel = st.selectbox("Quem é você?", PROFESSORAS_LISTA, key="sel_prof_name")
        horario_sel = st.select_slider("Horário:", options=HORARIOS_LABELS, key="slider_hora")
        info = st.session_state.calendario_anual[d_str]
        
        atend, local, mat = "---", "---", "---"

        if horario_sel == HORARIOS_LABELS[0]:
            local, atend, mat = "⛪ Igreja", "Todas as Alunas", "Solfejo Melódico"
        else:
            for linha in info["tabela"]:
                if f"({instrutora_sel})" in linha.get(horario_sel, ""):
                    atend = linha["Aluna"]
                    local = linha[horario_sel].split(" | ")[0]
                    mat = "Teoria" if "SALA 8" in local else "Solfejo" if "SALA 9" in local else "Prática"

        if "SALA 8" in local: st.warning(f"📚 {local} | 👤 Aluna: {atend} | 📖 Matéria: {mat}")
        elif "SALA 9" in local: st.success(f"🔊 {local} | 👤 Aluna: {atend} | 📖 Matéria: {mat}")
        elif "Igreja" in local: st.info(f"⛪ {local} | 👤 Aluna: {atend} | 📖 Matéria: {mat}")
        else: st.error(f"🎹 {local} | 👤 Aluna: {atend} | 📖 Matéria: {mat}")
        
        st.divider()

        # --- FORMULÁRIOS ESPECÍFICOS ---
        if mat == "Prática":
            st.subheader("📋 Formulário Prática (25 Itens Técnicos)")
            itens_pratica = [
                "Não estudou", "Estudo insatisfatório", "Não assistiu vídeos", "Dificuldade rítmica",
                "Nomes figuras rítmicas", "Adentrando às teclas", "Postura (Costas/Braços)", "Punho (Alto/Baixo)",
                "Não senta no centro", "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo", "Estuda sem metrônomo",
                "Clave de sol", "Clave de fá", "Atividades apostila", "Articulação ligada/semiligada",
                "Respirações", "Respirações passagem", "Recurso de dedilhado", "Nota de apoio", "Sem dificuldades"
            ]
            c1, c2 = st.columns(2)
            for i, item in enumerate(itens_pratica):
                (c1 if i < 13 else c2).checkbox(item, key=f"check_prat_{i}")
        
        elif mat == "Solfejo" or mat == "Solfejo Melódico":
            st.subheader("📋 Formulário Solfejo/MSA")
            for s in ["Afinação", "Linguagem Rítmica", "Pulsação", "Módulo MSA"]:
                st.checkbox(s, key=f"check_sol_{s}")
            
        elif mat == "Teoria":
            st.subheader("📋 Formulário Teoria")
            for t in ["Módulo MSA", "Exercícios Pauta", "Aplicação de Teste"]:
                st.checkbox(t, key=f"check_teo_{t}")

        st.text_input("🏠 Lição para Casa:", key="home_work")
        st.text_area("📝 Observações da Aula:", key="obs_aula")
        st.button("💾 Salvar Registro", key="btn_final_save")
    else:
        st.error("Escala não gerada para hoje.")
