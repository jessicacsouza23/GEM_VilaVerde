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

# --- FUNÇÕES DE BANCO ---
def db_get_calendario(data_id):
    try:
        res = supabase.table("calendario").select("*").eq("id", data_id).execute()
        return res.data[0]['escala'] if res.data else None
    except: return None

def db_get_historico():
    try:
        res = supabase.table("historico_pedagogico").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão Pedagógica 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico & Banca"])

if not supabase:
    st.error("⚠️ Configure os Secrets no Streamlit.")
    st.stop()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    st.header("🗓️ Painel da Secretaria")
    tab1, tab2 = st.tabs(["📅 Gestão de Sábado", "📋 Resumo de Aulas"])
    
    with tab1:
        data_sel = st.date_input("Data do Sábado:", value=datetime.now())
        d_str = data_sel.strftime("%d/%m/%Y")
        escala = db_get_calendario(d_str)
        
        if escala:
            st.success(f"Rodízio ativo para {d_str}")
            st.table(pd.DataFrame(escala))
            if st.button("🗑️ Resetar Rodízio"):
                supabase.table("calendario").delete().eq("id", d_str).execute()
                st.rerun()
        else:
            if st.button("🚀 Gerar Rodízio de Alunas"):
                nova_escala = []
                for t, alunas in TURMAS.items():
                    for a in alunas:
                        nova_escala.append({
                            "Aluna": a, "Turma": t,
                            HORARIOS[0]: "Igreja", HORARIOS[1]: "Prática",
                            HORARIOS[2]: "Teoria", HORARIOS[3]: "Solfejo"
                        })
                supabase.table("calendario").upsert({"id": d_str, "escala": nova_escala}).execute()
                st.rerun()

    with tab2:
        hist = db_get_historico()
        if hist:
            st.dataframe(pd.DataFrame(hist)[["data", "aluna", "professora", "presenca", "meta"]])

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe e Avaliação")
    prof_sel = st.selectbox("👤 Identifique-se:", ["Selecione..."] + PROFESSORAS)
    data_p = st.date_input("📅 Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")
    
    escala_dia = db_get_calendario(d_str)

    if escala_dia and prof_sel != "Selecione...":
        aluna_sel = st.selectbox("🎯 Aluna em Atendimento:", sorted([a['Aluna'] for a in escala_dia]))
        
        with st.form("form_completo"):
            # --- CHAMADA E PRESENÇA ---
            st.subheader("🚩 Chamada e Atividade")
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                presenca = st.radio("Presença:", ["Presente", "Faltou", "Atraso Justificado"], horizontal=True)
            with col_ch2:
                atividade_tipo = st.selectbox("Modalidade da Aula:", ["Prática Instrumental", "Teoria Musical", "Solfejo/Hinos"])

            st.divider()

            # --- FORMULÁRIOS DINÂMICOS CONFORME A MODALIDADE ---
            if atividade_tipo == "Prática Instrumental":
                st.markdown("#### **🎹 Avaliação Técnica (Prática)**")
                c1, c2 = st.columns(2)
                with c1:
                    p_check = st.multiselect("🪑 Postura:", ["Coluna", "Mãos/Punhos", "Pés/Pedaleira"])
                    t_check = st.multiselect("🎹 Técnica:", ["Dedilhado", "Articulação", "Legato", "Substituição"])
                with c2:
                    r_check = st.multiselect("⏱️ Ritmo:", ["Metrônomo", "Divisão Rítmica", "Pausas"])
                    relato_pratica = st.text_input("Lição/Hino trabalhado:")

            elif atividade_tipo == "Teoria Musical":
                st.markdown("#### **📖 Registro de Teoria**")
                c1, c2 = st.columns(2)
                with c1:
                    correcao = st.radio("Correção da Lição de Casa:", ["Tudo Certo", "Incompleto", "Não Fez", "Não trouxe o método"])
                    materia = st.text_input("Matéria dada hoje (Ex: Tonalidades):")
                with c2:
                    teo_dificuldade = st.multiselect("Dificuldades na Teoria:", ["Leitura de Notas", "Valores/Figuras", "Fórmulas Compasso"])

            else: # Solfejo/Hinos
                st.markdown("#### **🎶 Registro de Solfejo**")
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    solfejo_hinos = st.text_area("Hinos solfejados:")
                with col_s2:
                    s_check = st.multiselect("Dificuldades no Solfejo:", ["Marcação de Compasso", "Entonação", "Ritmo Linear"])

            st.divider()

            # --- BANCA SEMESTRAL E METAS (CONGELAMENTO) ---
            st.markdown("#### **🎓 Preparação para Banca**")
            banca = st.select_slider("Prontidão:", ["Iniciante", "Regular", "Bom", "Apta"])
            meta = st.text_input("🎯 Meta para a próxima aula:")
            observacoes = st.text_area("📝 Relato Pedagógico (Histórico Permanente):")

            if st.form_submit_button("💾 CONGELAR ANÁLISE E CHAMADA"):
                # Agrupa os dados dinâmicos para salvar no banco
                dados_aula = {
                    "data": d_str, "aluna": aluna_sel, "professora": prof_sel,
                    "presenca": presenca, "tipo": atividade_tipo,
                    "banca": banca, "meta": meta, "relato": observacoes,
                    "postura": str(p_check) if atividade_tipo == "Prática Instrumental" else "",
                    "tecnica": str(t_check) if atividade_tipo == "Prática Instrumental" else "",
                    "ritmo": str(r_check) if atividade_tipo == "Prática Instrumental" else "",
                    "teoria": materia if atividade_tipo == "Teoria Musical" else ""
                }
                supabase.table("historico_pedagogico").insert(dados_aula).execute()
                st.balloons()
                st.success("Ficha salva com sucesso!")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico & Banca":
    st.header("📊 Evolução Técnica")
    hist = db_get_historico()
    if hist:
        df = pd.DataFrame(hist)
        aluna_h = st.selectbox("Selecione a Aluna:", sorted(df["aluna"].unique()))
        df_f = df[df["aluna"] == aluna_h].sort_values(by="created_at", ascending=False)
        
        for _, row in df_f.iterrows():
            with st.expander(f"📅 {row['data']} - {row['tipo']} ({row['professora']})"):
                st.write(f"**📍 Presença:** {row['presenca']}")
                st.write(f"**🎯 Próxima Meta:** {row['meta']}")
                st.info(f"**Relato:** {row['relato']}")
