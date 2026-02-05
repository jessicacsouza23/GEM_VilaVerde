import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES SUPABASE (Mantidas para salvar os dados se o banco estiver ok) ---
SUPABASE_URL = "https://hnpxvxbimkbcxtyniryx.supabase.co"
SUPABASE_KEY = "sb_publishable_sZ7i2TMEbrF2-jCIHj5Edw_8kqvYU2P"
HEADERS = {
    "apikey": SUPABASE_KEY, 
    "Authorization": f"Bearer {SUPABASE_KEY}", 
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.set_page_config(page_title="GEM Vila Verde - Protótipo", layout="wide")

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

SALAS_RODIZIO = [
    "Sala 1 (Prática)", "Sala 2 (Prática)", "Sala 3 (Prática)", "Sala 4 (Prática)", 
    "Sala 5 (Prática)", "Sala 6 (Prática)", "Sala 7 (Prática)", 
    "Sala de Teoria", "Sala de Solfejo"
]

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas"]
LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# --- FUNÇÕES ---
def publicar_escala_banco(dados):
    url = f"{SUPABASE_URL}/rest/v1/agenda_aulas"
    try:
        return requests.post(url, json=dados, headers=HEADERS)
    except: return None

# --- INTERFACE PRINCIPAL ---
st.title("🎼 GEM Vila Verde - Gestão Integrada")
st.markdown("---")

# Seleção de Visão para teste
perfil_teste = st.sidebar.radio("Escolha sua Visão:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil_teste == "Secretaria":
    st.header("📋 Painel da Secretaria")
    tab_corr, tab_esc = st.tabs(["✅ Correção de Atividades", "🗓️ Gerar Rodízio"])

    with tab_corr:
        st.subheader("Registro de Correção de Lições (Casa)")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Aluna:", ALUNAS, key="s_alu")
            st.multiselect("Materiais Corrigidos:", CATEGORIAS_LICAO, key="s_mat")
            st.checkbox("Trouxe a apostila?", key="s_ap")
            st.checkbox("Fez os exercícios de pauta?", key="s_pa")
        with c2:
            st.text_area("Lições Realizadas (OK):", placeholder="Ex: MSA Lição 1 a 5 aprovadas", key="s_ok")
            st.text_area("Pendências (Para Refazer):", placeholder="O que precisa de correção?", key="s_pend")
        if st.button("Salvar Correção"):
            st.success("Simulação: Registro de correção salvo!")

    with tab_esc:
        st.subheader("Gerar Rodízio Automático por Folga")
        data_escala = st.date_input("Data da Aula:", format="DD/MM/YYYY")
        folgas = st.multiselect("Quem está de FOLGA hoje?", PROFESSORAS_LISTA)
        
        if st.button("Publicar Escala Automática", use_container_width=True):
            ativas = [p for p in PROFESSORAS_LISTA if p not in folgas]
            if not ativas:
                st.error("Nenhuma professora disponível!")
            else:
                nova_agenda = []
                for i, sala in enumerate(SALAS_RODIZIO):
                    if i < len(ativas):
                        mat = "Prática" if "Prática" in sala else ("Teoria" if "Teoria" in sala else "Solfejo")
                        nova_agenda.append({
                            "data": str(data_escala), "professor": ativas[i],
                            "materia": mat, "sala": sala, "aluna": ALUNAS[i % len(ALUNAS)]
                        })
                st.session_state.agenda_simulada = nova_agenda
                st.success("Rodízio gerado com sucesso!")
                st.table(pd.DataFrame(nova_agenda)[['professor', 'sala', 'aluna']])

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Registro de Aula (Professora)")
    prof_atual = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
    
    # Simulação de busca de aula
    st.info(f"Bem-vinda, Irmã {prof_atual}. Abaixo está o formulário para preenchimento da aula.")
    
    materia_aula = st.radio("Selecione a Matéria desta aula:", ["Prática", "Teoria", "Solfejo"], horizontal=True)
    aluna_aula = st.selectbox("Selecione a Aluna que está com você:", ALUNAS)
    
    st.divider()

    # --- FORMULÁRIO DE PRÁTICA (25 ITENS) ---
    if materia_aula == "Prática":
        st.subheader("Avaliação Técnica - Prática")
        st.selectbox("Lição/Volume Atual *", LICOES_NUM, key="p_v")
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

    # --- FORMULÁRIO DE TEORIA ---
    elif materia_aula == "Teoria":
        st.subheader("Avaliação Técnica - Teoria")
        st.selectbox("Módulo/Página *", LICOES_NUM, key="t_v")
        difs_t = [
            "Não assistiu vídeos complementares", "Clave de sol", "Clave de fá", 
            "Não realizou atividades", "Dificuldade na escrita musical", 
            "Divisão rítmica teórica", "Ordem das notas (asc/desc)", 
            "Intervalos", "Armaduras de clave", "Apostila incompleta", 
            "Não estudou nada", "Estudo insatisfatório", "Não apresentou dificuldades"
        ]
        c1, c2 = st.columns(2)
        for i, d in enumerate(difs_t): (c1 if i < 7 else c2).checkbox(d, key=f"t_{i}")

    # --- FORMULÁRIO DE SOLFEJO ---
    elif materia_aula == "Solfejo":
        st.subheader("Avaliação Técnica - Solfejo")
        st.selectbox("Lição Solfejo *", LICOES_NUM, key="s_v")
        difs_s = [
            "Não assistiu vídeos", "Afinação (altura das notas)", 
            "Leitura rítmica", "Leitura métrica", "Movimento da mão (compasso)", 
            "Pulsação inconstante", "Uso do metrônomo", "Estuda sem metrônomo", 
            "Clave de sol", "Clave de fá", "Não estudou nada", 
            "Estudo insatisfatório", "Não apresentou dificuldades"
        ]
        c1, c2 = st.columns(2)
        for i, d in enumerate(difs_s): (c1 if i < 7 else c2).checkbox(d, key=f"s_{i}")

    st.divider()
    st.subheader("🏠 Tarefa para Casa")
    st.text_input("Lição de Prática para próxima aula:", key="casa_p")
    st.text_input("Tarefa de Teoria/Apostila:", key="casa_t")
    st.text_area("Observações Finais da Aula:", key="obs_final")
    
    if st.button("Finalizar e Salvar Registro", use_container_width=True):
        st.balloons()
        st.success("Simulação: Aula registrada com sucesso!")
