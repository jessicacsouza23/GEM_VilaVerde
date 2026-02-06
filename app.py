import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS ---
def init_connection():
    try:
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
        st.error(f"⚠️ Erro de Conexão: {e}")
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

# --- LISTAS MESTRE (RESTAURADAS) ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 às 09h30", "09h35 às 10h05", "10h10 às 10h40", "10h45 às 11h15"]

# Dificuldades mapeadas para separação por áreas
DIFICULDADES = [
    "Dificuldade com a postura (costas, ombros e braços)", "Está deixando o punho alto ou baixo", 
    "Está quebrando as falanges", "Está adentrando às teclas", "Não senta no centro da banqueta",
    "Dificuldade em deixar os dedos arredondados", "Unhas muito compridas",
    "Dificuldade ritmica", "Dificuldade com o uso do metrônomo", "Estuda sem o metrônomo",
    "Dificuldade em distinguir os nomes das figuras ritmicas", "Dificuldade em leitura métrica",
    "Dificuldade em fazer a articulação ligada e semiligada", "Dificuldade com as respirações",
    "Dificuldade com as respirações sobre passagem", "Dificuldades em recurso de dedilhado",
    "Dificuldade em fazer nota de apoio", "Esquece de colocar o pé direito no pedal de expressão",
    "Dificuldades em ler as notas na clave de sol", "Dificuldades em ler as notas na clave de fá",
    "Não realizou as atividades da apostila", "Não estudou nada", "Não apresentou dificuldades"
]

# --- INTERFACE ---
st.sidebar.title("🎼 GEM Vila Verde 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ================= MÓDULO SECRETARIA =================
if perfil == "🏠 Secretaria":
    st.header("🏠 Gestão e Resumo da Secretaria")
    tab_r, tab_h = st.tabs(["🗓️ Rodízio Semanal", "📋 Histórico de Aulas"])
    
    with tab_r:
        data_r = st.date_input("Data do Rodízio:", value=datetime.now())
        if st.button("🚀 Gerar Rodízio Inicial"):
            escala = []
            for t, alunas in TURMAS.items():
                for a in alunas:
                    escala.append({"Aluna": a, "Turma": t, "Status": "Pendente"})
            db_save("rodizios", data_r.strftime("%d_%m_%Y"), {"dados": escala})
            st.success("Base de rodízio criada!")

    with tab_h:
        st.subheader("📋 Resumo da Secretaria (Consulta)")
        aulas = db_get_all("historico_geral")
        if aulas:
            df_sec = pd.DataFrame(aulas)
            st.dataframe(df_sec[["Data", "Aluna", "Materia", "Instrutora", "Horario"]].sort_values("Data", ascending=False))

# ================= MÓDULO PROFESSORA =================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe Pedagógico")
    
    with st.expander("📝 Registrar Nova Aula", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            instr_sel = st.selectbox("Instrutora:", PROFESSORAS)
            aluna_n = st.selectbox("Aluna:", sorted([a for t in TURMAS.values() for a in t]))
        with c2:
            h_sel = st.selectbox("Horário:", HORARIOS)
            mat_sel = st.selectbox("Matéria:", ["Prática", "Teoria", "Solfejo"])

        st.divider()
        st.subheader("⚠️ Dificuldades Técnicas")
        difs_sel = st.multiselect("Marque as dificuldades observadas:", DIFICULDADES)
        
        st.divider()
        st.subheader("🎯 Planejamento (Congelado para Consulta)")
        relato = st.text_area("Análise Pedagógica Detalhada (Histórico):")
        meta_prox = st.text_area("Metas para a Próxima Aula:")
        dica_banca = st.text_area("Dicas Específicas para a Banca Semestral:")

        if st.button("💾 SALVAR E CONGELAR REGISTRO"):
            doc_id = f"{aluna_n}_{datetime.now().timestamp()}".replace(".","")
            dados_aula = {
                "Data": datetime.now().strftime("%d/%m/%Y"), "Aluna": aluna_n, "Materia": mat_sel,
                "Dificuldades": difs_sel, "Obs": relato, "Metas": meta_prox,
                "Banca": dica_banca, "Instrutora": instr_sel, "Horario": h_sel
            }
            if db_save("historico_geral", doc_id, dados_aula):
                st.success(f"✅ Análise de {aluna_n} salva com sucesso!")

# ================= MÓDULO ANALÍTICO (O MAIS IMPORTANTE) =================
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise Pedagógica para Banca")
    hist = db_get_all("historico_geral")
    
    if hist:
        df = pd.DataFrame(hist)
        aluna_sel = st.selectbox("Selecionar Aluna para Auditoria:", sorted(df["Aluna"].unique()))
        df_alu = df[df["Aluna"] == aluna_sel].sort_values("Data", ascending=False)
        
        # --- LÓGICA DE SEPARAÇÃO POR ÁREAS ---
        difs_list = [d for lista in df_alu["Dificuldades"] for d in lista]
        
        st.subheader(f"📈 Diagnóstico Pedagógico: {aluna_sel}")
        col1, col2 = st.columns(2)
        
        with col1:
            st.error("🧘 **POSTURA**")
            postura = [d for d in set(difs_list) if any(x in d.lower() for x in ["postura", "punho", "falange", "unha", "banqueta", "teclas", "dedo"])]
            for i in postura: st.write(f"- {i}")
            
            st.warning("🎹 **TÉCNICA**")
            tecnica = [d for d in set(difs_list) if any(x in d.lower() for x in ["articulação", "respiração", "dedilhado", "apoio", "clave"])]
            for i in tecnica: st.write(f"- {i}")

        with col2:
            st.info("⏳ **RITMO**")
            ritmo = [d for d in set(difs_list) if any(x in d.lower() for x in ["metrônomo", "ritmica", "métrica", "figuras"])]
            for i in ritmo: st.write(f"- {i}")
            
            st.success("📖 **TEORIA**")
            teoria = [d for d in set(difs_list) if any(x in d.lower() for x in ["vídeos", "apostila", "atividades", "estudou"])]
            for i in teoria: st.write(f"- {i}")

        st.divider()
        st.subheader("🏛️ Foco para a Banca Semestral")
        c_m, c_b = st.columns(2)
        with c_m:
            st.markdown(f"**🎯 Metas Próxima Aula:**\n\n{df_alu['Metas'].iloc[0]}")
        with c_b:
            st.markdown(f"**💡 Dicas para a Banca:**\n\n{df_alu['Banca'].iloc[0]}")
            
        st.subheader("📜 Histórico de Relatos (Congelado)")
        st.table(df_alu[["Data", "Instrutora", "Obs"]])
    else:
        st.info("Nenhum registro encontrado.")
