import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from supabase import create_client, Client

# --- 1. CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema Integrado", layout="wide", page_icon="🎼")

# --- 2. CONEXÃO COM SUPABASE ---
SUPABASE_URL = "https://ixaqtoyqoianumczsjai.supabase.co"
SUPABASE_KEY = "sb_publishable_HwYONu26I0AzTR96yoy-Zg_nVxTlJD1"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. DADOS MESTRE ---
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
# Cada professora é "dona" de uma sala para nunca haver repetição na prática
MAPA_SALAS_FIXAS = {prof: i + 1 for i, prof in enumerate(PROFESSORAS_LISTA)}

ALUNAS_LISTA = [
    "Amanda S.", "Ana Marcela S.", "Caroline C.", "Elisa F.", "Emilly O.", 
    "Gabrielly V.", "Heloísa R.", "Ingrid M.", "Júlia Cristina", "Júlia S.", 
    "Julya O.", "Mellina S.", "Micaelle S.", "Raquel L.", "Rebeca R.", 
    "Rebecca A.", "Rebeka S.", "Sarah S.", "Stephany O.", "Vitória A.", "Vitória Bella T."
]

TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

# --- 4. FUNÇÕES DE BANCO DE DADOS ---
def db_get_calendario():
    try:
        res = supabase.table("calendario").select("*").execute()
        return {item['id']: item['escala'] for item in res.data}
    except: return {}

def db_get_analises():
    try:
        res = supabase.table("analises_congeladas").select("*").execute()
        return {item['id']: item['dados'] for item in res.data}
    except: return {}

