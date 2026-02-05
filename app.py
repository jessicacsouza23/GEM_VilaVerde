import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Rotação Inteligente", layout="wide")

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
st.title("🎼 GEM Vila Verde - Rotação Universal Inteligente")
perfil = st.sidebar.radio("Navegação de Perfil:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_admin = st.tabs(["🗓️ Planejar Sábados", "📍 Chamada Geral", "⚠️ Administração"])

    with tab_gerar:
        st.subheader("Configuração do Rodízio Dinâmico")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Teoria (Sala 8)")
            pt1 = st.selectbox("Prof. T1 (H1):", PROFESSORAS_LISTA, index=0, key=f"pt1_{data_str}")
            pt2 = st.selectbox("Prof. T2 (H2):", PROFESSORAS_LISTA, index=1, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Prof. T3 (H3):", PROFESSORAS_LISTA, index=2, key=f"pt3_{data_str}")
        with c2:
            st.markdown("#### 🔊 Solfejo (Sala 9)")
            st1 = st.selectbox("Prof. S1 (H1):", PROFESSORAS_LISTA, index=3, key=f"st1_{data_str}")
            st2 = st.selectbox("Prof. S2 (H2):", PROFESSORAS_LISTA, index=4, key=f"st2_{data_str}")
            st3 = st.selectbox("Prof. S3 (H3):", PROFESSORAS_LISTA, index=5, key=f"st3_{data_str}")
        
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button(f"🚀 Gerar Escala Total para {data_str}", use_container_width=True):
            # Mapeamento de quem está em Teoria/Solfejo por Horário
            escala_coletiva = {
                HORARIOS_LABELS[0]: [pt1, st1],
                HORARIOS_LABELS[1]: [pt2, st2],
                HORARIOS_LABELS[2]: [pt3, st3]
            }
            
            # Geração da Grade de Prática
            grade_dia = []
            for i in range(7):
                horarios_aluna = {}
                for h_idx, h_label in enumerate(HORARIOS_LABELS[:3]):
                    # Professoras disponíveis para Prática neste horário específico (Não estão em Teoria/Solfejo nem de Folga)
                    ocupadas = escala_coletiva[h_label] + folgas
                    disponiveis = [p for p in PROFESSORAS_LISTA if p not in ocupadas]
                    random.shuffle(disponiveis)
                    
                    # Alocação Rotativa (Carrossel de Salas e Professoras)
                    prof_alocada = disponiveis[i % len(disponiveis)] if disponiveis else "Vago"
                    sala_alocada = (i + h_idx) % 7 + 1
                    horarios_aluna[h_label] = f"Sala {sala_alocada} | Prof. {prof_alocada}"
                
                grade_dia.append({
                    "Ref. Aluna": TURMAS["Turma 3"][i],
                    **horarios_aluna
                })
            
            st.session_state.calendario_anual[data_str] = {
                "tabela": grade_dia,
                "config": {
                    "teoria": {HORARIOS_LABELS[0]: pt1, HORARIOS_LABELS[1]: pt2, HORARIOS_LABELS[2]: pt3},
                    "solfejo": {HORARIOS_LABELS[0]: st1, HORARIOS_LABELS[1]: st2, HORARIOS_LABELS[2]: st3}
                }
            }
            st.success(f"Escala de {data_str} salva com sucesso!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.subheader("Visualização da Grade de Prática")
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_admin:
        if st.button("🔥 LIMPAR TODO O BANCO DE DADOS"):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Diário da Instrutora")
    data_aula = st.date_input("Data:", value=datetime.now(), key="prof_date")
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        info = st.session_state.calendario_anual[d_str]
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário:", options=HORARIOS_LABELS)
        
        atendendo, sala, mat = "Não alocada", "---", "---"

        # RASTREAMENTO INTELIGENTE
        # 1. Verifica se está em Teoria ou Solfejo (Prioridade)
        if p_nome == info["config"]["teoria"].get(h_atual):
            sala, atendendo, mat = "Sala 8", "Turma Teoria", "Teoria"
        elif p_nome == info["config"]["solfejo"].get(h_atual):
            sala, atendendo, mat = "Sala 9", "Turma Solfejo", "Solfejo"
        else:
            # 2. Se não está nas coletivas, busca automaticamente na Prática
            for linha in info["tabela"]:
                if f"Prof. {p_nome}" in linha.get(h_atual, ""):
                    atendendo = linha["Ref. Aluna"]
                    sala = linha[h_atual].split(" | ")[0]
                    mat = "Prática"
                    break

        st.info(f"📍 **{sala}** | 👤 **Atendendo:** {atendendo} | 📖 **Matéria:** {mat}")
        st.divider()

        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO DE PRÁTICA (25 ITENS)")
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

        elif mat == "Teoria":
            st.subheader("📋 FORMULÁRIO DE TEORIA")
            for t in ["MSA", "Exercícios Pauta", "Aplicação de Teste"]: st.checkbox(t, key=f"t_{t}")

        elif mat == "Solfejo":
            st.subheader("📋 FORMULÁRIO DE SOLFEJO")
            for s in ["Linguagem Rítmica", "Pulsação", "Afinação", "Mão"]: st.checkbox(s, key=f"s_{s}")

        st.text_input("🏠 Lição de Casa:")
        st.button("💾 Salvar Atendimento")
