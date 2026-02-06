import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (FIRESTORE) ---
def init_connection():
    try:
        # Puxa a chave e garante que as quebras de linha sejam interpretadas corretamente
        pk = st.secrets["private_key"].replace("\\n", "\n").strip()
        
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": pk,
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
        st.error(f"⚠️ Erro de Conexão: Verifique os Secrets. Detalhe: {e}")
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

# --- LISTAS E BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
PROFESSORAS = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 às 09h30", "09h35 às 10h05", "10h10 às 10h40", "10h45 às 11h15"]

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

# --- MENU ---
st.sidebar.title("🎹 GEM Vila Verde 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# --- MODULO SECRETARIA ---
if perfil == "🏠 Secretaria":
    st.header("🏠 Gestão da Secretaria")
    tab1, tab2 = st.tabs(["🗓️ Rodízio", "📋 Resumo de Aulas"])
    
    with tab2:
        st.subheader("📋 Resumo Geral (Consultivo)")
        registros = db_get_all("historico_geral")
        if registros:
            df_sec = pd.DataFrame(registros)
            st.dataframe(df_sec[["Data", "Aluna", "Materia", "Instrutora", "Horario"]].sort_values("Data", ascending=False))

# --- MODULO PROFESSORA ---
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe Pedagógico")
    
    with st.expander("📝 Lançar Nova Aula", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            instr = st.selectbox("Instrutora:", PROFESSORAS)
            aluna = st.selectbox("Aluna:", sorted([a for t in TURMAS.values() for a in t]))
        with col2:
            horario = st.selectbox("Horário:", HORARIOS)
            mat = st.selectbox("Matéria:", ["Prática", "Teoria", "Solfejo"])

        st.divider()
        st.subheader("⚠️ Dificuldades Técnicas")
        difs_selecionadas = st.multiselect("Selecione as dificuldades observadas:", DIFICULDADES_PRATICA)
        
        st.divider()
        st.subheader("🎯 Planejamento e Banca")
        obs_geral = st.text_area("Relato Pedagógico (O que foi visto):")
        meta_aula = st.text_area("Metas para a Próxima Aula:")
        foco_banca = st.text_area("Dicas Específicas para a Banca Semestral:")

        if st.button("💾 SALVAR E CONGELAR ANÁLISE"):
            doc_id = f"{aluna}_{datetime.now().timestamp()}".replace(".","")
            dados = {
                "Data": datetime.now().strftime("%d/%m/%Y"),
                "Aluna": aluna,
                "Materia": mat,
                "Dificuldades": difs_selecionadas,
                "Relato": obs_geral,
                "Meta": meta_aula,
                "Banca": foco_banca,
                "Instrutora": instr,
                "Horario": horario
            }
            if db_save("historico_geral", doc_id, dados):
                st.success(f"✅ Registro de {aluna} congelado com sucesso!")

# --- MODULO ANALÍTICO (ANÁLISE POR ÁREAS) ---
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise Pedagógica para Banca")
    hist = db_get_all("historico_geral")
    
    if hist:
        df = pd.DataFrame(hist)
        aluna_sel = st.selectbox("Selecione a Aluna:", sorted(df["Aluna"].unique()))
        df_alu = df[df["Aluna"] == aluna_sel].sort_values("Data", ascending=False)
        
        # --- SEPARAÇÃO POR ÁREAS ---
        todas_difs = [d for lista in df_alu["Dificuldades"] for d in lista]
        
        st.subheader(f"📈 Evolução de {aluna_sel}")
        col_p, col_t = st.columns(2)
        
        with col_p:
            st.error("🧘 **POSTURA**")
            p = [d for d in set(todas_difs) if any(x in d.lower() for x in ["postura", "punho", "falange", "unha", "banqueta", "tecla", "dedo"])]
            for i in p: st.write(f"- {i}")
            
            st.warning("🎹 **TÉCNICA**")
            t = [d for d in set(todas_difs) if any(x in d.lower() for x in ["articulação", "respiração", "dedilhado", "apoio", "clave"])]
            for i in t: st.write(f"- {i}")

        with col_t:
            st.info("⏳ **RITMO**")
            r = [d for d in set(todas_difs) if any(x in d.lower() for x in ["metrônomo", "ritmica", "figura"])]
            for i in r: st.write(f"- {i}")
            
            st.success("📖 **TEORIA**")
            te = [d for d in set(todas_difs) if any(x in d.lower() for x in ["vídeo", "apostila", "atividade", "estudou"])]
            for i in te: st.write(f"- {i}")

        st.divider()
        st.subheader("🎯 Foco Estratégico")
        st.write(f"**Próxima Aula:** {df_alu['Meta'].iloc[0]}")
        st.warning(f"**Dica para a Banca:** {df_alu['Banca'].iloc[0]}")
        
        st.divider()
        st.subheader("📜 Histórico de Relatos (Congelado)")
        st.dataframe(df_alu[["Data", "Instrutora", "Relato"]])
    else:
        st.info("Aguardando registros para análise.")
