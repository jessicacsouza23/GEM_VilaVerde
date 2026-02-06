import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
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

# --- FUNÇÕES DE PERSISTÊNCIA (SUPABASE) ---
def db_get_calendario():
    try:
        res = supabase.table("calendario").select("*").execute()
        return {item['id']: item['escala'] for item in res.data}
    except: return {}

def db_save_calendario(d_str, escala):
    supabase.table("calendario").upsert({"id": d_str, "escala": escala}).execute()

def db_delete_calendario(d_str):
    supabase.table("calendario").delete().eq("id", d_str).execute()

# --- BANCO DE DADOS MESTRE (ORIGINAL) ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]

# ORDEM CRÍTICA DOS HORÁRIOS
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

def get_sabados_do_mes(ano, mes):
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    dias = cal.monthdatescalendar(ano, mes)
    return [dia for semana in dias for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora"])

calendario_anual = db_get_calendario()

if perfil == "🏠 Secretaria":
    st.subheader("🗓️ Gestão de Rodízios")
    c_m1, c_m2 = st.columns(2)
    mes_ref = c_m1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
    ano_ref = c_m2.selectbox("Ano:", [2026, 2027], index=0)
    sabados = get_sabados_do_mes(ano_ref, mes_ref)
    
    for idx_sab, sab in enumerate(sabados):
        d_str = sab.strftime("%d/%m/%Y")
        with st.expander(f"📅 SÁBADO: {d_str}"):
            if d_str not in calendario_anual:
                c1, c2 = st.columns(2)
                with c1:
                    pt2, pt3, pt4 = [st.selectbox(f"Teoria H{i} ({d_str}):", PROFESSORAS_LISTA, index=i-2, key=f"pt{i}_{d_str}") for i in range(2, 5)]
                with c2:
                    st2, st3, st4 = [st.selectbox(f"Solfejo H{i} ({d_str}):", PROFESSORAS_LISTA, index=i+1, key=f"st{i}_{d_str}") for i in range(2, 5)]
                folgas = st.multiselect(f"Folgas ({d_str}):", PROFESSORAS_LISTA, key=f"f_{d_str}")

                if st.button(f"🚀 Gerar Rodízio para {d_str}", key=f"btn_{d_str}"):
                    escala_final = []
                    fluxo = {
                        HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                        HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                        HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
                    }
                    
                    for t_nome, alunas in TURMAS.items():
                        for i, aluna in enumerate(alunas):
                            # Montagem do dicionário seguindo a ordem
                            agenda = {
                                "Aluna": aluna, 
                                "Turma": t_nome, 
                                HORARIOS_LABELS[0]: "⛪ IGREJA"
                            }
                            
                            for h_idx in [1, 2, 3]:
                                h_label = HORARIOS_LABELS[h_idx]
                                cfg = fluxo[h_label]
                                
                                if cfg["Teo"] == t_nome:
                                    agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['ITeo']})"
                                elif cfg["Sol"] == t_nome:
                                    agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['ISol']})"
                                else:
                                    p_disp = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]] + folgas]
                                    f_rot = (i + (idx_sab * 3) + h_idx)
                                    instr_p = p_disp[f_rot % len(p_disp)] if p_disp else "Vago"
                                    
                                    idx_instr = PROFESSORAS_LISTA.index(instr_p) if instr_p in PROFESSORAS_LISTA else 0
                                    sala_fixa = ((idx_instr + idx_sab) % 7) + 1
                                    agenda[h_label] = f"🎹 SALA {sala_fixa} | Prática ({instr_p})"
                            
                            escala_final.append(agenda)
                    
                    db_save_calendario(d_str, escala_final)
                    st.rerun()
            else:
                # --- CORREÇÃO DA ORDEM DAS COLUNAS ---
                df_view = pd.DataFrame(calendario_anual[d_str])
                # Reorganiza as colunas na ordem correta: Aluna, Turma, 1ª Aula, 2ª Aula, 3ª Aula, 4ª Aula
                colunas_ordenadas = ["Aluna", "Turma"] + HORARIOS_LABELS
                df_view = df_view[colunas_ordenadas]
                
                st.table(df_view)
                
                if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                    db_delete_calendario(d_str)
                    st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Identificação:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend = next((l for l in calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            sala_info = atend[h_sel].split("|")[0] if "|" in atend[h_sel] else "Igreja"
            quem_info = atend['Aluna'] if "Prática" in atend[h_sel] else atend['Turma']
            st.warning(f"📍 **ATENDIMENTO:** {quem_info} | **LOCAL:** {sala_info}")
            st.divider()

            texto_aula = atend[h_sel]
            mat = "Teoria" if "Teoria" in texto_aula else ("Solfejo" if "Solfejo" in texto_aula else "Prática")
            check_alunas = [atend['Aluna']] if mat == "Prática" else [a for a in TURMAS[atend['Turma']] if st.checkbox(a, value=True, key=f"p_{a}")]
            
            selecionadas = []
            home_m, home_a, lic_aula = "", "", ""

            if mat == "Prática":
                st.subheader("🎹 Aula Prática")
                lic_aula = st.selectbox("Lição/Volume:", [str(i) for i in range(1, 41)] + ["Outro"], key="lic_pr")
                dif_pr = ["Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos", "Dificuldade ritmica", "Punho alto ou baixo", "Sem metrônomo", "Não apresentou dificuldades"] # Simplificado para o exemplo, use sua lista completa
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_pr):
                    if (c1 if i < 4 else c2).checkbox(d, key=f"dk_{i}"): selecionadas.append(d)
                home_m = st.selectbox("Lição de casa - Volume:", [str(i) for i in range(1, 41)], key="hmp")
                home_a = st.text_input("Apostila:", key="hap")

            elif mat == "Teoria" or mat == "Solfejo":
                st.subheader(f"📚 Aula {mat}")
                lic_aula = st.text_input(f"Lição {mat}:")
                dif_te = ["Não assistiu vídeos", "Dificuldade leitura", "Sem metrônomo", "Não realizou atividades", "Sem dificuldades"]
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_te):
                    if (c1 if i < 3 else c2).checkbox(d, key=f"dt_{i}"): selecionadas.append(d)
                home_m = st.text_input(f"Casa ({mat}):")

            obs = st.text_area("Relato de Evolução:")
            if st.button("💾 SALVAR REGISTRO"):
                for aluna in check_alunas:
                    db_save_historico({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                        "Licao": lic_aula, "Dificuldades": selecionadas, "Obs": obs, 
                        "Home_M": home_m, "Home_A": home_a, "Instrutora": instr_sel
                    })
                st.success("Aula salva!")
                st.balloons()
        else: st.warning("Sem escala para você.")
    else: st.warning("Rodízio pendente.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica")
    if not historico_geral:
        st.info("Aguardando registros...")
    else:
        df_geral = pd.DataFrame(historico_geral)
        todas_alunas = sorted(df_geral["Aluna"].unique())
        aluna_sel = st.selectbox("Selecione a Aluna:", todas_alunas)
        
        df_f = df_geral[df_geral["Aluna"] == aluna_sel]
        st.subheader(f"Análise de {aluna_sel}")
        st.dataframe(df_f)



