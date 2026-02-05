import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Sistema 4 Aulas", layout="wide")

# --- BANCO DE DADOS DAS TURMAS ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

HORARIOS = ["08h45 às 09h25", "09h35 às 10h05", "10h10 às 10h40", "10h45 às 11h15"]

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão por Grade Horária")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    t1, t2, t3 = st.tabs(["🗓️ Grade do Dia", "📍 Chamada Geral", "✅ Correção"])

    with t1:
        st.subheader("Visualização da Grade de Rodízio")
        st.info("Esta grade segue o padrão de 4 aulas (Teoria, Prática e Solfejo).")
        
        # Representação da tabela que você enviou
        grade_data = {
            "Sala": ["Teoria", "Solfejo", "Sala 1", "Sala 2", "Sala 3", "Sala 4", "Sala 5", "Sala 6", "Sala 7"],
            "1ª Aula (8h45)": ["Téta (T1)", "Ester (T2)", "Flávia", "Cássia", "Kamyla", "Patrícia", "Elaine", "Roberta", "Luciene"],
            "2ª Aula (9h35)": ["Cássia (T2)", "Ester (T3)", "Flávia", "Vanessa", "Kamyla", "Patrícia", "Elaine", "Téta", "Luciene"],
            "3ª Aula (10h10)": ["Cássia (T3)", "Roberta (T1)", "Flávia", "Ester", "Kamyla", "Patrícia", "Elaine", "Téta", "Vanessa"]
        }
        st.table(pd.DataFrame(grade_data))
        
        if st.button("🔄 Sortear Novas Instrutoras (Aleatório)"):
            st.warning("O sistema embaralhará as instrutoras mantendo a estrutura de turmas.")

    with t2:
        st.subheader("📍 Lista de Presença")
        sel_t = st.selectbox("Filtrar por Turma:", ["Turma 1", "Turma 2", "Turma 3"])
        for aluna in TURMAS[sel_t]:
            st.checkbox(aluna, key=f"cham_{aluna}")

    with t3:
        st.subheader("✅ Checklist de Correção (Secretaria)")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Aluna:", TURMAS["Turma 1"] + TURMAS["Turma 2"] + TURMAS["Turma 3"])
            st.radio("Trouxe Apostila?", ["Sim", "Não"], horizontal=True)
            st.radio("Fez Exercícios Pauta?", ["Sim", "Não"], horizontal=True)
        with col2:
            st.radio("Assistiu Vídeos?", ["Sim", "Não"], horizontal=True)
            st.text_area("Lições de Casa Aprovadas:")
        st.button("Salvar Registro de Correção")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Diário da Professora")
    
    # 1. Identificação
    prof_nome = st.selectbox("Selecione seu Nome:", ["Cássia", "Téta", "Vanessa", "Ester", "Flávia", "Kamyla", "Patrícia", "Elaine", "Roberta", "Luciene"])
    
    # 2. Seleção da Aula/Horário
    aula_atual = st.select_slider("Selecione o Horário da Aula Atual:", options=HORARIOS)

    # Lógica de busca da aluna/turma baseada na sua tabela (Simulação)
    # Exemplo para a 1ª Aula
    info_aula = {"sala": "Não alocada", "atendimento": "---"}
    
    if aula_atual == HORARIOS[0]: # 8h45
        if prof_nome == "Téta": info_aula = {"sala": "Sala Teoria", "atendimento": "Turma 1"}
        elif prof_nome == "Ester": info_aula = {"sala": "Sala Solfejo", "atendimento": "Turma 2"}
        elif prof_nome == "Flávia": info_aula = {"sala": "Sala 1", "atendimento": "Heloísa R."}
        # ... (O sistema mapeia o restante da sua tabela aqui)
    
    # --- PAINEL DE AVISO ---
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📍 MINHA SALA", info_aula['sala'])
    with c2:
        st.metric("👤 ALUNA/TURMA", info_aula['atendimento'])
    with c3:
        st.metric("⏱️ TURNO", "1ª Aula" if aula_atual == HORARIOS[0] else "Próxima")

    st.divider()

    # --- FORMULÁRIOS TÉCNICOS (O que você enviou) ---
    st.subheader("📝 Registro de Avaliação Técnica")
    
    tipo_materia = st.radio("Matéria desta aula:", ["Prática", "Teoria", "Solfejo"], horizontal=True)

    if tipo_materia == "Prática":
        st.selectbox("Lição/Volume:", [str(i) for i in range(1,41)])
        # Os 25 itens técnicos
        difs = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respiração", "Passagem", "Dedilhado", "Nota Apoio", "Sem dificuldades"]
        cols = st.columns(3)
        for i, item in enumerate(difs):
            cols[i%3].checkbox(item, key=f"pr_{i}")

    elif tipo_materia == "Teoria":
        for t in ["Módulo MSA", "Exercícios Pauta", "Vídeos", "Escrita", "Intervalos"]: st.checkbox(t)

    elif tipo_materia == "Solfejo":
        for s in ["Afinação", "Compasso", "Leitura", "Métrica", "Pulsação"]: st.checkbox(s)

    st.divider()
    st.text_input("Tarefa para Casa (Próxima Lição):")
    st.text_area("Observações Finais:")
    
    if st.button("💾 Finalizar e Salvar Aula", use_container_width=True):
        st.balloons()
        st.success("Aula registrada no prontuário da aluna!")
