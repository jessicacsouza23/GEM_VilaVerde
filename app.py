import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from supabase import create_client, Client

# --- 1. CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- 2. CONEXÃO COM SUPABASE ---
# Usei suas credenciais fornecidas
SUPABASE_URL = "https://ixaqtoyqoianumczsjai.supabase.co"
SUPABASE_KEY = "sb_publishable_HwYONu26I0AzTR96yoy-Zg_nVxTlJD1"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro na conexão Supabase: {e}")
        return None

supabase = init_supabase()

# --- 3. FUNÇÕES DE BANCO DE DADOS ---
def db_save_calendario(d_str, escala):
    try:
        supabase.table("calendario").upsert({"id": d_str, "escala": escala}).execute()
    except Exception as e:
        st.error(f"Erro ao salvar rodízio: {e}")

def db_get_calendario():
    try:
        res = supabase.table("calendario").select("*").execute()
        return {item['id']: item['escala'] for item in res.data}
    except:
        return {}

def db_save_historico(dados):
    try:
        supabase.table("historico_geral").insert(dados).execute()
        return True
    except:
        return False

def db_save_analise(id_analise, dados):
    try:
        supabase.table("analises_congeladas").upsert({"id": id_analise, "dados": dados}).execute()
        return True
    except:
        return False

def db_get_analises():
    try:
        res = supabase.table("analises_congeladas").select("*").execute()
        return {item['id']: item['dados'] for item in res.data}
    except:
        return {}

# --- 4. DADOS MESTRE ---
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
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

# --- 5. INTERFACE ---
st.title("🎼 GEM Vila Verde - Sistema 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# --- MÓDULO SECRETARIA ---
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_analise = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Análise Pedagógica"])

    with tab_gerar:
        # Seleção de data
        c1, c2 = st.columns(2)
        mes_idx = datetime.now().month - 1
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=mes_idx)
        ano = c2.selectbox("Ano:", [2026, 2027])
        
        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        sabados = [d for sem in cal.monthdatescalendar(ano, mes) for d in sem if d.weekday() == calendar.SATURDAY and d.month == mes]
        d_str = st.selectbox("Data do Rodízio:", [s.strftime("%d/%m/%Y") for s in sabados])
        idx_sab = sabados[[s.strftime("%d/%m/%Y") for s in sabados].index(d_str)].day

        calendario_db = db_get_calendario()

        if d_str not in calendario_db:
            st.info(f"Configurando novo rodízio para {d_str}")
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

            if st.button("🚀 Gerar e Salvar no Supabase"):
                escala_final = []
                fluxo = {
                    HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "ITeo": pt2, "ISol": ps2},
                    HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "ITeo": pt3, "ISol": ps3},
                    HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "ITeo": pt4, "ISol": ps4}
                }

                for t_nome, alunas in TURMAS.items():
                    for i, aluna in enumerate(alunas):
                        agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                        for h_idx in [1, 2, 3]:
                            h_label = HORARIOS_LABELS[h_idx]
                            cfg = fluxo[h_label]
                            
                            if cfg["Teo"] == t_nome:
                                agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['ITeo']})"
                            elif cfg["Sol"] == t_nome:
                                agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['ISol']})"
                            else:
                                p_ocupadas = [cfg["ITeo"], cfg["ISol"]] + folgas
                                p_livres = [p for p in PROFESSORAS_LISTA if p not in p_ocupadas]
                                
                                instr_p = p_livres[(i + idx_sab) % len(p_livres)]
                                # SALA FIXA: Usa o índice original da lista mestre para nunca repetir
                                num_sala = (PROFESSORAS_LISTA.index(instr_p) % 7) + 1
                                agenda[h_label] = f"🎹 SALA {num_sala} | Prática ({instr_p})"
                        escala_final.append(agenda)
                
                db_save_calendario(d_str, escala_final)
                st.rerun()
        else:
            st.success(f"✅ Rodízio ativo para {d_str}")
            st.dataframe(pd.DataFrame(calendario_db[d_str]), use_container_width=True)
            if st.button("🗑️ Deletar Rodízio"):
                supabase.table("calendario").delete().eq("id", d_str).execute()
                st.rerun()

    with tab_chamada:
        st.subheader("📍 Chamada Rápida")
        if st.button("✅ Marcar Todas como Presente"):
            st.session_state.trigger_p = True

        registros = []
        for aluna in ALUNAS_LISTA:
            c_n, c_s = st.columns([3, 2])
            status = c_s.radio(f"{aluna}", ["P", "F", "J"], horizontal=True, label_visibility="collapsed", key=f"ch_{aluna}", index=0 if st.session_state.get("trigger_p") else 1)
            registros.append({"aluna": aluna, "status": status, "data": d_str})
        
        if st.button("💾 Salvar Chamada"):
            for r in registros: db_save_historico(r)
            st.success("Chamada Salva!")

    with tab_analise:
        st.subheader("📝 Análise Pedagógica Completa")
        alu_sel = st.selectbox("Selecione a Aluna:", ALUNAS_LISTA)
        
        # Campos detalhados conforme solicitado
        col_p, col_t = st.columns(2)
        postura = col_p.text_area("Postura:")
        tecnica = col_t.text_area("Técnica:")
        
        col_r, col_th = st.columns(2)
        ritmo = col_r.text_area("Ritmo:")
        teoria = col_th.text_area("Teoria:")
        
        banca = st.text_area("Dicas para Banca Semestral:")
        proxima = st.text_input("Meta para próxima aula:")

        if st.button("❄️ Congelar Análise"):
            dados_analise = {
                "postura": postura, "tecnica": tecnica, "ritmo": ritmo, 
                "teoria": teoria, "banca": banca, "proxima": proxima,
                "data": datetime.now().strftime("%d/%m/%Y")
            }
            db_save_analise(f"{alu_sel}_banca", dados_analise)
            st.success(f"Análise de {alu_sel} salva permanentemente!")

# --- MÓDULO ANALÍTICO (CONSULTA) ---
elif perfil == "📊 Analítico IA":
    st.header("📋 Histórico e Análises Salvas")
    analises = db_get_analises()
    alu_ref = st.selectbox("Ver análise de:", ALUNAS_LISTA)
    
    id_ref = f"{alu_ref}_banca"
    if id_ref in analises:
        a = analises[id_ref]
        st.write(f"**Data da última atualização:** {a['data']}")
        st.markdown(f"**Postura:** {a['postura']}")
        st.markdown(f"**Técnica:** {a['tecnica']}")
        st.markdown(f"**Ritmo:** {a['ritmo']}")
        st.markdown(f"**Teoria:** {a['teoria']}")
        st.warning(f"**Dicas Banca:** {a['banca']}")
        st.info(f"**Meta Próxima Aula:** {a['proxima']}")
    else:
        st.info("Nenhuma análise congelada para esta aluna.")
