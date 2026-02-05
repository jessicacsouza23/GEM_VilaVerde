import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Rodízio Dinâmico", layout="wide")

# --- TURMAS REAIS ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 (1ª Aula)", "09h35 (2ª Aula)", "10h10 (3ª Aula)", "10h45 (Teoria/Solfejo Final)"]

# --- ESTADO DO SISTEMA ---
if "config_dia" not in st.session_state:
    st.session_state.config_dia = None

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Rodízio Dinâmico de Alunas e Instrutoras")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_conf, tab_chamada, tab_corr = st.tabs(["⚙️ Configurar Rodízio", "📍 Chamada", "✅ Correção"])

    with tab_conf:
        st.subheader("Definições do Dia")
        c1, c2 = st.columns(2)
        with c1:
            p_teoria = st.selectbox("Professora de Teoria:", PROFESSORAS_LISTA, index=0)
            p_solfejo = st.selectbox("Professora de Solfejo:", PROFESSORAS_LISTA, index=1)
        with c2:
            folgas = st.multiselect("Professoras de Folga:", PROFESSORAS_LISTA)

        if st.button("🚀 Gerar e Publicar Rodízio de Alunas", use_container_width=True):
            # Filtra instrutoras para as 7 salas de prática
            instrutoras_pratica = [p for p in PROFESSORAS_LISTA if p not in folgas and p != p_teoria and p != p_solfejo]
            
            # Criamos a lógica de rotação das turmas
            # Ex: Turno 1 -> T1 na Teoria, T2 no Solfejo, T3 na Prática
            #     Turno 2 -> T3 na Teoria, T1 no Solfejo, T2 na Prática...
            st.session_state.config_dia = {
                "teoria": p_teoria,
                "solfejo": p_solfejo,
                "pratica": instrutoras_pratica[:7], # Pega as 7 disponíveis
                "data": datetime.now().strftime("%d/%m/%Y")
            }
            st.success("Rodízio configurado! As alunas agora rotacionarão automaticamente entre as salas.")

    with tab_chamada:
        st.subheader("Chamada Geral")
        for t_nome, lista in TURMAS.items():
            with st.expander(f"Ver {t_nome}"):
                for aluna in lista: st.checkbox(aluna, key=f"cham_{aluna}")

    with tab_corr:
        st.subheader("Correção de Atividades")
        st.selectbox("Aluna:", [a for lista in TURMAS.values() for a in lista])
        st.radio("Trouxe material?", ["Sim", "Não"], horizontal=True)
        st.text_area("Lições validadas:")
        st.button("Salvar")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Diário da Instrutora")
    
    if not st.session_state.config_dia:
        st.warning("A secretaria ainda não configurou o rodízio de hoje.")
    else:
        conf = st.session_state.config_dia
        p_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário Atual:", options=HORARIOS)

        # LÓGICA DE ROTAÇÃO DE ALUNAS (O coração do rodízio)
        # Vamos definir qual turma está em qual lugar em cada horário
        escala_alunas = {
            HORARIOS[0]: {"teoria": "Turma 1", "solfejo": "Turma 2", "pratica": "Turma 3"},
            HORARIOS[1]: {"teoria": "Turma 2", "solfejo": "Turma 3", "pratica": "Turma 1"},
            HORARIOS[2]: {"teoria": "Turma 3", "solfejo": "Turma 1", "pratica": "Turma 2"},
            HORARIOS[3]: {"teoria": "Todas", "solfejo": "Todas", "pratica": "Encerrado"}
        }

        # Identifica onde a professora está
        if p_nome == conf['teoria']:
            minha_sala = "Sala 8 (Teoria)"
            atendimento = escala_alunas[h_atual]['teoria']
            materia = "Teoria"
        elif p_nome == conf['solfejo']:
            minha_sala = "Sala 9 (Solfejo)"
            atendimento = escala_alunas[h_atual]['solfejo']
            materia = "Solfejo"
        elif p_nome in conf['pratica']:
            idx_prof = conf['pratica'].index(p_nome)
            minha_sala = f"Sala {idx_prof + 1} (Prática)"
            turma_na_pratica = escala_alunas[h_atual]['pratica']
            atendimento = TURMAS[turma_na_pratica][idx_prof] if turma_na_pratica != "Encerrado" else "---"
            materia = "Prática"
        else:
            minha_sala = "Folga / Não alocada"
            atendimento = "---"
            materia = "---"

        # --- PAINEL DE AVISO ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("📍 MINHA SALA", minha_sala)
            st.subheader(f"👤 Atendimento: {atendimento}")
        with c2:
            st.info(f"📚 Matéria: {materia}")
            # Próxima aluna (se for prática)
            if materia == "Prática" and h_atual != HORARIOS[2]:
                idx_h = HORARIOS.index(h_atual)
                prox_turma = escala_alunas[HORARIOS[idx_h+1]]['pratica']
                prox_aluna = TURMAS[prox_turma][conf['pratica'].index(p_nome)]
                st.write(f"➡️ **Próxima aluna:** {prox_aluna}")

        st.divider()

        # --- FORMULÁRIOS TÉCNICOS ---
        if materia == "Prática":
            st.subheader("Checklist Prática (25 Itens)")
            st.selectbox("Lição Atual:", [str(i) for i in range(1,41)])
            difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respiração", "Passagem", "Dedilhado", "Nota Apoio", "Sem dificuldades"]
            cols = st.columns(3)
            for i, d in enumerate(difs): cols[i%3].checkbox(d, key=f"chk_{i}")
        elif materia in ["Teoria", "Solfejo"]:
            st.subheader(f"Avaliação Coletiva - {materia}")
            st.write(f"Avaliando a {atendimento}")
            for item in ["Presença", "Participação", "Exercícios", "Vídeos"]: st.checkbox(item)

        st.text_input("Tarefa de Casa:")
        st.text_area("Observações:")
        if st.button("Finalizar Aula"): st.success("Registrado!")
