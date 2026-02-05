import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Sistema 9 Salas", layout="wide")

# --- BANCO DE DADOS DE ALUNAS POR TURMA ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 (1ª Aula)", "09h35 (2ª Aula)", "10h10 (3ª Aula)", "10h45 (Aula Final)"]

# --- ESTADO GLOBAL ---
if "grade_publicada" not in st.session_state:
    st.session_state.grade_publicada = None

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão Integrada de Rodízio")
perfil = st.sidebar.radio("Selecione sua Visão:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_corr = st.tabs(["🗓️ Gerar Rodízio 9 Salas", "📍 Chamada", "✅ Correção de Atividades"])

    with tab_gerar:
        st.subheader("Configuração das Salas Coletivas")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Sala 8 - Teoria")
            pt1 = st.selectbox("Prof. Teoria - Turma 1:", PROFESSORAS_LISTA, index=0)
            pt2 = st.selectbox("Prof. Teoria - Turma 2:", PROFESSORAS_LISTA, index=1)
            pt3 = st.selectbox("Prof. Teoria - Turma 3:", PROFESSORAS_LISTA, index=2)
        with c2:
            st.markdown("#### 🔊 Sala 9 - Solfejo")
            st1 = st.selectbox("Prof. Solfejo - Turma 1:", PROFESSORAS_LISTA, index=3)
            st2 = st.selectbox("Prof. Solfejo - Turma 2:", PROFESSORAS_LISTA, index=4)
            st3 = st.selectbox("Prof. Solfejo - Turma 3:", PROFESSORAS_LISTA, index=5)
        
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA)

        if st.button("🚀 Gerar e Publicar Grade Oficial", use_container_width=True):
            fixas = [pt1, pt2, pt3, st1, st2, st3]
            prat_disp = [p for p in PROFESSORAS_LISTA if p not in folgas and p not in fixas]
            random.shuffle(prat_disp)
            
            tabela_mestre = []
            # Gerando dados para a visualização da grade
            for i in range(7):
                prof_p = prat_disp[i] if i < len(prat_disp) else "Vago"
                tabela_mestre.append({
                    "Sala": f"Sala {i+1} (Prática)",
                    "Instrutora": prof_p,
                    "08h45 (H1)": TURMAS["Turma 3"][i],
                    "09h35 (H2)": TURMAS["Turma 1"][i],
                    "10h10 (H3)": TURMAS["Turma 2"][i]
                })
            
            # Adicionando Teoria e Solfejo na tabela visual
            tabela_mestre.append({"Sala": "Sala 8 (Teoria)", "Instrutora": "Por Turma", "08h45 (H1)": f"T1 ({pt1})", "09h35 (H2)": f"T2 ({pt2})", "10h10 (H3)": f"T3 ({pt3})"})
            tabela_mestre.append({"Sala": "Sala 9 (Solfejo)", "Instrutora": "Por Turma", "08h45 (H1)": f"T2 ({st2})", "09h35 (H2)": f"T3 ({st3})", "10h10 (H3)": f"T1 ({st1})"})

            st.session_state.grade_publicada = {
                "tabela": tabela_mestre,
                "config": {
                    "teoria": {"Turma 1": pt1, "Turma 2": pt2, "Turma 3": pt3},
                    "solfejo": {"Turma 1": st1, "Turma 2": st2, "Turma 3": st3},
                    "pratica": prat_disp
                }
            }
            st.success("Grade de 9 salas gerada e visível abaixo!")

        if st.session_state.grade_publicada:
            st.divider()
            st.subheader("📋 Grade de Aulas Gerada")
            st.table(pd.DataFrame(st.session_state.grade_publicada["tabela"]))

    with tab_chamada:
        st.subheader("📍 Controle de Presença")
        t_sel = st.selectbox("Selecione a Turma:", ["Turma 1", "Turma 2", "Turma 3"])
        for aluna in TURMAS[t_sel]:
            st.checkbox(aluna, key=f"cham_{aluna}")

    with tab_corr:
        st.subheader("✅ Formulário de Correção de Atividades")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Selecionar Aluna:", [a for l in TURMAS.values() for a in l], key="sel_alu")
            st.multiselect("Materiais Corrigidos:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas"])
            st.radio("Trouxe a apostila?", ["Sim", "Não", "Esqueceu"], horizontal=True)
        with c2:
            st.radio("Assistiu os vídeos da semana?", ["Sim", "Não", "Em parte"], horizontal=True)
            st.radio("Fez exercícios de pauta?", ["Sim", "Não", "Incompleto"], horizontal=True)
            st.text_area("Lições de Casa OK / Pendências:")
        st.button("Salvar Correção")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Portal da Instrutora")
    if not st.session_state.grade_publicada:
        st.warning("⚠️ O rodízio ainda não foi gerado pela Secretaria.")
    else:
        conf = st.session_state.grade_publicada["config"]
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Selecione o Horário Atual:", options=HORARIOS)

        # Lógica de Rotação de Turmas
        rot = {
            HORARIOS[0]: {"teo": "Turma 1", "sol": "Turma 2", "prat": "Turma 3"},
            HORARIOS[1]: {"teo": "Turma 2", "sol": "Turma 3", "prat": "Turma 1"},
            HORARIOS[2]: {"teo": "Turma 3", "sol": "Turma 1", "prat": "Turma 2"},
            HORARIOS[3]: {"teo": "Geral", "sol": "Geral", "prat": "Encerrado"}
        }

        sala, atendendo, mat = "Não alocada", "---", "---"

        if h_atual != HORARIOS[3]:
