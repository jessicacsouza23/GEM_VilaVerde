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
        st.error("⚠️ Configuração necessária: SUPABASE_URL e SUPABASE_KEY nos Secrets.")
        return None

supabase = init_supabase()

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
PROFESSORAS = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 (Igreja)", "09h35 (2ª Aula)", "10h10 (3ª Aula)", "10h45 (4ª Aula)"]

# --- FUNÇÕES DE PERSISTÊNCIA (SUPABASE) ---
def buscar_calendario(data_str):
    if supabase:
        res = supabase.table("calendario").select("*").eq("id", data_str).execute()
        return res.data[0]['escala'] if res.data else None
    return None

def buscar_historico():
    if supabase:
        res = supabase.table("historico_pedagogico").select("*").order("created_at", desc=True).execute()
        return res.data
    return []

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão Pedagógica 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico & Banca"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    st.header("🗓️ Painel da Secretaria")
    tab_rodizio, tab_resumo = st.tabs(["Gerar Rodízio", "Resumo de Aulas"])
    
    with tab_rodizio:
        data_sel = st.date_input("Data do Sábado:", value=datetime.now())
        d_str = data_sel.strftime("%d/%m/%Y")
        
        escala_atual = buscar_calendario(d_str)
        
        if escala_atual:
            st.success(f"Rodízio ativo para {d_str}")
            st.table(pd.DataFrame(escala_atual))
            if st.button("🗑️ Resetar este Sábado"):
                supabase.table("calendario").delete().eq("id", d_str).execute()
                st.rerun()
        else:
            if st.button("🚀 Gerar Rodízio para este Sábado"):
                nova_escala = []
                for t, alunas in TURMAS.items():
                    for a in alunas:
                        nova_escala.append({
                            "Aluna": a, "Turma": t, 
                            HORARIOS[0]: "Igreja", HORARIOS[1]: "Prática", 
                            HORARIOS[2]: "Teoria", HORARIOS[3]: "Solfejo"
                        })
                supabase.table("calendario").insert({"id": d_str, "escala": nova_escala}).execute()
                st.rerun()

    with tab_resumo:
        historico = buscar_historico()
        if historico:
            st.dataframe(pd.DataFrame(historico)[["data", "aluna", "professora", "banca", "meta"]])
        else:
            st.info("Nenhuma aula registrada ainda.")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Análise Pedagógica")
    instr_sel = st.selectbox("👤 Professora:", ["Selecione..."] + PROFESSORAS)
    data_p = st.date_input("📅 Data da Aula:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    escala_dia = buscar_calendario(d_str)

    if escala_dia and instr_sel != "Selecione...":
        alunas_dia = sorted([a['Aluna'] for a in escala_dia])
        aluna_sel = st.selectbox("🎯 Selecione a Aluna que está atendendo:", alunas_dia)
        
        # Busca qual o horário/atividade dessa aluna para informar a professora
        info_aluna = next(item for item in escala_dia if item["Aluna"] == aluna_sel)
        st.info(f"📍 Turma: {info_aluna['Turma']} | Horários gerados no rodízio.")

        with st.form("form_analise_detalhada"):
            st.subheader(f"Avaliação de {aluna_sel}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### **🪑 Postura**")
                p_check = st.multiselect("Dificuldades (Postura):", ["Coluna/Ombros", "Punhos/Braços", "Pés/Pedaleira"])
                
                st.markdown("#### **🎹 Técnica**")
                t_check = st.multiselect("Dificuldades (Técnica):", ["Dedilhado", "Articulação", "Independência de Mãos"])

            with c2:
                st.markdown("#### **⏱️ Ritmo**")
                r_check = st.multiselect("Dificuldades (Ritmo):", ["Metrônomo", "Divisão", "Respeito às Pausas"])
                
                st.markdown("#### **📖 Teoria**")
                teo_check = st.multiselect("Dificuldades (Teoria):", ["Leitura de Notas", "Tarefa de Casa", "Teoria Aplicada"])

            st.divider()
            st.markdown("#### **🎓 Preparação para Banca Semestral**")
            status_banca = st.select_slider("Nível de prontidão:", options=["Iniciante", "Evoluindo", "Consolidando", "Apta para Banca"])
            meta_proxima = st.text_input("🎯 Meta para a próxima aula / Dica específica:")
            relato_ia = st.text_area("📝 Relato detalhado da evolução:")

            if st.form_submit_button("💾 CONGELAR ANÁLISE"):
                dados_congelados = {
                    "data": d_str, "aluna": aluna_sel, "professora": instr_sel,
                    "postura": ", ".join(p_check), "tecnica": ", ".join(t_check),
                    "ritmo": ", ".join(r_check), "teoria": ", ".join(teo_check),
                    "banca": status_banca, "meta": meta_proxima, "relato": relato_ia
                }
                supabase.table("historico_pedagogico").insert(dados_congelados).execute()
                st.balloons()
                st.success(f"Análise de {aluna_sel} salva com sucesso!")
    else:
        st.warning("Selecione seu nome e verifique se a secretaria já gerou o rodízio para hoje.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico & Banca":
    st.header("📊 Histórico Pedagógico")
    historico = buscar_historico()
    if historico:
        df = pd.DataFrame(historico)
        aluna_h = st.selectbox("Escolha a Aluna:", sorted(df["aluna"].unique()))
        df_f = df[df["aluna"] == aluna_h]
        
        for _, row in df_f.iterrows():
            with st.expander(f"📅 Aula de {row['data']} - Profª {row['professora']}"):
                st.write(f"**🎓 Status Banca:** {row['banca']}")
                st.write(f"**🎯 Meta:** {row['meta']}")
                st.info(f"**Relato:** {row['relato']}")
