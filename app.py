import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Carrossel Total", layout="wide")

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS_LABELS = ["08h45 (H1)", "09h35 (H2)", "10h10 (H3)"]

if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Carrossel de Disciplinas")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_admin = st.tabs(["🗓️ Planejar Sábado", "⚠️ Administração"])

    with tab_gerar:
        st.subheader("Configuração do Carrossel")
        data_sel = st.date_input("Data do Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # O offset garante que a ordem das matérias mude a cada sábado (Ex: Teoria começa com T1, semana que vem com T2)
        offset_semana = (data_sel.day // 7) % 3

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Responsáveis Teoria (Sala 8)")
            pt1 = st.selectbox("Prof. Teoria H1:", PROFESSORAS_LISTA, index=0, key=f"pt1_{data_str}")
            pt2 = st.selectbox("Prof. Teoria H2:", PROFESSORAS_LISTA, index=1, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Prof. Teoria H3:", PROFESSORAS_LISTA, index=2, key=f"pt3_{data_str}")
        with c2:
            st.markdown("#### 🔊 Responsáveis Solfejo (Sala 9)")
            st1 = st.selectbox("Prof. Solfejo H1:", PROFESSORAS_LISTA, index=3, key=f"st1_{data_str}")
            st2 = st.selectbox("Prof. Solfejo H2:", PROFESSORAS_LISTA, index=4, key=f"st2_{data_str}")
            st3 = st.selectbox("Prof. Solfejo H3:", PROFESSORAS_LISTA, index=5, key=f"st3_{data_str}")
        
        folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button("🚀 Gerar Rodízio de Disciplinas", use_container_width=True):
            # Definição do Carrossel de Matérias por Turma
            # H1: T1(Teo), T2(Sol), T3(Pra) -> H2: T1(Sol), T2(Pra), T3(Teo) ...
            matérias = ["Teoria", "Solfejo", "Prática"]
            
            escala_final = []
            
            # Gera a grade para cada aluna de todas as turmas
            for t_nome, alunas in TURMAS.items():
                t_idx = list(TURMAS.keys()).index(t_nome)
                for i, aluna in enumerate(alunas):
                    agenda_aluna = {"Aluna": aluna, "Turma": t_nome}
                    
                    for h_idx in range(3):
                        h_label = HORARIOS_LABELS[h_idx]
                        # Lógica de carrossel de matérias
                        m_idx = (t_idx + h_idx + offset_semana) % 3
                        m_atual = matérias[m_idx]
                        
                        if m_atual == "Teoria":
                            prof = [pt1, pt2, pt3][h_idx]
                            agenda_aluna[h_label] = f"SALA 8 | Teoria ({prof})"
                        elif m_atual == "Solfejo":
                            prof = [st1, st2, st3][h_idx]
                            agenda_aluna[h_label] = f"SALA 9 | Solfejo ({prof})"
                        else:
                            # Prática: Rotaciona entre Salas 1 a 7 e professoras disponíveis
                            profs_ocup = [pt1, pt2, pt3, st1, st2, st3][h_idx*2 : h_idx*2+2] + folgas
                            profs_p = [p for p in PROFESSORAS_LISTA if p not in profs_ocup]
                            random.seed(i + offset_semana) # Garante que a sala mude toda semana
                            sala_p = (i + offset_semana + h_idx) % 7 + 1
                            prof_p = profs_p[i % len(profs_p)] if profs_p else "Vago"
                            agenda_aluna[h_label] = f"SALA {sala_p} | Prática ({prof_p})"
                    
                    escala_final.append(agenda_aluna)

            st.session_state.calendario_anual[data_str] = {
                "tabela": escala_final,
                "professores": {
                    "teo": [pt1, pt2, pt3],
                    "sol": [st1, st2, st3]
                }
            }
            st.success("Rodízio Gerado com Sucesso!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            df = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.dataframe(df, use_container_width=True)

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
        
        atendendo, sala, mat = "Ninguém alocada", "---", "---"

        for linha in info["tabela"]:
            if f"({p_nome})" in linha.get(h_atual, ""):
                atendendo = linha["Aluna"]
                detalhe = linha[h_atual].split(" | ")
                sala = detalhe[0]
                mat = "Teoria" if "Teoria" in detalhe[1] else "Solfejo" if "Solfejo" in detalhe[1] else "Prática"

        st.info(f"📍 **Local:** {sala} | 👤 **Atendendo:** {atendendo} | 📖 **Matéria:** {mat}")
        
        # --- FORMULÁRIOS ---
        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO PRÁTICA (25 ITENS)")
            difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respirações", "Passagem", "Dedilhado", "Nota Apoio", "Técnica", "Sem dificuldades"]
            cols = st.columns(2)
            for i, d in enumerate(difs): (cols[0] if i < 13 else cols[1]).checkbox(d, key=f"pra_{i}")
        elif mat == "Teoria":
            st.subheader("📋 FORMULÁRIO TEORIA (SALA 8)")
            for t in ["Módulo MSA", "Exercícios Pauta", "Teste Teórico"]: st.checkbox(t)
        elif mat == "Solfejo":
            st.subheader("📋 FORMULÁRIO SOLFEJO (SALA 9)")
            for s in ["Linguagem Rítmica", "Afinação", "Marcação Mão"]: st.checkbox(s)

        st.text_input("🏠 Lição de Casa:")
        st.button("Salvar Aula")
