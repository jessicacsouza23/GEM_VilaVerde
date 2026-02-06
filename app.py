import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account
import re

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (FIRESTORE) BLINDADA ---
def init_connection():
    try:
        # Limpeza agressiva da chave para evitar erros de padding/65 caracteres
        raw_key = st.secrets["private_key"]
        # Remove espaços em branco, quebras de linha extras e normaliza o formato
        clean_key = raw_key.replace("\\n", "\n").strip()
        
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": clean_key,
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"],
        }
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=st.secrets["project_id"])
    except Exception as e:
        st.error(f"⚠️ Erro de Conexão: {e}")
        return None

db = init_connection()

# --- FUNÇÕES DE PERSISTÊNCIA ---
def db_save(colecao, documento, dados):
    if db:
        try:
            db.collection(colecao).document(documento).set(dados)
            return True
        except: return False
    return False

def db_get_all(colecao):
    if db:
        try:
            return [doc.to_dict() for doc in db.collection(colecao).stream()]
        except: return []
    return []

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
SECRETARIAS = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"]
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

# --- DIFICULDADES (INTEGRAL) ---
DIFICULDADES_PRATICA = [
    "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos dos métodos",
    "Dificuldade ritmica", "Dificuldade em distinguir os nomes das figuras ritmicas",
    "Está adentrando às teclas", "Dificuldade com a postura (costas, ombros e braços)",
    "Está deixando o punho alto ou baixo", "Não senta no centro da banqueta", "Está quebrando as falanges",
    "Unhas muito compridas", "Dificuldade em deixar os dedos arredondados",
    "Esquece de colocar o pé direito no pedal de expressão", "Faz movimentos desnecessários com o pé esquerdo na pedaleira",
    "Dificuldade com o uso do metrônomo", "Estuda sem o metrônomo", "Dificuldades em ler as notas na clave de sol",
    "Dificuldades em ler as notas na clave de fá", "Não realizou as atividades da apostila",
    "Dificuldade em fazer a articulação ligada e semiligada", "Dificuldade com as respirações",
    "Dificuldade com as respirações sobre passagem", "Dificuldades em recurso de dedilhado",
    "Dificuldade em fazer nota de apoio", "Não apresentou dificuldades"
]

DIFICULDADES_TEORIA = [
    "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
    "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
    "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
    "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
    "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
    "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
]

