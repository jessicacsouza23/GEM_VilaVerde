import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (BLINDADA CONTRA ERRO 65) ---
def init_connection():
    try:
        # O segredo: replace e strip garantem que a chave tenha múltiplos de 4
        pk = st.secrets["private_key"].replace("\\n", "\n").replace("\n", "\n").strip()
        
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

# --- LISTAS MESTRE (RESTAURADAS 100%) ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
SECRETARIAS = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"]
HORARIOS = ["08h45 às 09h30 (1ª Aula)", "09h35 às 10h05 (2ª Aula)", "10h10 às 10h40 (3ª Aula)", "10h45 às 11h15 (4ª Aula)"]

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

# --- MENU LATERAL ---
st.sidebar.title("🎼 GEM Vila Verde")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ================= MÓDULO SECRETARIA =================
if perfil == "🏠 Secretaria":
    st.header("🏠 Gestão da Secretaria")
    tab_r, tab_s = st.tabs(["🗓️ Rodízio Semanal", "📋 Resumo da Secretaria"])
    
    with tab_r:
        data_sel = st.date_input("Data:", value=datetime.now())
        if st.button("🚀 Criar Base de Rodízio"):
            escala = []
            for t, alunas in TURMAS.items():
                for a in alunas:
                    escala.append({"Aluna": a, "Turma": t, "Status": "Pendente"})
            db_save("rodizios", data_sel.strftime("%d_%m_%Y"), {"dados": escala})
            st.success("Rodízio inicializado!")

    with tab_s:
        st.subheader("📋 Resumo Geral de Aulas")
        historico = db_get_all("historico_geral")
        if historico:
            df_sec = pd.DataFrame(historico)
            st.dataframe(df_sec[["Data", "Aluna", "Materia", "Instrutora", "Horario"]])

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
            mat = st.selectbox("Matéria:", ["Prática", "Teoria", "Solfejo"])

        st.divider()
        st.subheader("⚠️ Dificuldades Técnicas")
        lista_dif = DIFICULDADES_PRATICA if mat == "Prática" else DIFICULDADES_TEORIA
        selecionadas = st.multiselect("Marque as dificuldades observadas:", lista_dif)
        
        st.divider()
        st.subheader("🎯 Análise e Metas (Congelado)")
        obs_ped = st.text_area("Análise Pedagógica Completa (Histórico):")
        metas_prox = st.text_area("Metas para a Próxima Aula:")
        dicas_banca = st.text_area("Dicas Específicas para a Banca Semestral:")

        if st.button("💾 SALVAR E CONGELAR ANÁLISE"):
            doc_id = f"{aluna_n}_{datetime.now().timestamp()}".replace(".","")
            dados_aula = {
                "Data": datetime.now().strftime("%d/%m/%Y"), "Aluna": aluna_n, "Materia": mat,
                "Dificuldades": selecionadas, "Obs": obs_ped, "Metas": metas_prox,
                "Banca": dicas_banca, "Instrutora": instr_sel, "Horario": h_sel
            }
            if db_save("historico_geral", doc_id, dados_aula):
                st.success(f"✅ Registro de {aluna_n} salvo com sucesso!")

# ================= MÓDULO ANALÍTICO IA =================
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise Pedagógica Completa")
    hist_raw = db_get_all("historico_geral")
    
    if hist_raw:
        df = pd.DataFrame(hist_raw)
        aluna_sel = st.selectbox("Selecionar Aluna para Auditoria:", sorted(df["Aluna"].unique()))
        df_alu = df[df["Aluna"] == aluna_sel].sort_values("Data", ascending=False)
        
        # --- SEPARAÇÃO POR ÁREAS (POSTURA, TÉCNICA, RITMO, TEORIA) ---
        difs_list = [d for lista in df_alu["Dificuldades"] for d in lista]
        
        st.subheader(f"📈 Diagnóstico Pedagógico: {aluna_sel}")
        col1, col2 = st.columns(2)
        
        with col1:
            st.error("🧘 **POSTURA**")
            p = [d for d in set(difs_list) if any(x in d.lower() for x in ["postura", "punho", "falange", "unha", "banqueta", "teclas", "dedo"])]
            for i in p: st.write(f"- {i}")
            
            st.warning("🎹 **TÉCNICA**")
            t = [d for d in set(difs_list) if any(x in d.lower() for x in ["articulação", "respiração", "dedilhado", "apoio", "clave"])]
            for i in t: st.write(f"- {i}")

        with col2:
            st.info("⏳ **RITMO**")
            r = [d for d in set(difs_list) if any(x in d.lower() for x in ["metrônomo", "ritmica", "métrica", "figuras"])]
            for i in r: st.write(f"- {i}")
            
            st.success("📖 **TEORIA**")
            te = [d for d in set(difs_list) if any(x in d.lower() for x in ["vídeos", "apostila", "atividades", "estudou"])]
            for i in te: st.write(f"- {i}")

        st.divider()
        st.subheader("🏛️ Preparação para a Banca Semestral")
        c_meta, c_banca = st.columns(2)
        with c_meta:
            st.markdown(f"**🎯 Próxima Aula:**\n{df_alu['Metas'].iloc[0]}")
        with c_banca:
            st.markdown(f"**💡 Dicas para a Banca:**\n{df_alu['Banca'].iloc[0]}")
            
        st.subheader("📜 Histórico de Observações (Congelado)")
        st.write(df_alu[["Data", "Instrutora", "Obs"]])
    else:
        st.info("Sem dados para análise no momento.")