# --- 5. INTERFACE PRINCIPAL ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# --- MÓDULO SECRETARIA ---
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_analise = st.tabs(["🗓️ Planejamento", "📍 Chamada", "📝 Gerar Análise"])

    with tab_gerar:
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        sabados = [d for sem in calendar.Calendar().monthdatescalendar(2026, mes) for d in sem if d.weekday() == calendar.SATURDAY and d.month == mes]
        d_str = st.selectbox("Data do Rodízio:", [s.strftime("%d/%m/%Y") for s in sabados])
        idx_sab = sabados[[s.strftime("%d/%m/%Y") for s in sabados].index(d_str)].day

        cal_db = db_get_calendario()

        if d_str not in cal_db:
            st.info(f"Configurando Rodízio para {d_str}")
            col1, col2 = st.columns(2)
            with col1:
                pt2 = st.selectbox("Teoria H2 (T1):", PROFESSORAS_LISTA, index=0)
                pt3 = st.selectbox("Teoria H3 (T2):", PROFESSORAS_LISTA, index=1)
                pt4 = st.selectbox("Teoria H4 (T3):", PROFESSORAS_LISTA, index=2)
            with col2:
                ps2 = st.selectbox("Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3)
                ps3 = st.selectbox("Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4)
                ps4 = st.selectbox("Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5)
            
            folgas = st.multiselect("Professoras de Folga:", PROFESSORAS_LISTA)

            if st.button("🚀 Gerar Rodízio Sem Conflitos"):
                escala_final = []
                fluxo_coletivo = {
                    HORARIOS_LABELS[1]: {"Teo": ("Turma 1", pt2), "Sol": ("Turma 2", ps2)},
                    HORARIOS_LABELS[2]: {"Teo": ("Turma 2", pt3), "Sol": ("Turma 3", ps3)},
                    HORARIOS_LABELS[3]: {"Teo": ("Turma 3", pt4), "Sol": ("Turma 1", ps4)}
                }

                for t_nome, alunas in TURMAS.items():
                    for i, aluna in enumerate(alunas):
                        agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                        for h_idx in [1, 2, 3]:
                            h_label = HORARIOS_LABELS[h_idx]
                            cfg = fluxo_coletivo[h_label]
                            
                            if cfg["Teo"][0] == t_nome:
                                agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['Teo'][1]})"
                            elif cfg["Sol"][0] == t_nome:
                                agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['Sol'][1]})"
                            else:
                                p_ocupadas = [cfg["Teo"][1], cfg["Sol"][1]] + folgas
                                p_livres = [p for p in PROFESSORAS_LISTA if p not in p_ocupadas]
                                # Distribuição 1-para-1 usando o índice da aluna
                                instr_p = p_livres[i % len(p_livres)]
                                agenda[h_label] = f"🎹 SALA {MAPA_SALAS_FIXAS[instr_p]} | Prática ({instr_p})"
                        escala_final.append(agenda)
                
                supabase.table("calendario").upsert({"id": d_str, "escala": escala_final}).execute()
                st.rerun()
        else:
            st.success(f"✅ Rodízio ativo: {d_str}")
            st.dataframe(pd.DataFrame(cal_db[d_str]), use_container_width=True)
            if st.button("🗑️ Deletar Rodízio"):
                supabase.table("calendario").delete().eq("id", d_str).execute()
                st.rerun()

    with tab_chamada:
        st.subheader("📍 Registro de Presença")
        data_ch = st.selectbox("Data da Chamada:", [s.strftime("%d/%m/%Y") for s in sabados], key="ch_data")
        if st.button("✅ Presente em Massa"): st.session_state.all_p = True
        
        registros = []
        for aluna in ALUNAS_LISTA:
            c_n, c_s = st.columns([3, 2])
            status = c_s.radio(f"{aluna}", ["P", "F", "J"], horizontal=True, key=f"r_{aluna}", index=0 if st.session_state.get("all_p") else 1)
            registros.append({"data": data_ch, "aluna": aluna, "status": status})
        
        if st.button("💾 Salvar Chamada no Banco"):
            supabase.table("historico_geral").insert(registros).execute()
            st.success("Chamada gravada!")

    with tab_analise:
        st.subheader("📝 Análise Pedagógica Detalhada")
        alu_sel = st.selectbox("Aluna:", ALUNAS_LISTA)
        c1, c2 = st.columns(2); post = c1.text_area("Postura:"); tec = c2.text_area("Técnica:")
        c3, c4 = st.columns(2); rit = c3.text_area("Ritmo:"); teo = c4.text_area("Teoria:")
        banca = st.text_area("Dicas para Banca Semestral:")
        meta = st.text_input("Dica próxima aula:")
        
        if st.button("❄️ Congelar Análise"):
            dados = {"postura": post, "tecnica": tec, "ritmo": rit, "teoria": teo, "banca": banca, "meta": meta, "data": d_str}
            supabase.table("analises_congeladas").upsert({"id": alu_sel, "dados": dados}).execute()
            st.success(f"Análise de {alu_sel} congelada!")

# --- MÓDULO PROFESSORA ---
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Espaço da Professora")
    prof_nome = st.selectbox("Selecione seu nome:", PROFESSORAS_LISTA)
    data_hj = datetime.now().strftime("%d/%m/%Y")
    cal_db = db_get_calendario()
    
    if data_hj in cal_db:
        df = pd.DataFrame(cal_db[data_hj])
        minha_escala = df[df.apply(lambda row: row.astype(str).str.contains(prof_nome).any(), axis=1)]
        st.subheader(f"Sua agenda para hoje ({data_hj}):")
        st.table(minha_escala)
    else:
        st.warning("Nenhum rodízio gerado para a data de hoje.")

# --- MÓDULO ANALÍTICO (CONSULTA) ---
elif perfil == "📊 Analítico IA":
    st.header("📊 Consulta de Evolução")
    analises = db_get_analises()
    alu_ref = st.selectbox("Ver relatório de:", ALUNAS_LISTA)
    
    if alu_ref in analises:
        a = analises[alu_ref]["dados"]
        st.info(f"📅 Relatório referente a: {a['data']}")
        st.markdown(f"**Postura:** {a['postura']}\n\n**Técnica:** {a['tecnica']}")
        st.markdown(f"**Ritmo:** {a['ritmo']}\n\n**Teoria:** {a['teoria']}")
        st.warning(f"🎯 **Meta Banca:** {a['banca']}")
        st.success(f"💡 **Próxima Aula:** {a['meta']}")
    else:
        st.info("Ainda não há uma análise congelada para esta aluna.")
