import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Rodízio Oficial", layout="wide")

# --- DADOS MESTRES ---
ALUNAS = [
    "Amanda S. - Parque do Carmo II", "Ana Marcela S. - Vila Verde", "Caroline C. - Vila Ré",
    "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá Velha", "Gabrielly V. - Vila Verde",
    "Heloísa R. - Vila Verde", "Ingrid M. - Parque do Carmo II", "Júlia Cristina - União de Vila Nova",
    "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá Velha", "Mellina S. - Jardim Lígia",
    "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", "Rebeca R. - Vila Ré",
    "Rebecca A. - Vila Verde", "Rebeka S. - Jardim Lígia", "Sarah S. - Vila Verde",
    "Stephany O. - Vila Curuçá Velha", "Vitória A. - Vila Verde", "Vitória Bella T. - Vila Verde"
]

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa"]

SALAS_PRATICA = [f"Sala {i} (Prática)" for i in range(1, 8)] # 7 salas
SALA_TEORIA = "Sala de Teoria"
SALA_SOLFEJO = "Sala de Solfejo"

# --- ESTADO GLOBAL (Simulando Banco de Dados para teste) ---
if "escala_ativa" not in st.session_state:
    st.session_state.escala_ativa = []

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão Integrada")
perfil_teste = st.sidebar.radio("Escolha sua Visão:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil_teste == "Secretaria":
    st.header("📋 Painel da Secretaria")
    tab_chamada, tab_correcao, tab_escala = st.tabs(["📍 Chamada", "✅ Correção de Atividades", "🗓️ Gerar Rodízio (9 Salas)"])

    with tab_escala:
        st.subheader("Configuração da Escala da Semana")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            prof_teoria = st.selectbox("Professora de TEORIA:", PROFESSORAS_LISTA, index=0)
        with c2:
            prof_solfejo = st.selectbox("Professora de SOLFEJO:", PROFESSORAS_LISTA, index=1)
        with c3:
            folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA)

        if st.button("Gerar e Publicar Rodízio de 9 Salas", use_container_width=True):
            # Filtrar professoras para a PRÁTICA (Quem não está de folga e não é teoria/solfejo)
            profs_pratica = [p for p in PROFESSORAS_LISTA if p not in folgas and p != prof_teoria and p != prof_solfejo]
            
            nova_escala = []
            alunas_restantes = ALUNAS.copy()

            # 1. Alocar Prática (7 salas)
            for i, sala in enumerate(SALAS_PRATICA):
                if i < len(profs_pratica) and alunas_restantes:
                    aluna = alunas_restantes.pop(0)
                    nova_escala.append({"prof": profs_pratica[i], "sala": sala, "aluna": aluna, "materia": "Prática"})

            # 2. Alocar Teoria (Restante dividida)
            meio = len(alunas_restantes) // 2
            alunas_teoria = alunas_restantes[:meio]
            alunas_solfejo = alunas_restantes[meio:]

            nova_escala.append({"prof": prof_teoria, "sala": SALA_TEORIA, "aluna": f"Turma Teoria ({len(alunas_teoria)} alunas)", "materia": "Teoria", "lista": alunas_teoria})
            nova_escala.append({"prof": prof_solfejo, "sala": SALA_SOLFEJO, "aluna": f"Turma Solfejo ({len(alunas_solfejo)} alunas)", "materia": "Solfejo", "lista": alunas_solfejo})

            st.session_state.escala_ativa = nova_escala
            st.success("Rodízio Gerado!")
            st.table(pd.DataFrame(nova_escala)[['prof', 'sala', 'aluna', 'materia']])

    # Manter as outras abas simplificadas para o código não ficar gigante
    with tab_chamada: st.write("Módulo de chamada disponível.")
    with tab_correcao: st.write("Módulo de correção disponível.")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Registro de Aula")
    prof_logada = st.selectbox("Sua Identificação:", PROFESSORAS_LISTA)
    
    # Busca a escala da professora logada
    minha_aula = next((item for item in st.session_state.escala_ativa if item['prof'] == prof_logada), None)

    if not minha_aula:
        st.warning("Você não está escalada para nenhuma sala hoje ou a secretaria ainda não publicou o rodízio.")
    else:
        # Lógica de "Próxima Aluna"
        # Para fins de simulação, pegamos a próxima aluna da lista global se for prática
        try:
            index_atual = ALUNAS.index(minha_aula['aluna'])
            proxima_aluna = ALUNAS[index_atual + 1] if index_atual + 1 < len(ALUNAS) else "Fim do Rodízio"
        except:
            proxima_aluna = "Verificar com Secretaria"

        # --- PAINEL DE AVISO (O que você pediu) ---
        c1, c2 = st.columns(2)
        with c1:
            st.metric(label="📍 SALA ATUAL", value=minha_aula['sala'])
            st.write(f"👤 **Aluna Atual:** {minha_aula['aluna']}")
        with c2:
            st.metric(label="➡️ PRÓXIMA ALUNA", value=proxima_aluna)
            st.caption("A próxima aluna deverá se dirigir à sua sala em 40 minutos.")

        st.divider()
        
        # --- FORMULÁRIOS TÉCNICOS ---
        mat_aula = minha_aula['materia']
        st.subheader(f"Avaliação Técnica - {mat_aula}")

        if mat_aula == "Prática":
            st.selectbox("Lição/Volume Atual:", [str(i) for i in range(1,41)], key="p_v")
            difs_p = ["Não estudou nada", "Estudo insatisfatório", "Não assistiu os vídeos", "Dificuldade rítmica", "Nomes das figuras", "Adentrando teclas", "Postura", "Punho", "Centro", "Falanges", "Unhas", "Dedos", "Pedal", "Pé esquerdo", "Metrônomo", "Sem metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", "Respirações", "Passagem", "Dedilhado", "Nota apoio", "Sem dificuldades"]
            c1, c2 = st.columns(2)
            for i, d in enumerate(difs_p): (c1 if i < 13 else c2).checkbox(d, key=f"p_{i}")

        elif mat_aula == "Teoria":
            if "lista" in minha_aula: st.write(f"**Alunas na sala:** {', '.join(minha_aula['lista'])}")
            st.selectbox("Módulo/Página:", [str(i) for i in range(1,41)], key="t_v")
            difs_t = ["Sem vídeos", "Clave Sol", "Clave Fá", "Sem atividades", "Escrita", "Rítmica", "Notas", "Intervalos", "Armaduras", "Apostila incompleta", "Sem dificuldades"]
            for d in difs_t: st.checkbox(d, key=f"t_{d}")

        elif mat_aula == "Solfejo":
            if "lista" in minha_aula: st.write(f"**Alunas na sala:** {', '.join(minha_aula['lista'])}")
            st.selectbox("Lição Solfejo:", [str(i) for i in range(1,41)], key="s_v")
            difs_s = ["Afinação", "Leitura Rítmica", "Leitura Métrica", "Mão (Compasso)", "Pulsação", "Metrônomo", "Clave Sol", "Clave Fá", "Sem dificuldades"]
            for d in difs_s: st.checkbox(d, key=f"s_{d}")

        st.divider()
        st.text_input("Tarefa para Casa:", key="homework")
        st.text_area("Observações Finais:", key="obs")
        if st.button("Salvar e Finalizar Aula", use_container_width=True):
            st.balloons(); st.success("Registro concluído!")
