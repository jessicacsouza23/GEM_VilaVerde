import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Rotação Total", layout="wide")

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
st.title("🎼 GEM Vila Verde - Rotação Universal")
perfil = st.sidebar.radio("Navegação de Perfil:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_admin = st.tabs(["🗓️ Planejar Sábados", "📍 Chamada", "⚠️ Administração"])

    with tab_gerar:
        st.subheader("Configuração de Rodízio")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Teoria (Responsáveis)")
            pt1 = st.selectbox("Prof. T1:", PROFESSORAS_LISTA, index=0, key=f"pt1_{data_str}")
            pt2 = st.selectbox("Prof. T2:", PROFESSORAS_LISTA, index=1, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Prof. T3:", PROFESSORAS_LISTA, index=2, key=f"pt3_{data_str}")
        with c2:
            st.markdown("#### 🔊 Solfejo (Responsáveis)")
            st1 = st.selectbox("Prof. S1:", PROFESSORAS_LISTA, index=3, key=f"st1_{data_str}")
            st2 = st.selectbox("Prof. S2:", PROFESSORAS_LISTA, index=4, key=f"st2_{data_str}")
            st3 = st.selectbox("Prof. S3:", PROFESSORAS_LISTA, index=5, key=f"st3_{data_str}")
        
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button(f"🚀 Gerar Rodízio 100% Dinâmico para {data_str}", use_container_width=True):
            fixas = [pt1, pt2, pt3, st1, st2, st3]
            prat_disp = [p for p in PROFESSORAS_LISTA if p not in folgas and p not in fixas]
            random.shuffle(prat_disp)
            
            # CRIANDO A GRADE ONDE TUDO MUDA
            grade_dia = []
            for i in range(7):
                instrutora = prat_disp[i] if i < len(prat_disp) else "Vago"
                # Lógica: Sala e Instrutora acompanham o deslocamento da aluna
                grade_dia.append({
                    "Ref. Aluna": TURMAS["Turma 3"][i],
                    "08h45 (H1)": f"Sala {i+1} | Prof. {instrutora}",
                    "09h35 (H2)": f"Sala {(i+1)%7 + 1} | Prof. {prat_disp[(i+1)%len(prat_disp)] if prat_disp else 'Vago'}",
                    "10h10 (H3)": f"Sala {(i+2)%7 + 1} | Prof. {prat_disp[(i+2)%len(prat_disp)] if prat_disp else 'Vago'}"
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
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_admin:
        st.subheader("⚠️ Limpeza de Dados")
        if st.button("🔥 LIMPAR TODO O BANCO DE DADOS"):
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
        
        atendendo, sala, mat = "Não alocada", "---", "---"

        # RASTREAMENTO DINÂMICO
        # 1. Busca na Prática (Carrossel)
        for linha in info["tabela"]:
            if p_nome in linha.get(h_atual, ""):
                atendendo = linha["Ref. Aluna"]
                sala = linha[h_atual].split(" | ")[0]
                mat = "Prática"

        # 2. Busca na Teoria/Solfejo (Rotativo)
        if p_nome == info["config"]["teoria"].get(h_atual):
            sala, atendendo, mat = "Sala 8", "Turma Rotativa", "Teoria"
        elif p_nome == info["config"]["solfejo"].get(h_atual):
            sala, atendendo, mat = "Sala 9", "Turma Rotativa", "Solfejo"

        st.info(f"📍 **{sala}** | 👤 **Atendimento:** {atendendo} | 📖 **Matéria:** {mat}")
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
            for t in ["MSA", "Exercícios Pauta", "Aplicação de Teste", "Leitura de Notas"]: st.checkbox(t, key=f"teo_{t}")

        elif mat == "Solfejo":
            st.subheader("📋 FORMULÁRIO DE SOLFEJO")
            for s in ["Linguagem Rítmica", "Pulsação", "Afinação", "Marcação Manual", "Postura"]: st.checkbox(s, key=f"sol_{s}")

        st.text_input("🏠 Lição de Casa:")
        st.text_area("📝 Observações:")
        st.button("💾 Salvar Atendimento")
