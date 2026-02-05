import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema Integrado", layout="wide", page_icon="🎼")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card { padding: 20px; border-radius: 15px; margin-bottom: 20px; color: white; }
    .pratica-card { background: linear-gradient(135deg, #1e3a8a, #3b82f6); border-left: 10px solid #000033; }
    .teoria-card { background: linear-gradient(135deg, #b45309, #f59e0b); border-left: 10px solid #451a03; }
    .solfejo-card { background: linear-gradient(135deg, #6d28d9, #8b5cf6); border-left: 10px solid #2e1065; }
    .igreja-card { background: linear-gradient(135deg, #059669, #10b981); border-left: 10px solid #064e3b; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}

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

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    perfil = st.radio("Selecione o Perfil:", ["Secretaria", "Instrutora"])
    st.divider()
    st.info("💡 Lembrete: O rodízio garante que alunas e professoras não repitam salas.")

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_presenca, tab_correcao = st.tabs(["🗓️ Gerar Escala", "📍 Chamada", "✅ Correção de Exercícios"])

    with tab_gerar:
        st.subheader("Configuração Semanal")
        data_sel = st.date_input("Data do Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        offset = (data_sel.day // 7) % 7

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📚 Sala 8 (Teoria)")
            pt2 = st.selectbox("Prof. H2 (T1):", PROFESSORAS_LISTA, index=0)
            pt3 = st.selectbox("Prof. H3 (T2):", PROFESSORAS_LISTA, index=1)
            pt4 = st.selectbox("Prof. H4 (T3):", PROFESSORAS_LISTA, index=2)
        with col2:
            st.markdown("#### 🔊 Sala 9 (Solfejo/MSA)")
            st2 = st.selectbox("Prof. H2 (T2):", PROFESSORAS_LISTA, index=3)
            st3 = st.selectbox("Prof. H3 (T3):", PROFESSORAS_LISTA, index=4)
            st4 = st.selectbox("Prof. H4 (T1):", PROFESSORAS_LISTA, index=5)
        
        folgas = st.multiselect("Professoras de Folga:", PROFESSORAS_LISTA)

        if st.button("🚀 Gerar Rodízio Colorido", use_container_width=True):
            fluxo = {
                HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
            }
            grade = []
            for t_nome, alunas in TURMAS.items():
                for i, aluna in enumerate(alunas):
                    row = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "IGREJA (Solfejo Melódico)"}
                    for h_idx in [1, 2, 3]:
                        h_lab = HORARIOS_LABELS[h_idx]
                        conf = fluxo[h_lab]
                        if conf["Teo"] == t_nome: row[h_lab] = f"SALA 8 | Teoria ({conf['ITeo']})"
                        elif conf["Sol"] == t_nome: row[h_lab] = f"SALA 9 | Solfejo/MSA ({conf['ISol']})"
                        else:
                            p_disp = [p for p in PROFESSORAS_LISTA if p not in [conf["ITeo"], conf["ISol"]] + folgas]
                            sala_p = (i + offset + h_idx) % 7 + 1
                            prof_p = p_disp[i % len(p_disp)] if p_disp else "Vago"
                            row[h_lab] = f"SALA {sala_p} | Prática ({prof_p})"
                    grade.append(row)
            st.session_state.calendario_anual[data_str] = {"tabela": grade}
            st.success("Escala gerada com sucesso!")

    with tab_presenca:
        st.subheader("📍 Chamada das Alunas")
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            c1, c2 = st.columns([3, 1])
            c1.write(aluna)
            c2.checkbox("Presente", key=f"pres_{aluna}")
        st.button("Salvar Chamada")

    with tab_correcao:
        st.subheader("📝 Formulário de Correção de Atividades")
        aluna_corr = st.selectbox("Selecione a aluna para corrigir exercícios:", sorted([a for l in TURMAS.values() for a in l]))
        c1, c2 = st.columns(2)
        with c1:
            st.checkbox("Caderno de Pauta em dia?", key="corr_1")
            st.checkbox("Apostila de Teoria preenchida?", key="corr_2")
        with c2:
            st.checkbox("Lições do MSA feitas?", key="corr_3")
            st.checkbox("Vídeos de auxílio assistidos?", key="corr_4")
        st.radio("Status da Atividade:", ["Aprovado", "Corrigir Erros", "Incompleto"], horizontal=True)
        st.text_area("Notas da Correção:")
        st.button("Salvar Correção")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.subheader("👩‍🏫 Portal da Instrutora")
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        p_nome = st.selectbox("Seu Nome:", PROFESSORAS_LISTA)
        h_sel = st.select_slider("Horário:", options=HORARIOS_LABELS)
        info = st.session_state.calendario_anual[d_str]
        
        atend, local, mat = "---", "---", "---"

        if h_sel == HORARIOS_LABELS[0]:
            atend, local, mat = "Todas as Alunas", "Igreja", "Solfejo Melódico"
            st.markdown(f'<div class="main-card igreja-card"><h2>⛪ {mat}</h2><p>{local} | Atendendo: {atend}</p></div>', unsafe_allow_html=True)
        else:
            for linha in info["tabela"]:
                if f"({p_nome})" in linha.get(h_sel, ""):
                    atend, local = linha["Aluna"], linha[h_sel].split(" | ")[0]
                    mat = "Teoria" if "SALA 8" in local else "Solfejo/MSA" if "SALA 9" in local else "Prática"
            
            card_class = "pratica-card" if mat == "Prática" else "teoria-card" if mat == "Teoria" else "solfejo-card"
            icon = "🎹" if mat == "Prática" else "📚" if mat == "Teoria" else "🔊"
            st.markdown(f'<div class="main-card {card_class}"><h2>{icon} {mat}: {atend}</h2><p>{local}</p></div>', unsafe_allow_html=True)

        st.divider()

        # FORMULÁRIO DINÂMICO DE ACORDO COM A MATÉRIA
        if mat == "Prática":
            st.subheader("📋 Avaliação Prática (25 Itens Técnicos)")
            itens = ["Não estudou nada", "Estudo insatisfatório", "Não assistiu os vídeos", "Dificuldade rítmica", "Nomes figuras rítmicas", "Adentrando às teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos arredondados", "Pedal expressão", "Pé esquerdo", "Metrônomo", "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Apostila", "Articulação", "Respiração", "Passagem de dedos", "Dedilhado", "Nota de apoio", "Técnica"]
            col1, col2 = st.columns(2)
            for i, item in enumerate(itens):
                (col1 if i < 13 else col2).checkbox(item, key=f"pra_{i}")
        
        elif mat == "Teoria":
            st.subheader("📋 Avaliação de Teoria (Sala 8)")
            for t in ["Explicação Teórica", "Correção de Pauta", "Aplicação de Teste", "Comportamento"]:
                st.checkbox(t, key=f"teo_{t}")

        elif "Solfejo" in mat:
            st.subheader("📋 Avaliação de Solfejo (Sala 9 ou Igreja)")
            for s in ["Linguagem Rítmica", "Afinação Melódica", "Marcação Mão", "MSA Módulo"]:
                st.checkbox(s, key=f"sol_{s}")

        st.text_input("🏠 Lição para Casa:")
        st.text_area("📝 Observações da Aula:")
        st.button("✅ Salvar Atendimento")
    else:
        st.error("A Secretaria ainda não gerou a escala para este sábado.")
