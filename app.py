import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (FIRESTORE) BLINDADA ---
def init_connection():
    try:
        # Puxa os segredos do Streamlit
        key_data = st.secrets["private_key"].replace("\\n", "\n").strip()
        
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": key_data,
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
        st.error(f"⚠️ Erro de Conexão: Verifique os Secrets. {e}")
        return None

db = init_connection()

# --- FUNÇÕES DE BANCO ---
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

# --- BANCO DE DADOS MESTRE (LISTAS ORIGINAIS RESTAURADAS) ---
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
st.sidebar.title("🎹 GEM Vila Verde 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ================= MÓDULO SECRETARIA =================
if perfil == "🏠 Secretaria":
    st.header("🏠 Gestão da Secretaria")
    tab1, tab2 = st.tabs(["🗓️ Rodízio Semanal", "📋 Resumo da Secretaria"])
    
    with tab1:
        data_r = st.date_input("Data do Rodízio:", value=datetime.now())
        if st.button("🚀 Inicializar Rodízio no Firestore"):
            escala = []
            for t, alunas in TURMAS.items():
                for a in alunas:
                    escala.append({"Aluna": a, "Turma": t, HORARIOS_LABELS[1]: "🎹 Prática", HORARIOS_LABELS[2]: "📚 Teoria"})
            db_save("rodizios", data_r.strftime("%d_%m_%Y"), {"id": data_r.strftime("%d/%m/%Y"), "dados": escala})
            st.success("Base de dados criada para este sábado!")

# ================= MÓDULO PROFESSORA =================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Registro Pedagógico Detalhado")
    instr_sel = st.selectbox("Professora:", PROFESSORAS_LISTA)
    data_aula = st.date_input("Data da Aula:")
    d_str = data_aula.strftime("%d/%m/%Y")
    
    col_h, col_m = st.columns(2)
    with col_h:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS)
    with col_m:
        mat = st.selectbox("📚 Matéria:", ["Prática", "Teoria", "Solfejo"])
        aluna_n = st.selectbox("👤 Aluna:", sorted([a for t in TURMAS.values() for a in t]))

    st.divider()
    st.subheader("⚠️ Dificuldades Observadas")
    lista_dif = DIFICULDADES_PRATICA if mat == "Prática" else DIFICULDADES_TEORIA
    selecionadas = []
    
    c1, c2 = st.columns(2)
    for i, d in enumerate(lista_dif):
        if (c1 if i < len(lista_dif)/2 else c2).checkbox(d):
            selecionadas.append(d)
    
    obs = st.text_area("✍️ Relato Evolutivo para a Banca Semestral:")
    
    if st.button("💾 SALVAR REGISTRO COMPLETO"):
        doc_id = f"{aluna_n}_{datetime.now().timestamp()}".replace(".","")
        sucesso = db_save("historico_geral", doc_id, {
            "Data": d_str, "Aluna": aluna_n, "Materia": mat, 
            "Dificuldades": selecionadas, "Obs": obs, "Instrutora": instr_sel,
            "Horario": h_sel
        })
        if sucesso: st.success(f"✅ Aula de {aluna_n} registrada!")

# ================= MÓDULO ANALÍTICO IA =================
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise Pedagógica Completa")
    hist = db_get_all("historico_geral")
    
    if hist:
        df = pd.DataFrame(hist)
        aluna_sel = st.selectbox("Selecionar Aluna para Auditoria:", sorted(df["Aluna"].unique()))
        df_alu = df[df["Aluna"] == aluna_sel].sort_values("Data", ascending=False)
        
        # Separação por Áreas Pedagógicas (Meta Semestral)
        todas_difs = [d for lista in df_alu["Dificuldades"] for d in lista]
        
        col1, col2 = st.columns(2)
        with col1:
            st.error("🧘 **POSTURA**")
            p = [d for d in set(todas_difs) if any(x in d.lower() for x in ["postura", "punho", "falange", "unha", "banqueta", "teclas", "dedo"])]
            for i in p: st.write(f"- {i}")
            
            st.warning("🎹 **TÉCNICA**")
            t = [d for d in set(todas_difs) if any(x in d.lower() for x in ["articulação", "respiração", "dedilhado", "apoio", "clave"])]
            for i in t: st.write(f"- {i}")
            
        with col2:
            st.info("⏳ **RITMO**")
            r = [d for d in set(todas_difs) if any(x in d.lower() for x in ["metrônomo", "ritmica", "figuras"])]
            for i in r: st.write(f"- {i}")
            
            st.success("📖 **TEORIA**")
            te = [d for d in set(todas_difs) if any(x in d.lower() for x in ["vídeos", "apostila", "atividades", "estudou"])]
            for i in te: st.write(f"- {i}")
            
        st.divider()
        st.subheader("🎯 Metas para Próxima Aula e Banca")
        st.info(f"**Último feedback da professora:** {df_alu['Obs'].iloc[0] if not df_alu.empty else 'N/A'}")
    else:
        st.info("Aguardando registros para gerar análise.")
