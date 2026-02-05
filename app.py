import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema Integral", layout="wide")

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

SALAS_PRATICA = [f"Sala {i} (Prática)" for i in range(1, 8)] # 7 Salas
SALA_TEORIA = "Sala 8 (Teoria)"
SALA_SOLFEJO = "Sala 9 (Solfejo)"

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas"]
LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# --- ESTADO GLOBAL (Simulando Banco) ---
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

    with tab_chamada:
        st.subheader("Lista de Presença do Dia")
        data_c = st.date_input("Data da Aula:", value=datetime.now())
        
        chamada_data = []
        for aluna in ALUNAS:
            c1, c2 = st.columns([3, 2])
            with c1: st.write(f"**{aluna}**")
            with c2: 
                status = st.radio("Status", ["Presente", "Falta", "Justificada"], key=f"ch_{aluna}", horizontal=True, label_visibility="collapsed")
                chamada_data.append({"Aluna": aluna, "Status": status})
        
        if st.button("Salvar Chamada Geral"):
            st.success("Chamada registrada com sucesso!")

    with tab_correcao:
        st.subheader("Módulo de Correção (Lição de Casa)")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Selecionar Aluna:", ALUNAS, key="cor_alu")
            st.multiselect("Materiais Corrigidos:", CATEGORIAS_LICAO, key="cor_mat")
            st.radio("Trouxe a apostila?", ["Sim", "Não", "Esqueceu"], key="cor_ap")
            st.radio("Fez os exercícios de pauta?", ["Sim", "Não", "Incompleto"], key="cor_pauta")
        with c2:
            st.text_area("Lições Aprovadas (OK):", placeholder="Ex: MSA Lição 1 a 5", key="cor_ok")
            st.text_area("Pendências / Para Refazer:", placeholder="Ex: Erro rítmico na lição 6", key="cor_pend")
            st.radio("Assistiu aos vídeos da semana?", ["Sim", "Não", "Em parte"], key="cor_vid")
        
        if st.button("Registrar Correção"):
            st.success("Dados de correção salvos!")

    with tab_escala:
        st.subheader("Configuração das 9 Salas")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            p_teoria = st.selectbox("Professora de TEORIA (Sala 8):", PROFESSORAS_LISTA, index=0)
        with col_b:
            p_solfejo = st.selectbox("Professora de SOLFEJO (Sala 9):", PROFESSORAS_LISTA, index=1)
        with col_c:
            folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA)

        if st.button("Publicar Rodízio Oficial", use_container_width=True):
            # Filtra profs para as 7 salas de prática
            profs_pratica = [p for p in PROFESSORAS_LISTA if p not in folgas and p != p_teoria and p != p_solfejo]
            
            nova_escala = []
            alunas_fila = ALUNAS.copy()

            # Alocar Prática (1 a 7)
            for i, sala in enumerate(SALAS_PRATICA):
                if i < len(profs_pratica) and alunas_fila:
                    aluna = alunas_fila.pop(0)
                    nova_escala.append({"prof": profs_pratica[i], "sala": sala, "aluna": aluna, "materia": "Prática"})

            # Alocar Teoria e Solfejo (8 e 9)
            meio = len(alunas_fila) // 2
            nova_escala.append({"prof": p_teoria, "sala": SALA_TEORIA, "aluna": "Turma Teoria", "materia": "Teoria", "lista": alunas_fila[:meio]})
            nova_escala.append({"prof": p_solfejo, "sala": SALA_SOLFEJO, "aluna": "Turma Solfejo", "materia": "Solfejo", "lista": alunas_fila[meio:]})

            st.session_state.escala_ativa = nova_escala
            st.success("Rodízio das 9 Salas Publicado!")
            st.table(pd.DataFrame(nova_escala)[['prof', 'sala', 'aluna', 'materia']])

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Registro de Aula")
    prof_nome = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
    
    aula_info = next((item for item in st.session_state.escala_ativa if item['prof'] == prof_nome), None)

    if not aula_info:
        st.warning("Escala não encontrada. Peça para a secretaria gerar o rodízio.")
    else:
        # Lógica Próxima Aluna
        try:
            total_alunas = ALUNAS
            idx_atual = total_alunas.index(aula_info['aluna']) if aula_info['materia'] == "Prática" else -1
            proxima = total_alunas[idx_atual + 7] if (idx_atual + 7) < len(total_alunas) else "Fim do período"
        except: proxima = "Consultar Secretaria"

        # --- AVISO DE SALA E PRÓXIMA ---
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"📍 **SALA ATUAL:** {aula_info['sala']}")
            st.write(f"👤 **ALUNA:** {aula_info['aluna']}")
        with c2:
            st.warning(f"➡️ **PRÓXIMA ALUNA:** {proxima}")
            st.caption("Aguarde a troca de turno para chamar a próxima.")

        st.divider()

        # --- FORMULÁRIO TÉCNICO COMPLETO ---
        if aula_info['materia'] == "Prática":
            st.subheader("Checklist de Prática (25 itens)")
            st.selectbox("Lição/Volume Atual:", LICOES_NUM, key="p_v")
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
            for i, d in enumerate(difs_p): (c1 if i < 13 else c2).checkbox(d, key=f"chk_p_{i}")

        elif aula_info['materia'] == "Teoria":
            st.subheader("Avaliação de Teoria")
            st.write(f"**Alunas na sala:** {', '.join(aula_info.get('lista', []))}")
            st.selectbox("Módulo/Página:", LICOES_NUM, key="t_v")
            difs_t = ["Não assistiu vídeos", "Clave de sol", "Clave de fá", "Escrita musical", "Divisão rítmica", "Ordem das notas", "Intervalos", "Armaduras", "Apostila incompleta", "Não estudou", "Não apresentou dificuldades"]
            for d in difs_t: st.checkbox(d, key=f"chk_t_{d}")

        elif aula_info['materia'] == "Solfejo":
            st.subheader("Avaliação de Solfejo")
            st.write(f"**Alunas na sala:** {', '.join(aula_info.get('lista', []))}")
            st.selectbox("Lição Solfejo:", LICOES_NUM, key="s_v")
            difs_s = ["Afinação (altura)", "Leitura rítmica", "Leitura métrica", "Movimento mão (compasso)", "Pulsação", "Metrônomo", "Clave de sol", "Clave de fá", "Não estudou", "Não apresentou dificuldades"]
            for d in difs_s: st.checkbox(d, key=f"chk_s_{d}")

        st.divider()
        st.subheader("🏠 Próxima Aula")
        st.text_input("Tarefa de Prática:", key="tp")
        st.text_input("Tarefa de Teoria/Solfejo:", key="tt")
        st.text_area("Observações Finais:", key="obs")
        if st.button("Finalizar e Enviar Aula", use_container_width=True):
            st.balloons(); st.success("Aula registrada!")
