import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from supabase import create_client, Client
import io
from PIL import Image, ImageDraw, ImageFont

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Oficial", layout="wide")

# Conexão Direta (Conforme solicitado)
SUPABASE_URL = "https://ixaqtoyqoianumczsjai.supabase.co"
SUPABASE_KEY = "sb_publishable_HwYONu26I0AzTR96yoy-Zg_nVxTlJD1"

@st.cache_resource
def init_supabase():
    try: return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = init_supabase()

# --- FUNÇÕES DE BANCO ---
def db_get_calendario():
    try:
        res = supabase.table("calendario").select("*").execute()
        return {item['id']: item['escala'] for item in res.data}
    except: return {}

def db_get_historico():
    try:
        res = supabase.table("historico_geral").select("*").execute()
        return res.data
    except: return []

def db_save_historico(dados):
    try: 
        supabase.table("historico_geral").insert(dados).execute()
        return True
    except Exception as e: 
        st.error(f"Erro ao salvar: {e}")
        return False

# --- 2. DADOS MESTRE ---
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
ALUNAS_LISTA = sorted([
    "Amanda S.", "Ana Marcela S.", "Caroline C.", "Elisa F.", "Emilly O.", "Gabrielly V.",
    "Heloísa R.", "Ingrid M.", "Júlia Cristina", "Júlia S.", "Julya O.", "Mellina S.",
    "Micaelle S.", "Raquel L.", "Rebeca R.", "Rebecca A.", "Rebeka S.", "Sarah S.",
    "Stephany O.", "Vitória A.", "Vitória Bella T."
])
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
HORARIOS = ["08h45 (Igreja)", "09h35 (H2)", "10h10 (H3)", "10h45 (H4)"]

# --- 3. INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

historico_geral = db_get_historico()
calendario_db = db_get_calendario()

# ==========================================
# MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    t_plan, t_cham, t_ped = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Análise Pedagógica"])
    
    with t_plan:
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
                p_t = [st.selectbox(f"Prof. Teoria {h}", PROFESSORAS_LISTA, index=i, key=f"t{h}{data_sel}") for i, h in enumerate(["H2", "H3", "H4"])]
            with col_s:
                st.subheader("🔊 Solfejo (SALA 9)")
                p_s = [st.selectbox(f"Prof. Solfejo {h}", PROFESSORAS_LISTA, index=i+3, key=f"s{h}{data_sel}") for i, h in enumerate(["H2", "H3", "H4"])]
            folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA, key=f"f{data_sel}")

            if st.button(f"🚀 Gerar Rodízio Oficial"):
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
                                row[h_lab] = f"🎹 SALA {num_sala} | {instr}"
                        escala.append(row)
                supabase.table("calendario").upsert({"id": data_sel, "escala": escala}).execute()
                st.rerun()
        else:
            st.success(f"🗓️ Rodízio Ativo: {data_sel}")
            df_v = pd.DataFrame(calendario_db[data_sel])
            st.dataframe(df_v[["Aluna", "Turma"] + HORARIOS], use_container_width=True)
            if st.button("🗑️ Excluir Rodízio"):
                supabase.table("calendario").delete().eq("id", data_sel).execute()
                st.rerun()

    with t_cham:
        st.subheader("📍 Chamada Secretaria")
        data_ch_sel = st.selectbox("Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="ch_sec")
        if st.button("✅ Marcar Todas como Presença"):
            st.session_state["p_geral"] = True
        
        idx_p = 0 if st.session_state.get("p_geral", False) else 1
        reg_chamada = []
        for aluna in ALUNAS_LISTA:
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.write(aluna)
            status = c2.radio(f"S_{aluna}", ["P", "F", "J"], index=idx_p, horizontal=True, key=f"r_{aluna}", label_visibility="collapsed")
            obs = c3.text_input("Obs:", key=f"o_{aluna}") if status == "J" else ""
            reg_chamada.append({"Data": data_ch_sel, "Aluna": aluna, "Status": status, "Obs": obs, "Tipo": "Chamada"})
        
        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True):
            for r in reg_chamada: db_save_historico(r)
            st.session_state["p_geral"] = False
            st.success("Salvo!")

    with t_ped:
        st.subheader("✅ Análise Pedagógica Individual")
        alu_sel = st.selectbox("Aluna:", ALUNAS_LISTA, key="ped_alu_sec")
        with st.form("f_ped_congelar"):
            c1, c2 = st.columns(2)
            d_pos = c1.text_area("Postura (Mãos/Coluna):")
            d_tec = c2.text_area("Técnica (Dedilhado/Articulação):")
            d_rit = c1.text_area("Ritmo (Metrônomo/Métrica):")
            d_teo = c2.text_area("Teoria (Leitura/Claves):")
            resumo = st.text_area("Resumo Secretaria (Banca Semestral):")
            meta = st.text_input("Meta próxima aula:")
            if st.form_submit_button("❄️ CONGELAR ANÁLISE"):
                db_save_historico({
                    "Aluna": alu_sel, "Tipo": "Analise_Pedagogica", "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Dados": {"Postura": d_pos, "Técnica": d_tec, "Ritmo": d_rit, "Teoria": d_teo, "Meta": meta, "Resumo": resumo}
                })
                st.success("Análise congelada para histórico!")

