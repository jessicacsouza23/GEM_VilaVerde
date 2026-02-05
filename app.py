import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Pro", layout="wide", page_icon="🎼")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4CAF50; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #ffffff; border-radius: 5px; padding: 10px; }
    .card-pratica { padding: 20px; border-radius: 10px; background-color: #e3f2fd; border-left: 5px solid #2196f3; }
    .card-teoria { padding: 20px; border-radius: 10px; background-color: #fff3e0; border-left: 5px solid #ff9800; }
    .card-solfejo { padding: 20px; border-radius: 10px; background-color: #f3e5f5; border-left: 5px solid #9c27b0; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS MESTRE ---
if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}
if "chamada_data" not in st.session_state:
    st.session_state.chamada_data = {}

TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
TODAS_ALUNAS = sorted([aluna for lista in TURMAS.values() for aluna in lista])
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

# --- INTERFACE LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3844/3844724.png", width=100)
    st.title("GEM Vila Verde")
    perfil = st.radio("Módulo:", ["🏠 Início / Secretaria", "👩‍🏫 Portal Instrutora"])
    st.divider()
    st.caption("Sistema de Gestão GEM v2.0")

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Início / Secretaria":
    tab_gerar, tab_chamada, tab_correcao, tab_admin = st.tabs([
        "🗓️ Planejar Sábado", "📍 Chamada Geral", "✅ Correção de Exercícios", "⚠️ Configurações"
    ])

    with tab_gerar:
        st.subheader("Configuração do Rodízio")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        offset_semana = (data_sel.day // 7) % 7

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📚 Teoria (Sala 8)")
            pt2 = st.selectbox("Instrutora H2 (T1):", PROFESSORAS_LISTA, index=0)
            pt3 = st.selectbox("Instrutora H3 (T2):", PROFESSORAS_LISTA, index=1)
            pt4 = st.selectbox("Instrutora H4 (T3):", PROFESSORAS_LISTA, index=2)
        with col2:
            st.markdown("### 🔊 Solfejo (Sala 9)")
            st2 = st.selectbox("Instrutora H2 (T2):", PROFESSORAS_LISTA, index=3)
            st3 = st.selectbox("Instrutora H3 (T3):", PROFESSORAS_LISTA, index=4)
            st4 = st.selectbox("Instrutora H4 (T1):", PROFESSORAS_LISTA, index=5)
        
        folgas = st.multiselect("Folgas do Dia:", PROFESSORAS_LISTA)

        if st.button("🚀 Gerar e Publicar Escala Colorida"):
            fluxo = {
                HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
            }
            escala_final = []
            for t_nome, alunas in TURMAS.items():
                for i, aluna in enumerate(alunas):
                    ag = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "IGREJA (Solfejo Melódico)"}
                    for h_idx in [1, 2, 3]:
                        h_lab = HORARIOS_LABELS[h_idx]
                        conf = fluxo[h_lab]
                        if conf["Teo"] == t_nome: ag[h_lab] = f"SALA 8 | Teoria ({conf['ITeo']})"
                        elif conf["Sol"] == t_nome: ag[h_lab] = f"SALA 9 | Solfejo/MSA ({conf['ISol']})"
                        else:
                            p_ocup = [conf["ITeo"], conf["ISol"]] + folgas
                            p_disp = [p for p in PROFESSORAS_LISTA if p not in p_ocup]
                            sala_p = (i + offset_semana + h_idx) % 7 + 1
                            inst_p = p_disp[i % len(p_disp)] if p_disp else "Vago"
                            ag[h_lab] = f"SALA {sala_p} | Prática ({inst_p})"
                    escala_final.append(ag)
            st.session_state.calendario_anual[data_str] = {"tabela": escala_final}
            st.balloons()

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.dataframe(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]), use_container_width=True)

    with tab_chamada:
        st.subheader(f"📍 Presença: {data_str if 'data_str' in locals() else ''}")
        col_c1, col_c2 = st.columns([2, 1])
        for aluna in TODAS_ALUNAS:
            c = st.container()
            c1, c2, c3 = c.columns([3, 1, 1])
            c1.write(f"**{aluna}**")
            c2.checkbox("Presente", key=f"pres_{aluna}")
            c3.checkbox("Justificado", key=f"just_{aluna}")
        st.button("Salvar Chamada Geral")

    with tab_correcao:
        st.subheader("✅ Correção de Exercícios (Secretaria/Instrutora)")
        sel_alu = st.selectbox("Selecione a Aluna para Validar:", TODAS_ALUNAS)
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("**Materiais Entregues**")
            st.checkbox("Caderno de Pauta", key="v1")
            st.checkbox("Apostila de Teoria", key="v2")
            st.checkbox("Método MSA", key="v3")
        with col_v2:
            st.markdown("**Status dos Exercícios**")
            st.radio("Resultado:", ["Tudo Correto", "Corrigir Erros", "Não Fez"], horizontal=True)
        st.text_area("Observações da Correção:")
        st.button("Registrar Validação")

    with tab_admin:
        if st.button("🔥 RESET TOTAL DO SISTEMA"):
            st.session_state.clear()
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.subheader("👩‍🏫 Portal da Instrutora")
    data_aula = st.date_input("Data da Aula:", value=datetime.now(), key="p_data")
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        instr_sel = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        hr_sel = st.select_slider("Horário da Aula:", options=HORARIOS_LABELS)
        
        info = st.session_state.calendario_anual[d_str]
        aluna_atend, local_atend, mat_atend = "---", "---", "---"

        if hr_sel == HORARIOS_LABELS[0]:
            local_atend, aluna_atend, mat_atend = "Igreja", "Todas", "Solfejo Melódico"
        else:
            for linha in info["tabela"]:
                if f"({instr_sel})" in linha.get(hr_sel, ""):
                    aluna_atend = linha["Aluna"]
                    local_atend = linha[hr_sel].split(" | ")[0]
                    mat_atend = "Teoria" if "SALA 8" in local_atend else "Solfejo/MSA" if "SALA 9" in local_atend else "Prática"

        # --- CABEÇALHO COLORIDO DO ATENDIMENTO ---
        if mat_atend == "Prática":
            st.markdown(f'<div class="card-pratica"><h3>🎸 Aula Prática: {aluna_atend}</h3><p>Local: {local_atend}</p></div>', unsafe_allow_html=True)
        elif mat_atend == "Teoria":
            st.markdown(f'<div class="card-teoria"><h3>📖 Aula de Teoria: {aluna_atend}</h3><p>Local: {local_atend}</p></div>', unsafe_allow_html=True)
        elif mat_atend == "Solfejo/MSA":
            st.markdown(f'<div class="card-solfejo"><h3>🔊 Solfejo/MSA: {aluna_atend}</h3><p>Local: {local_atend}</p></div>', unsafe_allow_html=True)
        else:
            st.info(f"📍 Local: {local_atend} | Matéria: {mat_atend}")

        st.divider()

        # --- FORMULÁRIOS DINÂMICOS ---
        if mat_atend == "Prática":
            st.markdown("#### 📋 Checklist de Técnica (25 Itens)")
            itens = [
                "Não estudou", "Estudo insatisfatório", "Não assistiu vídeos", "Dificuldade rítmica",
                "Nomes figuras rítmicas", "Adentrando às teclas", "Postura (Costas/Braços)", "Punho (Alto/Baixo)",
                "Não senta no centro", "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo", "Estuda sem metrônomo",
                "Clave de sol", "Clave de fá", "Atividades apostila", "Articulação ligada/semiligada",
                "Respirações", "Respirações passagem", "Recurso de dedilhado", "Nota de apoio", "Sem dificuldades"
            ]
            col_f1, col_f2 = st.columns(2)
            for i, item in enumerate(itens):
                (col_f1 if i < 13 else col_f2).checkbox(item, key=f"p_item_{i}")

        elif mat_atend == "Teoria":
            st.markdown("#### 📖 Avaliação de Teoria")
            c1, c2 = st.columns(2)
            with c1:
                st.checkbox("Explicou Matéria Nova", key="t_new")
                st.checkbox("Corrigiu Exercícios", key="t_corr")
            with c2:
                st.checkbox("Aplicou Teste", key="t_test")
                st.checkbox("Dificuldade em Claves", key="t_clav")

        elif mat_atend == "Solfejo/MSA":
            st.markdown("#### 🔊 Avaliação de Solfejo/MSA")
            c1, c2 = st.columns(2)
            with c1:
                st.checkbox("Linguagem Rítmica OK", key="s_rit")
                st.checkbox("Afinação Melódica OK", key="s_afin")
            with c2:
                st.checkbox("Marcação de Compasso", key="s_comp")
                st.checkbox("Módulo MSA Concluído", key="s_msa")

        st.divider()
        st.text_input("🏠 Lição para Casa:", placeholder="Digite as páginas ou lições...")
        st.text_area("📝 Observações Gerais:")
        if st.button("💾 Salvar Registro de Aula"):
            st.success("Registro salvo com sucesso!")
    else:
        st.warning("⚠️ Escala não encontrada para esta data. Peça para a Secretaria gerar o planejamento.")
