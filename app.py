import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES ---
SUPABASE_URL = "https://hnpxvxbimkbcxtyniryx.supabase.co"
SUPABASE_KEY = "sb_publishable_sZ7i2TMEbrF2-jCIHj5Edw_8kqvYU2P"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

st.set_page_config(page_title="GEM Vila Verde - Sistema Completo", layout="wide")

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

SALAS_PRATICA = ["Sala 1 (Prática)", "Sala 2 (Prática)", "Sala 3 (Prática)", "Sala 4 (Prática)", "Sala 5 (Prática)", "Sala 6 (Prática)", "Sala 7 (Prática)"]
SALAS_COLETIVAS = ["Sala de Teoria", "Sala de Solfejo"]

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas"]
LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão Integrada")
perfil_teste = st.sidebar.radio("Escolha sua Visão:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil_teste == "Secretaria":
    st.header("📋 Painel da Secretaria")
    tab_chamada, tab_correcao, tab_escala = st.tabs(["📍 Chamada", "✅ Correção de Atividades", "🗓️ Rodízio e Turmas"])

    with tab_chamada:
        st.subheader("Lista de Presença do Dia")
        data_presenca = st.date_input("Data:", value=datetime.now(), key="dt_chamada")
        
        presencas = []
        for aluna in ALUNAS:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(aluna)
            with col2:
                status = st.radio("Status", ["Presente", "Falta", "Justificada"], key=f"cham_{aluna}", label_visibility="collapsed", horizontal=True)
                presencas.append({"Aluna": aluna, "Status": status})
        
        if st.button("Salvar Chamada"):
            st.success(f"Chamada do dia {data_presenca.strftime('%d/%m/%Y')} registrada!")

    with tab_correcao:
        st.subheader("Correção de Materiais (Lição de Casa)")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Selecionar Aluna para Correção:", ALUNAS, key="corr_alu")
            st.multiselect("Materiais Entregues:", CATEGORIAS_LICAO, key="corr_mat")
            st.radio("Trouxe a apostila?", ["Sim", "Não", "Não se aplica"], key="corr_ap")
            st.radio("Fez os exercícios de pauta?", ["Sim", "Incompleto", "Não"], key="corr_pa")
        with c2:
            st.text_area("Lições Realizadas e Aprovadas:", placeholder="Liste as lições que a aluna acertou...", key="corr_ok")
            st.text_area("Lições para Refazer / Dificuldades:", placeholder="Descreva o que ela precisa estudar novamente...", key="corr_pend")
        
        st.divider()
        st.radio("A aluna assistiu aos vídeos da semana?", ["Sim", "Não", "Parcialmente"], key="corr_video")
        if st.button("Finalizar Registro de Correção"):
            st.success("Dados de correção enviados para o histórico da aluna!")

    with tab_escala:
        st.subheader("Gerar Rodízio: Prática + Turmas 1, 2 e 3")
        folgas = st.multiselect("Professoras que FALTARAM ou estão de FOLGA:", PROFESSORAS_LISTA)
        
        if st.button("Gerar e Publicar Escala", use_container_width=True):
            ativas = [p for p in PROFESSORAS_LISTA if p not in folgas]
            if not ativas:
                st.error("Erro: Nenhuma professora disponível.")
            else:
                escala = []
                alunas_restantes = ALUNAS.copy()
                
                # 1. Prática (7 Salas)
                for i, sala in enumerate(SALAS_PRATICA):
                    if i < len(ativas) and alunas_restantes:
                        prof = ativas.pop(0)
                        aluna = alunas_restantes.pop(0)
                        escala.append({"Professor(a)": prof, "Sala": sala, "Aluna/Turma": aluna, "Matéria": "Prática"})

                # 2. Turmas de Teoria/Solfejo (Restante das alunas em 3 Turmas)
                num_turmas = 3
                tamanho = len(alunas_restantes) // num_turmas
                for i in range(num_turmas):
                    turma_nome = f"Turma {i+1}"
                    grupo = alunas_restantes[i*tamanho : (i+1)*tamanho] if i < 2 else alunas_restantes[i*tamanho:]
                    
                    if ativas:
                        prof = ativas.pop(0)
                        sala = SALAS_COLETIVAS[0] if i == 0 else (SALAS_COLETIVAS[1] if i == 1 else "Sala Extra")
                        escala.append({"Professor(a)": prof, "Sala": sala, "Aluna/Turma": f"{turma_nome} ({len(grupo)} alunas)", "Matéria": "Teoria/Solfejo"})
                
                st.table(pd.DataFrame(escala))
                for i in range(num_turmas):
                    grupo = alunas_restantes[i*tamanho : (i+1)*tamanho] if i < 2 else alunas_restantes[i*tamanho:]
                    st.caption(f"**{f'Turma {i+1}'}**: {', '.join(grupo)}")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Registro de Aula")
    c1, c2 = st.columns(2)
    with c1:
        prof_nome = st.selectbox("Sua Identificação:", PROFESSORAS_LISTA)
        mat_aula = st.radio("Matéria ministrada:", ["Prática", "Teoria", "Solfejo"], horizontal=True)
    with c2:
        tipo_atend = st.radio("Atendimento:", ["Individual (Prática)", "Turma (Teoria/Solfejo)"], horizontal=True)
        aluna_atend = st.selectbox("Aluna ou Turma:", ALUNAS + ["Turma 1", "Turma 2", "Turma 3"])

    st.divider()

    if mat_aula == "Prática":
        st.subheader("📋 Avaliação Técnica - Prática (25 Itens)")
        st.selectbox("Lição/Volume Atual:", LICOES_NUM, key="pv")
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

    elif mat_aula == "Teoria":
        st.subheader("📋 Avaliação Técnica - Teoria")
        st.selectbox("Módulo/Página:", LICOES_NUM, key="tv")
        difs_t = [
            "Não assistiu vídeos", "Clave de sol", "Clave de fá", "Não realizou atividades",
            "Dificuldade na escrita musical", "Divisão rítmica teórica", "Ordem das notas (asc/desc)",
            "Intervalos", "Armaduras de clave", "Apostila incompleta", "Não estudou",
            "Estudo insatisfatório", "Não apresentou dificuldades"
        ]
        c1, c2 = st.columns(2)
        for i, d in enumerate(difs_t): (c1 if i < 7 else c2).checkbox(d, key=f"chk_t_{i}")

    elif mat_aula == "Solfejo":
        st.subheader("📋 Avaliação Técnica - Solfejo")
        st.selectbox("Lição de Solfejo:", LICOES_NUM, key="sv")
        difs_s = [
            "Não assistiu vídeos", "Afinação (altura das notas)", "Leitura rítmica",
            "Leitura métrica", "Movimento da mão (compasso)", "Pulsação inconstante",
            "Uso do metrônomo", "Estuda sem metrônomo", "Clave de sol", "Clave de fá",
            "Não estudou nada", "Estudo insatisfatório", "Não apresentou dificuldades"
        ]
        c1, c2 = st.columns(2)
        for i, d in enumerate(difs_s): (c1 if i < 7 else c2).checkbox(d, key=f"chk_s_{i}")

    st.divider()
    st.subheader("🏠 Tarefa para Casa")
    st.text_input("Próxima Lição de Prática:", key="h_p")
    st.text_input("Próxima Lição de Teoria/Solfejo:", key="h_t")
    st.text_area("Observações Finais para a Secretaria:", key="obs_f")
    
    if st.button("Finalizar e Salvar Aula", use_container_width=True):
        st.balloons(); st.success("Aula registrada com sucesso!")