# ==========================================
# MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Professora:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in calendario_db:
        h_sel = st.radio("⏰ Horário:", HORARIOS, horizontal=True)
        atend = next((l for l in calendario_db[d_str] if instr_sel in str(l.get(h_sel, ""))), None)
        
        if atend:
            mat = "Teoria" if "SALA 8" in atend[h_sel] else ("Solfejo" if "SALA 9" in atend[h_sel] else "Prática")
            st.warning(f"📍 Atendimento: {atend['Aluna'] if mat == 'Prática' else atend['Turma']} ({mat})")
            
            check_alunas = [atend['Aluna']] if mat == "Prática" else [a for a in TURMAS.get(atend['Turma'], []) if st.checkbox(a, value=True)]
            
            st.subheader("📝 Relato de Dificuldades")
            if mat == "Prática":
                lista_dif = ["Não estudou", "Estudou insatisfatório", "Não assistiu vídeos", "Dificuldade rítmica", "Postura", "Punho alto/baixo", "Quebrando falanges", "Uso do metrônomo", "Não apresentou dificuldades"]
            else:
                lista_dif = ["Não realizou atividades", "Leitura rítmica", "Leitura métrica", "Solfejo (afinação)", "Movimento da mão", "Não apresentou dificuldades"]
            
            cols = st.columns(2)
            selecionadas = [d for i, d in enumerate(lista_dif) if cols[i % 2].checkbox(d)]
            
            li_hj = st.text_input("📖 Lição dada hoje:")
            p_m = st.text_input("🏠 Para casa (Método):")
            p_a = st.text_input("🏠 Para casa (Apostila):")
            obs_f = st.text_area("✍️ Relato Pedagógico:")

            if st.button("💾 SALVAR REGISTRO DE AULA", type="primary"):
                for aluna in check_alunas:
                    db_save_historico({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                        "Licao": li_hj, "Dificuldades": ", ".join(selecionadas), 
                        "Obs": obs_f, "Home_M": p_m, "Home_A": p_a, "Instrutora": instr_sel
                    })
                st.success("Registrado!")
        else: st.info("Sem aula agendada para você agora.")
    else: st.error("Rodízio não localizado.")

# ==========================================
# MÓDULO ANALÍTICO (COMPLETO)
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica - Vila Verde")
    
    if "analises_salvas" not in st.session_state: st.session_state.analises_salvas = {}
    
    if not historico_geral: st.info("Sem dados.")
    else:
        df_g = pd.DataFrame(historico_geral)
        c1, c2, c3 = st.columns(3)
        alu_sel = c1.selectbox("Aluna:", sorted(df_g["Aluna"].unique()))
        periodo = c2.selectbox("Período:", ["Diário", "Mensal", "Semestral"])
        d_ini = c3.date_input("A partir de:")

        df_f = df_g[(df_g["Aluna"] == alu_sel)] # Filtro simplificado para exemplo
        
        if not df_f.empty:
            df_aulas = df_f[df_f["Tipo"] == "Aula"]
            df_ped = df_f[df_f["Tipo"] == "Analise_Pedagogica"]

            # Exibição da Análise "Congelada"
            if not df_ped.empty:
                st.subheader("❄️ Última Análise Congelada")
                ultima = df_ped.iloc[-1]["Dados"]
                with st.container(border=True):
                    st.markdown(f"### Ficha: {alu_sel}")
                    col_a, col_b = st.columns(2)
                    col_a.error(f"**POSTURA:** {ultima.get('Postura')}")
                    col_b.warning(f"**TÉCNICA:** {ultima.get('Técnica')}")
                    col_a.info(f"**RITMO:** {ultima.get('Ritmo')}")
                    col_b.success(f"**TEORIA:** {ultima.get('Teoria')}")
                    st.divider()
                    st.write(f"**🏢 Resumo Secretaria:** {ultima.get('Resumo')}")
                    st.write(f"**🎯 Meta:** {ultima.get('Meta')}")

                # --- GERADOR DE PNG ---
                img = Image.new('RGB', (800, 600), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                txt = f"RELATORIO PEDAGOGICO - {alu_sel}\n\nPOSTURA: {ultima.get('Postura')}\nTECNICA: {ultima.get('Técnica')}\nRITMO: {ultima.get('Ritmo')}\nTEORIA: {ultima.get('Teoria')}\n\nBANCA: {ultima.get('Resumo')}"
                d.text((40, 40), txt, fill=(0, 0, 0))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.download_button("📥 Baixar Relatório PNG", buf.getvalue(), "analise.png")

            st.divider()
            st.subheader("📂 Logs de Auditoria")
            st.dataframe(df_aulas[["Data", "Materia", "Licao", "Dificuldades", "Instrutora"]], use_container_width=True)