# --- INTERFACE ---
st.sidebar.title("🎹 Gestão GEM 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    st.header("🏠 Central da Secretaria")
    tab_escala, tab_resumo = st.tabs(["🗓️ Escala Semanal", "📋 Resumo de Atividades"])
    
    with tab_escala:
        data_s = st.date_input("Data do Sábado:", value=datetime.now())
        if st.button("🚀 Gerar Rodízio"):
            # Lógica de Rodízio Salva no Firestore
            escala = []
            for t, alunas in TURMAS.items():
                for a in alunas:
                    escala.append({"Aluna": a, "Turma": t, HORARIOS_LABELS[1]: "Prática", HORARIOS_LABELS[2]: "Teoria"})
            db_save("rodizios", data_s.strftime("%d_%m_%Y"), {"id": data_s.strftime("%d/%m/%Y"), "dados": escala})
            st.success("Escala de rodízio enviada ao banco!")
            
    with tab_resumo:
        st.subheader("📋 Resumo para Secretaria")
        registros = db_get_all("historico_geral")
        if registros:
            df_sec = pd.DataFrame(registros)
            st.metric("Total de Atendimentos", len(df_sec))
            st.dataframe(df_sec[["Data", "Aluna", "Materia", "Instrutora"]].sort_values("Data", ascending=False))

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe Digital")
    instr_sel = st.selectbox("Instrutora:", PROFESSORAS_LISTA)
    data_aula = st.date_input("Data da Aula:")
    d_str = data_aula.strftime("%d/%m/%Y")
    
    col_h, col_m = st.columns(2)
    with col_h: h_sel = st.radio("Horário:", HORARIOS_LABELS)
    with col_m: 
        mat = st.selectbox("Matéria:", ["Prática", "Teoria", "Solfejo"])
        aluna_n = st.selectbox("Aluna:", sorted([a for t in TURMAS.values() for a in t]))

    st.subheader("🔍 Avaliação Técnica")
    lista_dif = DIFICULDADES_PRATICA if mat == "Prática" else DIFICULDADES_TEORIA
    selecionadas = []
    c1, c2 = st.columns(2)
    for i, d in enumerate(lista_dif):
        if (c1 if i < 13 else c2).checkbox(d): selecionadas.append(d)
    
    st.subheader("🎯 Planejamento Pedagógico")
    obs = st.text_area("Relato de Evolução (Histórico):")
    metas = st.text_area("Metas para a Próxima Aula:")
    dica_banca = st.text_area("Dicas Específicas para a Banca Semestral:")

    if st.button("💾 SALVAR AULA E CONGELAR ANÁLISE"):
        doc_id = f"{aluna_n}_{datetime.now().timestamp()}".replace(".","")
        dados = {
            "Data": d_str, "Aluna": aluna_n, "Materia": mat, 
            "Dificuldades": selecionadas, "Obs": obs, "Metas": metas,
            "Dica_Banca": dica_banca, "Instrutora": instr_sel, "Horario": h_sel
        }
        if db_save("historico_geral", doc_id, dados):
            st.success(f"✅ Análise de {aluna_n} salva e congelada com sucesso!")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise Pedagógica Completa")
    hist = db_get_all("historico_geral")
    
    if hist:
        df = pd.DataFrame(hist)
        aluna_sel = st.selectbox("Selecione a Aluna para Auditoria:", sorted(df["Aluna"].unique()))
        df_alu = df[df["Aluna"] == aluna_sel].sort_values("Data", ascending=False)
        
        # --- SEPARAÇÃO POR ÁREAS (Dificuldades Congeladas) ---
        todas_difs = [d for lista in df_alu["Dificuldades"] for d in lista]
        
        st.subheader(f"📈 Evolução de {aluna_sel}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.error("🧘 **POSTURA**")
            p = [d for d in set(todas_difs) if any(x in d.lower() for x in ["postura", "punho", "falange", "unha", "banqueta", "teclas", "dedos"])]
            for i in p: st.write(f"- {i}")
            
            st.warning("🎹 **TÉCNICA**")
            t = [d for d in set(todas_difs) if any(x in d.lower() for x in ["articulação", "respiração", "dedilhado", "apoio", "clave"])]
            for i in t: st.write(f"- {i}")
            
        with c2:
            st.info("⏳ **RITMO**")
            r = [d for d in set(todas_difs) if any(x in d.lower() for x in ["metrônomo", "ritmica", "métrica", "figuras"])]
            for i in r: st.write(f"- {i}")
            
            st.success("📖 **TEORIA**")
            te = [d for d in set(todas_difs) if any(x in d.lower() for x in ["vídeos", "apostila", "atividades", "estudou"])]
            for i in te: st.write(f"- {i}")
            
        st.divider()
        
        # --- BANCA E METAS ---
        col_meta, col_banca = st.columns(2)
        with col_meta:
            st.subheader("🎯 Próxima Aula")
            st.info(df_alu["Metas"].iloc[0] if "Metas" in df_alu else "Sem metas definidas.")
        with col_banca:
            st.subheader("🏛️ Foco para a Banca")
            st.warning(df_alu["Dica_Banca"].iloc[0] if "Dica_Banca" in df_alu else "Sem dicas registradas.")
            
        st.subheader("📋 Histórico de Observações (Congelado)")
        st.write(df_alu[["Data", "Instrutora", "Obs"]])
    else:
        st.info("Aguardando os primeiros registros para gerar análise.")
