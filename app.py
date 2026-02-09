import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io
from PIL import Image, ImageDraw
from supabase import create_client, Client

# --- 1. CONFIGURAÇÕES E BANCO ---
st.set_page_config(page_title="GEM Vila Verde", layout="wide")

@st.cache_resource
def init_supabase():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_supabase()

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
        res = supabase.table("historico_geral").select("*").execute()
        return res.data
    except: return []

def db_save_historico(dados):
    try:
        supabase.table("historico_geral").insert(dados).execute()
        return True
    except: return False

# --- 2. DADOS MESTRE ---
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
ALUNAS_LISTA = [
    "Amanda S.", "Ana Marcela S.", "Caroline C.", "Elisa F.", "Emilly O.", "Gabrielly V.",
    "Heloísa R.", "Ingrid M.", "Júlia Cristina", "Júlia S.", "Julya O.", "Mellina S.",
    "Micaelle S.", "Raquel L.", "Rebeca R.", "Rebecca A.", "Rebeka S.", "Sarah S.",
    "Stephany O.", "Vitória A.", "Vitória Bella T."
]
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly V. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
HORARIOS = ["08h45 (Igreja)", "09h35 (H2)", "10h10 (H3)", "10h45 (H4)"]

# --- 3. INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

calendario_db = db_get_calendario()
historico_geral = db_get_historico()

if perfil == "🏠 Secretaria":
    tab_plan, tab_chamada, tab_ped = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Análise Pedagógica"])
    
    with tab_plan:
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano = c2.selectbox("Ano:", [2026, 2027])
        sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano, mes) 
                   for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]
        data_sel = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados])

        if data_sel not in calendario_db:
            st.warning(f"Rodízio de {data_sel} não gerado.")
            col_t, col_s = st.columns(2)
            with col_t:
                st.subheader("📚 Teoria (SALA 8)")
                p_t = [st.selectbox(f"Prof. Teoria {h}", PROFESSORAS_LISTA, index=i, key=f"t{h}") for i, h in enumerate(["H2", "H3", "H4"])]
            with col_s:
                st.subheader("🔊 Solfejo (SALA 9)")
                p_s = [st.selectbox(f"Prof. Solfejo {h}", PROFESSORAS_LISTA, index=i+3, key=f"s{h}") for i, h in enumerate(["H2", "H3", "H4"])]
            folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA)

            if st.button(f"🚀 Gerar Rodízio Oficial {data_sel}"):
                escala = []
                fluxo_coletivo = {
                    HORARIOS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "ITeo": p_t[0], "ISol": p_s[0]},
                    HORARIOS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "ITeo": p_t[1], "ISol": p_s[1]},
                    HORARIOS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "ITeo": p_t[2], "ISol": p_s[2]}
                }
                for t_nome, alunas in TURMAS.items():
                    for idx_alu, aluna in enumerate(alunas):
                        row = {"Aluna": aluna, "Turma": t_nome, HORARIOS[0]: "⛪ Solfejo Melódico (Igreja)"}
                        for h_idx in [1, 2, 3]:
                            h_lab = HORARIOS[h_idx]
                            cfg = fluxo_coletivo[h_lab]
                            if cfg["Teo"] == t_nome: row[h_lab] = f"📚 SALA 8 | Teoria ({cfg['ITeo']})"
                            elif cfg["Sol"] == t_nome: row[h_lab] = f"🔊 SALA 9 | Solfejo ({cfg['ISol']})"
                            else:
                                p_livres = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]] + folgas]
                                instr = p_livres[(idx_alu + h_idx) % len(p_livres)]
                                num_sala = (PROFESSORAS_LISTA.index(instr) % 7) + 1
                                row[h_lab] = f"🎹 SALA {num_sala} | ({instr})"
                        escala.append(row)
                db_save_calendario(data_sel, escala)
                st.rerun()
        else:
            st.success(f"🗓️ Rodízio Ativo: {data_sel}")
            st.dataframe(pd.DataFrame(calendario_db[data_sel]), use_container_width=True)
            if st.button("🗑️ Excluir este Rodízio"):
                db_delete_calendario(data_sel)
                st.rerun()

    with tab_chamada:
        st.subheader("📍 Chamada")
        data_ch_sel = st.selectbox("Data da Chamada:", [s.strftime("%d/%m/%Y") for s in sabados])
        if st.button("✅ Marcar Todas Presentes"):
            st.session_state["p_geral"] = True
            st.rerun()
        
        idx_p = 0 if st.session_state.get("p_geral", False) else 1
        regs = []
        for aluna in ALUNAS_LISTA:
            c1, c2 = st.columns([3, 2])
            status = c2.radio(aluna, ["P", "F", "J"], index=idx_p, horizontal=True, key=f"ch_{aluna}", label_visibility="collapsed")
            c1.write(aluna)
            regs.append({"Aluna": aluna, "Status": status, "Data": data_ch_sel, "Tipo": "Chamada"})
        
        if st.button("💾 SALVAR CHAMADA"):
            for r in regs: db_save_historico(r)
            st.session_state["p_geral"] = False
            st.success("Salvo!")

    with tab_ped:
        st.subheader("✅ Análise Pedagógica")
        alu_sel = st.selectbox("Aluna:", ALUNAS_LISTA)
        with st.form("f_ped"):
            c1, c2 = st.columns(2)
            d_pos = c1.text_area("Postura:")
            d_tec = c2.text_area("Técnica:")
            d_rit = c1.text_area("Ritmo:")
            d_teo = c2.text_area("Teoria:")
            resumo = st.text_area("Resumo Secretaria (Banca):")
            meta = st.text_input("Meta próxima aula:")
            if st.form_submit_button("❄️ CONGELAR ANÁLISE"):
                db_save_historico({"Aluna": alu_sel, "Tipo": "Analise_Pedagogica", "Dados": {"Postura": d_pos, "Técnica": d_tec, "Ritmo": d_rit, "Teoria": d_teo, "Meta": meta, "Resumo": resumo}})
                st.success("Congelado!")

elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Professora:", PROFESSORAS_LISTA)
    data_p = st.selectbox("Data da Aula:", list(calendario_db.keys())) if calendario_db else None

    if data_p:
        h_sel = st.radio("⏰ Horário:", HORARIOS, horizontal=True)
        # Busca no banco se existe aula para esta professora neste horário
        dia_escala = calendario_db[data_p]
        atend = next((l for l in dia_escala if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            mat = "Teoria" if "Teoria" in atend[h_sel] else ("Solfejo" if "Solfejo" in atend[h_sel] else "Prática")
            st.warning(f"📍 Atendimento: {atend['Aluna'] if mat == 'Prática' else atend['Turma']} ({mat})")
            
            check_alunas = [atend['Aluna']] if mat == "Prática" else [a for a in TURMAS.get(atend['Turma'], []) if st.checkbox(a, value=True, key=f"p_{a}")]
            
            st.subheader(f"Dificuldades em {mat}")
            lista_dif = ["Não estudou", "Dificuldade rítmica", "Postura", "Metrônomo", "Clave de Fá", "Leitura", "Não apresentou dificuldades"]
            selecionadas = [d for d in lista_dif if st.checkbox(d, key=f"dif_{d}")]
            
            l_hj = st.text_input("📖 Lição dada:")
            obs_f = st.text_area("✍️ Relato Pedagógico:")

            if st.button("💾 SALVAR REGISTRO"):
                for aluna in check_alunas:
                    db_save_historico({"Data": data_p, "Aluna": aluna, "Tipo": "Aula", "Materia": mat, "Licao": l_hj, "Dificuldades": ", ".join(selecionadas), "Obs": obs_f, "Instrutora": instr_sel})
                st.success("Registrado!")
        else:
            st.info("Nenhuma aula agendada para este horário.")

elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica")
    if not historico_geral:
        st.info("Sem dados no histórico.")
    else:
        df_geral = pd.DataFrame(historico_geral)
        aluna_sel = st.selectbox("Selecione a Aluna:", sorted(df_geral["Aluna"].unique()))
        df_f = df_geral[df_geral["Aluna"] == aluna_sel]
        
        st.subheader("📈 Performance")
        col1, col2 = st.columns(2)
        with col1:
            df_aulas = df_f[df_f["Tipo"] == "Aula"]
            if not df_aulas.empty:
                st.write("Aulas por Matéria")
                st.bar_chart(df_aulas["Materia"].value_counts())
        with col2:
            df_ch = df_f[df_f["Tipo"] == "Chamada"]
            if not df_ch.empty:
                st.write("Frequência")
                st.bar_chart(df_ch["Status"].value_counts())
        
        if st.button("📥 Gerar Relatório PNG"):
            img = Image.new('RGB', (800, 600), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), f"Relatorio: {aluna_sel}\nGerado em: {datetime.now()}", fill=(0,0,0))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.download_button("Baixar PNG", buf.getvalue(), "relatorio.png")
