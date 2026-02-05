import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema 2026", layout="wide")

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
    tab_gerar, tab_admin = st.tabs(["🗓️ Planejar Sábado", "⚠️ Administração"])

    with tab_gerar:
        st.subheader("Planejamento do Rodízio")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # Lógica de offset semanal para rodar as salas de prática das alunas
        offset_semana = (data_sel.day // 7) % 7

        st.markdown("#### 👩‍🏫 Escala de Instrutoras (H2 até H4)")
        c1, c2 = st.columns(2)
        with c1:
            st.info("Sala 8 - Teoria")
            pt2 = st.selectbox("Instrutora Teoria H2 (T1):", PROFESSORAS_LISTA, index=0, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Instrutora Teoria H3 (T2):", PROFESSORAS_LISTA, index=1, key=f"pt3_{data_str}")
            pt4 = st.selectbox("Instrutora Teoria H4 (T3):", PROFESSORAS_LISTA, index=2, key=f"pt4_{data_str}")
        with c2:
            st.info("Sala 9 - Solfejo/MSA")
            st2 = st.selectbox("Instrutora Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3, key=f"st2_{data_str}")
            st3 = st.selectbox("Instrutora Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4, key=f"st3_{data_str}")
            st4 = st.selectbox("Instrutora Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5, key=f"st4_{data_str}")
        
        folgas = st.multiselect("Instrutoras de FOLGA hoje:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button("🚀 Gerar e Salvar Grade Completa", use_container_width=True):
            escala_final = []
            
            # Mapeamento do Rodízio de Matérias/Turmas
            fluxo = {
                HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
            }

            for t_nome, alunas in TURMAS.items():
                for i, aluna in enumerate(alunas):
                    agenda = {"Aluna": aluna, "Turma": t_nome}
                    
                    # 1ª AULA: IGREJA (Todos Juntos)
                    agenda[HORARIOS_LABELS[0]] = "IGREJA | Solfejo Melódico Coletivo"
                    
                    # 2ª, 3ª e 4ª AULAS: DISTRIBUIÇÃO
                    for h_idx in [1, 2, 3]:
                        h_label = HORARIOS_LABELS[h_idx]
                        config = fluxo[h_label]
                        
                        if config["Teo"] == t_nome:
                            agenda[h_label] = f"SALA 8 | Teoria ({config['ITeo']})"
                        elif config["Sol"] == t_nome:
                            agenda[h_label] = f"SALA 9 | Solfejo/MSA ({config['ISol']})"
                        else:
                            # AULA PRÁTICA: Professora que sobrou vai para sala prática
                            profs_ocupadas = [config["ITeo"], config["ISol"]] + folgas
                            disponiveis_pratica = [p for p in PROFESSORAS_LISTA if p not in profs_ocupadas]
                            
                            # Rotação de Sala (1-7) para a aluna não repetir lugar
                            sala_p = (i + offset_semana + h_idx) % 7 + 1
                            instrutora_p = disponiveis_pratica[i % len(disponiveis_pratica)] if disponiveis_pratica else "Vago"
                            agenda[h_label] = f"SALA {sala_p} | Prática ({instrutora_p})"
                    
                    escala_final.append(agenda)

            st.session_state.calendario_anual[data_str] = {"tabela": escala_final}
            st.success(f"Grade de {data_str} salva com sucesso!")

        if data_str in st.session_state.calendario_anual:
            st.divider()
            df = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.dataframe(df, use_container_width=True)

    with tab_admin:
        if st.button("🔥 LIMPAR TODO O HISTÓRICO"):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Diário de Classe")
    data_aula = st.date_input("Data da Aula:", value=datetime.now())
    d_str = data_aula.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        instrutora_sel = st.selectbox("Quem é você?", PROFESSORAS_LISTA)
        horario_sel = st.select_slider("Horário da Aula:", options=HORARIOS_LABELS)
        info = st.session_state.calendario_anual[d_str]
        
        # Busca automática de onde a instrutora deve estar e quem atender
        aluna_atual, local_atual, materia_atual = "---", "---", "---"

        if horario_sel == HORARIOS_LABELS[0]:
            local_atual, aluna_atual, materia_atual = "Igreja", "Todas as Alunas", "Solfejo Melódico"
        else:
            for linha in info["tabela"]:
                if f"({instrutora_sel})" in linha.get(horario_sel, ""):
                    aluna_atual = linha["Aluna"]
                    partes = linha[horario_sel].split(" | ")
                    local_atual = partes[0]
                    materia_atual = "Teoria" if "SALA 8" in local_atual else "Solfejo/MSA" if "SALA 9" in local_atual else "Prática"

        st.warning(f"📍 **Local:** {local_atual} | 👤 **Aluna:** {aluna_atual} | 📖 **Matéria:** {materia_atual}")
        st.divider()

        # FORMULÁRIOS DINÂMICOS
        if materia_atual == "Prática":
            st.subheader("📋 AVALIAÇÃO PRÁTICA (25 ITENS)")
            itens = ["Não estudou", "Insatisfatório", "Sem vídeos", "Rítmica", "Figuras", "Teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé Esq", "Metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respirações", "Passagem", "Dedilhado", "Nota Apoio", "Técnica", "Sem dificuldades"]
            c1, c2 = st.columns(2)
            for i, item in enumerate(itens): (c1 if i < 13 else c2).checkbox(item, key=f"pra_{i}")
        
        elif "Solfejo" in materia_atual:
            st.subheader("📋 AVALIAÇÃO DE SOLFEJO")
            for s in ["Afinação", "Pulsação", "Ritmo", "Mão/Compasso"]: st.checkbox(s, key=f"s_{s}")
            
        elif materia_atual == "Teoria":
            st.subheader("📋 AVALIAÇÃO DE TEORIA")
            for t in ["MSA", "Exercícios", "Teste"]: st.checkbox(t, key=f"t_{t}")

        st.text_input("🏠 Lição para Casa:")
        st.button("💾 Salvar Atendimento")
