import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM SUPABASE ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = init_supabase()

# --- DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
PROFESSORAS = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 (Igreja)", "09h35 (2ª Aula)", "10h10 (3ª Aula)", "10h45 (4ª Aula)"]

# --- FUNÇÕES DE PERSISTÊNCIA ---
def buscar_calendario(data_str):
    try:
        res = supabase.table("calendario").select("*").eq("id", data_str).execute()
        return res.data[0]['escala'] if res.data else None
    except: return None

def buscar_historico():
    try:
        res = supabase.table("historico_pedagogico").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão Pedagógica 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico & Banca"])

if not supabase:
    st.error("⚠️ Erro de Conexão. Verifique os Secrets.")
    st.stop()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    st.header("🗓️ Painel da Secretaria")
    t_rod, t_his = st.tabs(["Gerar Rodízio", "Histórico Geral"])
    
    with t_rod:
        data_sel = st.date_input("Data do Sábado:", value=datetime.now())
        d_str = data_sel.strftime("%d/%m/%Y")
        escala = buscar_calendario(d_str)
        
        if escala:
            st.success(f"Rodízio ativo para {d_str}")
            st.table(pd.DataFrame(escala))
            if st.button("🗑️ Resetar Rodízio"):
                supabase.table("calendario").delete().eq("id", d_str).execute()
                st.rerun()
        else:
            if st.button("🚀 Gerar Rodízio"):
                nova_escala = []
                for t, alunas in TURMAS.items():
                    for a in alunas:
                        nova_escala.append({"Aluna": a, "Turma": t, HORARIOS[0]: "Igreja", HORARIOS[1]: "Prática", HORARIOS[2]: "Teoria", HORARIOS[3]: "Solfejo"})
                supabase.table("calendario").insert({"id": d_str, "escala": nova_escala}).execute()
                st.rerun()

    with t_his:
        hist = buscar_historico()
        if hist: st.dataframe(pd.DataFrame(hist))

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Ficha de Aula")
    prof_sel = st.selectbox("👤 Professora:", ["Selecione..."] + PROFESSORAS)
    data_p = st.date_input("📅 Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")
    
    escala_dia = buscar_calendario(d_str)

    if escala_dia and prof_sel != "Selecione...":
        aluna_sel = st.selectbox("🎯 Aluna em Aula:", sorted([a['Aluna'] for a in escala_dia]))
        
        with st.form("ficha"):
            st.markdown(f"### Avaliação: {aluna_sel}")
            c1, c2 = st.columns(2)
            with c1:
                p_check = st.multiselect("🪑 Postura:", ["Coluna", "Punho", "Pés"])
                t_check = st.multiselect("🎹 Técnica:", ["Dedilhado", "Articulação", "Legato"])
            with c2:
                r_check = st.multiselect("⏱️ Ritmo:", ["Metrônomo", "Divisão", "Pausas"])
                teo_check = st.multiselect("📖 Teoria:", ["Leitura", "Tarefa", "Matéria Nova"])
            
            banca = st.select_slider("🎓 Status Banca:", ["Início", "Bom", "Apta"])
            meta = st.text_input("🎯 Próxima Meta:")
            relato = st.text_area("📝 Relato Completo:")
            
            if st.form_submit_button("💾 SALVAR"):
                supabase.table("historico_pedagogico").insert({
                    "data": d_str, "aluna": aluna_sel, "professora": prof_sel,
                    "postura": str(p_check), "tecnica": str(t_check),
                    "ritmo": str(r_check), "teoria": str(teo_check),
                    "banca": banca, "meta": meta, "relato": relato
                }).execute()
                st.success("Salvo!")
    else:
        st.warning("Peça para a secretaria gerar o rodízio do dia.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico & Banca":
    st.header("📊 Evolução")
    hist = buscar_historico()
    if hist:
        df = pd.DataFrame(hist)
        aluna = st.selectbox("Aluna:", sorted(df["aluna"].unique()))
        st.dataframe(df[df["aluna"] == aluna])
