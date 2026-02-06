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
        st.error("⚠️ Erro: Configure SUPABASE_URL e SUPABASE_KEY nos Secrets do Streamlit.")
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
                st.subheader("📋 Resumo Geral de Aulas (Secretaria)")
                # Exibe o resumo básico para a secretaria
                st.dataframe(df_sec[["data", "aluna", "professora", "banca", "meta"]], use_container_width=True)
                
                st.download_button(
                    label="📥 Baixar Relatório Completo (CSV)",
                    data=df_sec.to_csv(index=False).encode('utf-8'),
                    file_name=f"GEM_VilaVerde_Relatorio_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Nenhuma aula registrada até o momento.")
        except:
            st.warning("Aguardando criação da tabela no Supabase.")
    
# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Ficha Pedagógica Detalhada")
    
    with st.form("ficha_pedagogica"):
        col_id1, col_id2 = st.columns(2)
        with col_id1:
            prof_sel = st.selectbox("👤 Professora:", ["Selecione seu nome..."] + PROFESSORAS)
        with col_id2:
            aluna_sel = st.selectbox("🎯 Aluna:", sorted([a for t in TURMAS.values() for a in t]))
        
        data_aula = st.date_input("📅 Data da Aula:", value=datetime.now())
        
        st.divider()
        
        # --- SELEÇÃO DE DIFICULDADES (O QUE VOCÊ ACHOU LEGAL!) ---
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### **🪑 Postura**")
            p_check = st.multiselect("Dificuldades Observadas (Postura):", 
                                     ["Coluna Curvada", "Ombros Tensos", "Altura do Banco", "Punho Baixo", "Dedo Esticado", "Pés Fora do Lugar"])
            
            st.markdown("### **🎹 Técnica**")
            t_check = st.multiselect("Dificuldades Observadas (Técnica):", 
                                     ["Dedilhado Incorreto", "Articulação (Pobre)", "Falta de Legato", "Substituição", "Falta de Dinâmica", "Independência de Mãos"])
            
        with col2:
            st.markdown("### **⏱️ Ritmo**")
            r_check = st.multiselect("Dificuldades Observadas (Ritmo):", 
                                     ["Falta Metrônomo", "Acelera/Atrasa", "Divisão de Figuras", "Respeito às Pausas", "Estabilidade"])
            
            st.markdown("### **📖 Teoria**")
            teo_check = st.multiselect("Dificuldades Observadas (Teoria):", 
                                       ["Leitura de Notas", "Fórmulas de Compasso", "Armaduras/Tonalidade", "Terminologia Musical", "Tarefa Não Feita"])

        st.divider()
        
        # --- BANCA E METAS ---
        st.markdown("### **🎓 Preparação para Banca Semestral**")
        banca_status = st.select_slider("Status de Prontidão:", 
                                        options=["Início do Método", "Desenvolvendo", "Bom Progresso", "Apta para Pré-Exame", "PRONTA (EXCELENTE)"])
        
        meta_prox = st.text_input("🎯 Meta específica para a próxima aula (Dica para Aluna):")
        relato_detalhado = st.text_area("📝 Relato Pedagógico (Análise para o histórico):")

        if st.form_submit_button("💾 CONGELAR ANÁLISE COMPLETA"):
            if prof_sel != "Selecione seu nome..." and supabase:
                # Monta os dados para salvar
                dados = {
                    "data": data_aula.strftime("%d/%m/%Y"),
                    "aluna": aluna_sel,
                    "professora": prof_sel,
                    "postura": ", ".join(p_check) if p_check else "OK",
                    "tecnica": ", ".join(t_check) if t_check else "OK",
                    "ritmo": ", ".join(r_check) if r_check else "OK",
                    "teoria": ", ".join(teo_check) if teo_check else "OK",
                    "banca": banca_status,
                    "meta": meta_prox,
                    "relato": relato_detalhado
                }
                # Insere no Supabase
                supabase.table("historico_pedagogico").insert(dados).execute()
                st.balloons()
                st.success(f"Análise de {aluna_sel} foi congelada no histórico!")
            else:
                st.error("Por favor, selecione seu nome e verifique a conexão com o banco.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico & Banca":
    st.header("📊 Evolução Técnica e Preparação")
    
    if supabase:
        try:
            res = supabase.table("historico_pedagogico").select("*").execute()
            df_total = pd.DataFrame(res.data)
            
            if not df_total.empty:
                aluna_h = st.selectbox("Selecione a Aluna para ver o Histórico:", sorted(df_total["aluna"].unique()))
                df_aluna = df_total[df_total["aluna"] == aluna_h].sort_values(by="created_at", ascending=False)
                
                # Resumo visual do progresso
                st.write(f"### Histórico de {aluna_h}")
                
                for _, row in df_aluna.iterrows():
                    with st.expander(f"📅 Aula de {row['data']} - Profª {row['professora']}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**🎯 Meta definida:** {row['meta']}")
                            st.write(f"**🏆 Status Banca:** {row['banca']}")
                        with col_b:
                            st.write(f"**📝 Relato:** {row['relato']}")
                        
                        st.divider()
                        # Mostra as dificuldades separadas por áreas
                        st.write("**Dificuldades registradas nesta aula:**")
                        c_p, c_t, c_r, c_te = st.columns(4)
                        c_p.write(f"🪑 **Postura:** {row['postura']}")
                        c_t.write(f"🎹 **Técnica:** {row['tecnica']}")
                        c_r.write(f"⏱️ **Ritmo:** {row['ritmo']}")
                        c_te.write(f"📖 **Teoria:** {row['teoria']}")
            else:
                st.info("Aguardando o primeiro registro para gerar o histórico.")
        except:
            st.error("Erro ao carregar dados do banco.")
