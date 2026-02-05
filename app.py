import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Rodízio Inteligente", layout="wide")

# --- DEFINIÇÃO DAS TURMAS REAIS ---
TURMAS = {
    "Turma 1": [
        "Rebecca A. - Vila Verde", "Amanda S. - Parque do Carmo II", 
        "Ingrid M. - Parque do Carmo II", "Rebeka S. - Jardim Lígia", 
        "Mellina S. - Jardim Lígia", "Rebeca R. - Vila Ré", "Caroline C. - Vila Ré"
    ],
    "Turma 2": [
        "Vitória A. - Vila Verde", "Elisa F. - Vila Verde", "Sarah S. - Vila Verde", 
        "Gabrielly C. V. - Vila Verde", "Emily O. - Vila Curuçá Velha", 
        "Julya O. - Vila Curuçá Velha", "Stephany O. - Vila Curuçá Velha"
    ],
    "Turma 3": [
        "Heloísa R. - Vila Verde", "Ana Marcela S. - Vila Verde", "Vitória Bella T. - Vila Verde", 
        "Júlia G. S. - Vila Verde", "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", 
        "Júlia Cristina - União de Vila Nova"
    ]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa"]
SALAS_PRATICA = [f"Sala {i}" for i in range(1, 8)]

if "escala_gerada" not in st.session_state:
    st.session_state.escala_gerada = None

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Sistema de Rodízio Aleatório")
perfil = st.sidebar.radio("Selecione a Visão:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_esc, tab_cha, tab_cor = st.tabs(["🗓️ Gerar Rodízio", "📍 Chamada", "✅ Correção"])

    with tab_esc:
        st.subheader("Configuração do Rodízio Semanal")
        
        c1, c2 = st.columns(2)
        with c1:
            folgas = st.multiselect("Professoras de FOLGA hoje:", PROFESSORAS_LISTA)
            p_teoria = st.selectbox("Professora de TEORIA:", [p for p in PROFESSORAS_LISTA if p not in folgas])
            t_teoria = st.selectbox("Turma da TEORIA:", ["Turma 1", "Turma 2", "Turma 3"], key="tt")
        
        with c2:
            p_solfejo = st.selectbox("Professora de SOLFEJO:", [p for p in PROFESSORAS_LISTA if p not in folgas and p != p_teoria])
            t_solfejo = st.selectbox("Turma do SOLFEJO:", ["Turma 1", "Turma 2", "Turma 3"], key="ts")

        if st.button("🎲 Gerar Rodízio Aleatório", use_container_width=True):
            profs_disponiveis = [p for p in PROFESSORAS_LISTA if p not in folgas and p != p_teoria and p != p_solfejo]
            random.shuffle(profs_disponiveis) # Embaralha para ser aleatório
            
            # Identifica qual turma sobrou para a PRÁTICA
            turmas_ocupadas = [t_teoria, t_solfejo]
            turma_pratica = next(t for t in TURMAS.keys() if t not in turmas_ocupadas)
            alunas_pratica = TURMAS[turma_pratica].copy()
            random.shuffle(alunas_pratica)

            escala = []
            
            # 1. Aloca Teoria (Sala Teoria)
            escala.append({"Sala": "Sala Teoria", "Professora": p_teoria, "Aluna/Turma": t_teoria, "Matéria": "Teoria"})
            
            # 2. Aloca Solfejo (Sala Solfejo)
            escala.append({"Sala": "Sala Solfejo", "Professora": p_solfejo, "Aluna/Turma": t_solfejo, "Matéria": "Solfejo"})
            
            # 3. Aloca Prática (Salas 1 a 7) aleatoriamente
            for i, sala in enumerate(SALAS_PRATICA):
                if i < len(profs_disponiveis) and i < len(alunas_pratica):
                    escala.append({
                        "Sala": sala, 
                        "Professora": profs_disponiveis[i], 
                        "Aluna/Turma": alunas_pratica[i], 
                        "Matéria": "Prática"
                    })
            
            st.session_state.escala_gerada = escala
            st.success(f"Rodízio Gerado! Turma na Prática hoje: {turma_pratica}")
            st.table(pd.DataFrame(escala))

    with tab_cha:
        st.subheader("Chamada por Turma")
        turma_sel = st.selectbox("Ver Turma:", ["Turma 1", "Turma 2", "Turma 3"])
        for aluna in TURMAS[turma_sel]:
            st.checkbox(aluna, key=f"check_{aluna}")

    with tab_cor:
        st.subheader("Módulo de Correção")
        aluna_c = st.selectbox("Aluna:", TURMAS["Turma 1"] + TURMAS["Turma 2"] + TURMAS["Turma 3"])
        st.radio("Assistiu os vídeos?", ["Sim", "Não"], horizontal=True)
        st.radio("Trouxe Apostila?", ["Sim", "Não"], horizontal=True)
        st.text_area("Lições de Casa aprovadas:")
        st.button("Salvar Correção")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Área da Professora")
    p_ident = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
    
    if not st.session_state.escala_gerada:
        st.warning("A secretaria ainda não gerou o rodízio aleatório de hoje.")
    else:
        minha_escala = next((item for item in st.session_state.escala_gerada if item['Professora'] == p_ident), None)
        
        if not minha_escala:
            st.info("Você está de folga ou não foi alocada nesta rodada.")
        else:
            # --- AVISO DE PRÓXIMA ALUNA ---
            # Se for prática, a próxima aluna será da mesma turma mas em outro horário, ou troca a turma.
            st.metric("SUA SALA HOJE", minha_escala['Sala'])
            st.subheader(f"Atendimento Atual: {minha_escala['Aluna/Turma']}")
            
            st.divider()

            # --- FORMULÁRIOS TÉCNICOS ---
            mat = minha_escala['Matéria']
            
            if mat == "Prática":
                st.subheader("📋 Checklist de Prática (25 itens)")
                difs_p = [
                    "Não estudou nada", "Estudo insatisfatório", "Não assistiu os vídeos",
                    "Dificuldade rítmica", "Nomes das figuras rítmicas", "Adentrando às teclas",
                    "Postura (costas/ombros/braços)", "Punho alto/baixo", "Não senta no centro",
                    "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                    "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo",
                    "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Atividades apostila",
                    "Articulação ligada/semiligada", "Respirações", "Respirações sobre passagem",
                    "Recurso de dedilhado", "Nota de apoio", "Não apresentou dificuldades"
                ]
                c1, c2 = st.columns(2)
                for i, d in enumerate(difs_p): (c1 if i < 13 else c2).checkbox(d, key=f"p_{i}")
            
            elif mat == "Teoria":
                st.subheader("📋 Avaliação de Teoria")
                st.write(f"Alunas da {minha_escala['Aluna/Turma']}: {', '.join(TURMAS[minha_escala['Aluna/Turma']])}")
                for t in ["Vídeos", "Escrita", "Ritmo", "Intervalos", "Armaduras", "MSA"]: st.checkbox(t)
            
            elif mat == "Solfejo":
                st.subheader("📋 Avaliação de Solfejo")
                st.write(f"Alunas da {minha_escala['Aluna/Turma']}: {', '.join(TURMAS[minha_escala['Aluna/Turma']])}")
                for s in ["Afinação", "Compasso", "Leitura", "Mão", "Pulsação"]: st.checkbox(s)

            st.divider()
            st.text_input("Próxima Lição/Tarefa:")
            st.text_area("Observações Gerais da Aula:")
            st.button("Finalizar e Salvar Aula")
