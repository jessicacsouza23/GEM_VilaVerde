import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (SUPABASE) ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        st.error("⚠️ Erro: Adicione SUPABASE_URL e SUPABASE_KEY nos Secrets do Streamlit.")
        return None

supabase = init_supabase()

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
PROFESSORAS = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Análise Pedagógica 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico & Banca"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    st.header("🗓️ Painel da Secretaria")
    
    if supabase:
        try:
            res = supabase.table("historico_pedagogico").select("*").order("created_at", desc=True).execute()
            df_sec = pd.DataFrame(res.data)
            
            if not df_sec.empty:
                st.subheader("📋 Resumo de Atividades Recentes")
                st.dataframe(df_sec[["data", "aluna", "professora", "banca", "meta"]], use_container_width=True)
            else:
                st.info("Nenhuma aula registrada até o momento.")
        except:
            st.warning("Tabela 'historico_pedagogico' não encontrada. Verifique o SQL Editor no Supabase.")
    
# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário Pedagógico de Aula")
    
    with st.form("ficha_pedagogica"):
        col_id1, col_id2 = st.columns(2)
        with col_id1:
            prof_sel = st.selectbox("👤 Professora:", ["Selecione seu nome..."] + PROFESSORAS)
        with col_id2:
            aluna_sel = st.selectbox("🎯 Aluna:", sorted([a for t in TURMAS.values() for a in t]))
        
        data_aula = st.date_input("📅 Data da Aula:", value=datetime.now())
        
        st.divider()
        
        # --- ANÁLISE POR ÁREAS (POSTURA, TÉCNICA, RITMO, TEORIA) ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### **🪑 Postura**")
            p_check = st.multiselect("Dificuldades Observadas:", ["Costas/Ombros", "Punhos/Braços", "Mão Arredondada", "Pés/Pedaleira"])
            
            st.markdown("### **🎹 Técnica**")
            t_check = st.multiselect("Dificuldades Observadas:", ["Dedilhado", "Articulação (Legato)", "Substituição", "Fraseado"])
            
        with c2:
            st.markdown("### **⏱️ Ritmo**")
            r_check = st.multiselect("Dificuldades Observadas:", ["Uso do Metrônomo", "Divisão Rítmica", "Pausas/Valores"])
            
            st.markdown("### **📖 Teoria**")
            teo_check = st.multiselect("Dificuldades Observadas:", ["Leitura Clave Sol/Fá", "Tonalidades", "Tarefa de Casa"])

        st.divider()
        st.markdown("### **🎓 Preparação para Banca Semestral**")
        banca_status = st.select_slider("Prontidão da Aluna:", ["Necessita Atenção", "Em Desenvolvimento", "Bom", "Apta para Exame"])
        meta_prox = st.text_input("🎯 Meta específica para a próxima aula:")
        relato_detalhado = st.text_area("📝 Relato Pedagógico (Análise Completa):")

        if st.form_submit_button("💾 CONGELAR ANÁLISE"):
            if prof_sel != "Selecione seu nome..." and supabase:
                dados = {
                    "data": data_aula.strftime("%d/%m/%Y"),
                    "aluna": aluna_sel,
                    "professora": prof_sel,
                    "postura": ", ".join(p_check),
                    "tecnica": ", ".join(t_check),
                    "ritmo": ", ".join(r_check),
                    "teoria": ", ".join(teo_check),
                    "banca": banca_status,
                    "meta": meta_prox,
                    "relato": relato_detalhado
                }
                supabase.table("historico_pedagogico").insert(dados).execute()
                st.balloons()
                st.success(f"Análise de {aluna_sel} salva com sucesso!")
            else:
                st.error("Verifique se seu nome foi selecionado e se o banco está conectado.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico & Banca":
    st.header("📊 Evolução Histórica")
    
    if supabase:
        try:
            res = supabase.table("historico_pedagogico").select("*").execute()
            df_total = pd.DataFrame(res.data)
            
            if not df_total.empty:
                aluna_h = st.selectbox("Selecione a Aluna para Ver o Histórico:", sorted(df_total["aluna"].unique()))
                df_aluna = df_total[df_total["aluna"] == aluna_h].sort_values(by="created_at", ascending=False)
                
                for _, row in df_aluna.iterrows():
                    with st.expander(f"📅 Aula de {row['data']} - Profª {row['professora']}"):
                        st.write(f"**🎯 Próxima Meta:** {row['meta']}")
                        st.write(f"**🏆 Status Banca:** {row['banca']}")
                        st.info(f"**Relato Detalhado:** {row['relato']}")
                        st.write(f"🚩 Dificuldades pontuadas: {row['postura']} | {row['tecnica']} | {row['ritmo']} | {row['teoria']}")
            else:
                st.info("Nenhum histórico encontrado para análise.")
        except:
            st.error("Erro ao carregar dados.")
