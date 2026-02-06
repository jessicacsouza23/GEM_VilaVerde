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

# --- FUNÇÕES DE BANCO DE DADOS ---
def db_get_calendario():
    try:
        res = supabase.table("calendario").select("*").execute()
        return {item['id']: item['escala'] for item in res.data}
    except: return {}

def db_save_calendario(d_str, escala):
    supabase.table("calendario").upsert({"id": d_str, "escala": escala}).execute()

def db_delete_calendario(d_str):
    supabase.table("calendario").delete().eq("id", d_str).execute()

def db_get_historico():
    try:
        res = supabase.table("historico_geral").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

def db_save_historico(dados):
    # Converte listas em strings para evitar erro de API do Supabase
    if "Dificuldades" in dados and isinstance(dados["Dificuldades"], list):
        dados["Dificuldades"] = ", ".join(dados["Dificuldades"])
    supabase.table("historico_geral").insert(dados).execute()

def db_get_correcoes():
    try:
        res = supabase.table("correcoes_secretaria").select("*").execute()
        return res.data
    except: return []

def db_save_correcao(dados):
    supabase.table("correcoes_secretaria").insert(dados).execute()

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
SECRETARIAS = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"]
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
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

calendario_anual = db_get_calendario()
historico_geral = db_get_historico()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_correcao = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Correção de Atividades"])

    with tab_gerar:
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
                                agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                                for h_idx in [1, 2, 3]:
                                    h_label = HORARIOS_LABELS[h_idx]; cfg = fluxo[h_label]
                                    if cfg["Teo"] == t_nome: agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['ITeo']})"
                                    elif cfg["Sol"] == t_nome: agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['ISol']})"
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
                    df_view = pd.DataFrame(calendario_anual[d_str])
                    colunas_certas = ["Aluna", "Turma"] + HORARIOS_LABELS
                    st.table(df_view[colunas_certas])
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        db_delete_calendario(d_str)
                        st.rerun()

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        data_ch_sel = st.selectbox("Data da Chamada:", [s.strftime("%d/%m/%Y") for s in sabados])
        presenca_padrao = st.toggle("Marcar todas como Presente", value=True)
        registros_chamada = []
        for turma, alunas in TURMAS.items():
            with st.expander(f"Chamada - {turma}"):
                for aluna in alunas:
                    c1, c2, c3 = st.columns([2, 2, 2])
                    c1.write(aluna)
                    st_alu = c2.radio("Status", ["Presente", "Falta", "Justificada"], index=0 if presenca_padrao else 1, key=f"ch_{aluna}_{data_ch_sel}", horizontal=True, label_visibility="collapsed")
                    mot_alu = c3.text_input("Obs", key=f"mot_{aluna}_{data_ch_sel}", placeholder="Motivo...", label_visibility="collapsed") if st_alu == "Justificada" else ""
                    registros_chamada.append({"Data": data_ch_sel, "Aluna": aluna, "Tipo": "Chamada", "Status": st_alu, "Motivo": mot_alu})
        
        if st.button("💾 Salvar Chamada Completa"):
            for r in registros_chamada: db_save_historico(r)
            st.success("Chamada salva!")

    with tab_correcao:
        st.subheader("✅ Correção de Atividades (Secretaria)")
        sec_resp = st.selectbox("Secretária:", SECRETARIAS)
        alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
        status_corr = st.radio("Status:", ["Realizada", "Não Realizada", "Devolvida"], horizontal=True)
        obs_sec = st.text_area("Notas da Secretaria:")
        if st.button("💾 Salvar Registro de Correção"):
            db_save_correcao({"Data": datetime.now().strftime("%d/%m/%Y"), "Aluna": alu_corr, "Secretaria": sec_resp, "Status": status_corr, "Obs": obs_sec})
            st.success("Salvo!")

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
            
            mat = "Teoria" if "Teoria" in atend[h_sel] else ("Solfejo" if "Solfejo" in atend[h_sel] else "Prática")
            check_alunas = [atend['Aluna']] if mat == "Prática" else [a for a in TURMAS[atend['Turma']] if st.checkbox(f"Presente: {a}", value=True, key=f"p_{a}")]
            
            selecionadas = []
            home_m, home_a, lic_aula = "", "", ""

            if mat == "Prática":
                st.subheader("🎹 Controle de Desempenho - Prática")
                lic_aula = st.selectbox("Lição/Volume Atual:", [str(i) for i in range(1, 41)] + ["Outro"])
                dif_pr = ["Não estudou", "Insatisfatório", "Postura", "Metrônomo", "Leitura Clave Sol", "Leitura Clave Fá", "Articulação", "Dedilhado", "Sem dificuldades"]
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_pr):
                    if (c1 if i < 5 else c2).checkbox(d, key=f"dk_{d}"): selecionadas.append(d)
                home_m = st.selectbox("Tarefa (Volume):", [str(i) for i in range(1, 41)])
                home_a = st.text_input("Tarefa (Apostila):")

            else:
                st.subheader(f"📚 Controle de Desempenho - {mat}")
                lic_aula = st.text_input("Lição do dia:")
                dif_te = ["Não assistiu vídeos", "Teoria básica", "Ritmo", "Solfejo (Afinação)", "Movimento Mão", "Sem dificuldades"]
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_te):
                    if (c1 if i < 3 else c2).checkbox(d, key=f"dt_{d}"): selecionadas.append(d)
                home_m = st.text_input("Tarefa de casa:")

            obs = st.text_area("Observações Pedagógicas:")
            
            if st.button("💾 SALVAR REGISTRO"):
                for aluna in check_alunas:
                    db_save_historico({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                        "Licao": lic_aula, "Dificuldades": selecionadas, "Obs": obs, 
                        "Home_M": home_m, "Home_A": home_a, "Instrutora": instr_sel
                    })
                st.success(f"Registros de {mat} salvos com sucesso!")
        else: st.warning("Você não tem atendimento agendado para este horário.")
    else: st.warning("A secretaria ainda não gerou o rodízio para esta data.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Banco de Dados Pedagógico")
    if historico_geral:
        st.dataframe(pd.DataFrame(historico_geral))
    else: st.info("Sem dados registrados até o momento.")
