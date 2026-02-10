import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from supabase import create_client, Client
import io
from PIL import Image, ImageDraw

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide")

# Conexão Supabase
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
SECRETARIAS_LISTA = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"]
ALUNAS_LISTA = sorted([
    "Amanda S. - Parque do Carmo II", "Anne da Silva - Vila Verde", "Ana Marcela S. - Vila Verde", 
    "Caroline C. - Vila Ré", "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá Velha", 
    "Gabrielly V. - Vila Verde", "Heloísa R. - Vila Verde", "Ingrid M. - Parque do Carmo II", 
    "Júlia Cristina - União de Vila Nova", "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá Velha", 
    "Mellina S. - Jardim Lígia", "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", 
    "Rebeca R. - Vila Ré", "Rebecca A. - Vila Verde", "Rebeka S. - Jardim Lígia", 
    "Sarah S. - Vila Verde", "Stephany O. - Vila Curuçá Velha", "Vitória A. - Vila Verde", 
    "Vitória Bella T. - Vila Verde"
])

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
STATUS_LICAO = ["Realizadas - sem pendência", "Realizada - devolvida para refazer", "Não realizada"]

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
    tab_plan, tab_cham, tab_lição = st.tabs(["🗓️ Planejamento", "📍 Chamada", "📝 Controle de Lições"])
    
    with tab_plan:
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano = c2.selectbox("Ano:", [2026, 2027])
        sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano, mes) 
                   for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]
        data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados])

        if data_sel_str not in calendario_db:
            st.warning("Rodízio não gerado.")
            col_t, col_s = st.columns(2)
            with col_t:
                st.subheader("📚 Teoria (SALA 8)")
                pt2 = st.selectbox("Prof. Teoria H2", PROFESSORAS_LISTA, index=0, key="t2")
                pt3 = st.selectbox("Prof. Teoria H3", PROFESSORAS_LISTA, index=1, key="t3")
                pt4 = st.selectbox("Prof. Teoria H4", PROFESSORAS_LISTA, index=2, key="t4")
            with col_s:
                st.subheader("🔊 Solfejo (SALA 9)")
                ps2 = st.selectbox("Prof. Solfejo H2", PROFESSORAS_LISTA, index=3, key="s2")
                ps3 = st.selectbox("Prof. Solfejo H3", PROFESSORAS_LISTA, index=4, key="s3")
                ps4 = st.selectbox("Prof. Solfejo H4", PROFESSORAS_LISTA, index=5, key="s4")
            
            folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA)

            if st.button("🚀 GERAR RODÍZIO CARROSSEL TOTAL"):
                # Semente de rotação baseada na data
                dt_obj = datetime.strptime(data_sel_str, "%d/%m/%Y")
                offset = dt_obj.isocalendar()[1] # Semana do ano (ex: 6, 7, 8...)
                
                mapa = {aluna: {"Aluna": aluna, "Turma": t_nome} for t_nome, alunas in TURMAS.items() for aluna in alunas}
                for a in mapa: mapa[a][HORARIOS[0]] = "⛪ Igreja"

                config_h = {
                    HORARIOS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "P_Teo": pt2, "P_Sol": ps2},
                    HORARIOS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "P_Teo": pt3, "P_Sol": ps3},
                    HORARIOS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "P_Teo": pt4, "P_Sol": ps4}
                }

                for h in [HORARIOS[1], HORARIOS[2], HORARIOS[3]]:
                    conf = config_h[h]
                    ocupadas_h = [conf["P_Teo"], conf["P_Sol"]] + folgas
                    profs_livres = [p for p in PROFESSORAS_LISTA if p not in ocupadas_h]
                    
                    # Rodar a lista de professoras livres baseado na semana
                    # Isso garante que a Professora que estava na Sala 1 semana passada mude
                    num_profs = len(profs_livres)
                    
                    alunas_pratica = []
                    for t_nome, alunas in TURMAS.items():
                        if conf["Teo"] == t_nome:
                            for a in alunas: mapa[a][h] = f"📚 SALA 8 | {conf['P_Teo']}"
                        elif conf["Sol"] == t_nome:
                            for a in alunas: mapa[a][h] = f"🔊 SALA 9 | {conf['P_Sol']}"
                        else:
                            alunas_pratica.extend(alunas)
                    
                    # Distribuição com deslocamento duplo (Aluna -> Prof -> Sala)
                    for i, aluna_p in enumerate(alunas_pratica):
                        # i + offset garante que a cada semana a aluna pegue uma prof diferente
                        # e que cada prof pegue uma sala diferente
                        posicao_rotativa = (i + offset) % num_profs
                        prof_da_vez = profs_livres[posicao_rotativa]
                        
                        # Sala rotativa: a sala também muda para a professora
                        sala_num = ((posicao_rotativa + offset) % 7) + 1
                        
                        mapa[aluna_p][h] = f"🎹 SALA {sala_num} | {prof_da_vez}"

                supabase.table("calendario").upsert({"id": data_sel_str, "escala": list(mapa.values())}).execute()
                st.rerun()
        else:
            st.success(f"🗓️ Rodízio Ativo: {data_sel_str}")
            df_raw = pd.DataFrame(calendario_db[data_sel_str])
            cols = [c for c in ["Aluna", "Turma"] + HORARIOS if c in df_raw.columns]
            st.dataframe(df_raw[cols], use_container_width=True, hide_index=True)
            if st.button("🗑️ Deletar Rodízio"):
                supabase.table("calendario").delete().eq("id", data_sel_str).execute()
                st.rerun()
                
    with tab_cham:
            st.subheader("📍 Chamada")
            dt_ch = st.selectbox("Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="dt_ch")
            reg_chamada = []
            for aluna in ALUNAS_LISTA:
                c1, c2, c3 = st.columns([2, 1, 2])
                c1.write(aluna)
                status = c2.radio(f"S_{aluna}", ["P", "F", "J"], horizontal=True, key=f"st_{aluna}", label_visibility="collapsed")
                obs = c3.text_input("Obs:", key=f"ob_{aluna}") if status == "J" else ""
                reg_chamada.append({"Data": dt_ch, "Aluna": aluna, "Status": status, "Obs": obs, "Tipo": "Chamada"})
            if st.button("💾 Salvar Chamada"):
                for r in reg_chamada: db_save_historico(r)
                st.success("Chamada Salva!")

    with tab_lição:
        st.subheader("📝 Controle de Lições (Secretaria)")
        with st.form("f_controle_licoes", clear_on_submit=True):
            data_aula = st.date_input("Data da aula:", datetime.now())
            sec_resp = st.selectbox("Secretária responsável:", SECRETARIAS_LISTA)
            alu_sel = st.selectbox("Aluna:", ALUNAS_LISTA)
            
            st.divider()
            c1, c2 = st.columns([1, 2])
            cat_sel = c1.radio("Categoria:", CATEGORIAS_LICAO)
            detalhe_licao = c2.text_input("Lição / Página:", placeholder="Ex: Lição 02 a 10, pág 15")
            
            st.divider()
            status_sel = st.radio("Status das Lições:", STATUS_LICAO, horizontal=True)
            obs_liçao = st.text_area("Observações Adicionais:")
            
            if st.form_submit_button("❄️ CONGELAR CONTROLE DE LIÇÃO"):
                dados_licao = {
                    "Aluna": alu_sel,
                    "Tipo": "Controle_Licao",
                    "Data": data_aula.strftime("%d/%m/%Y"),
                    "Secretaria": sec_resp,
                    "Categoria": cat_sel,
                    "Licao_Detalhe": detalhe_licao, # NOVO CAMPO
                    "Status": status_sel,
                    "Observacao": obs_liçao
                }
                db_save_historico(dados_licao)
                st.success(f"Registro de {alu_sel} salvo com sucesso!")
# ==========================================
# MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr = st.selectbox("Professora:", PROFESSORAS_LISTA)
    data_hj = datetime.now().strftime("%d/%m/%Y")

    if data_hj in calendario_db:
        h_atual = st.radio("Horário:", HORARIOS, horizontal=True)
        escala = calendario_db[data_hj]
        atend = next((l for l in escala if instr in str(l.get(h_atual, ""))), None)
        
        if atend:
            mat = "Teoria" if "SALA 8" in atend[h_atual] else ("Solfejo" if "SALA 9" in atend[h_atual] else "Prática")
            st.warning(f"📍 {mat}: {atend['Aluna'] if mat == 'Prática' else atend['Turma']}")
            
            with st.form("f_aula_prof"):
                li_hj = st.text_input("Lição dada hoje:")
                st.write("---")
                st.write("**Dificuldades:**")
                lista_dif = ["Postura", "Punho", "Ritmo", "Leitura", "Metrônomo", "Não estudou", "Sem dificuldades"]
                cols = st.columns(3)
                difs = [d for i, d in enumerate(lista_dif) if cols[i%3].checkbox(d)]
                
                p_casa = st.text_input("Para casa (Lições/Apostila):")
                relato = st.text_area("O que observar na próxima aula:")
                
                if st.form_submit_button("💾 Salvar Registro"):
                    db_save_historico({
                        "Data": data_hj, "Aluna": atend["Aluna"], "Tipo": "Aula", "Materia": mat,
                        "Licao": li_hj, "Dificuldades": ", ".join(difs), "ParaCasa": p_casa, "Obs": relato, "Instrutora": instr
                    })
                    st.success("Aula registrada!")
        else: st.info("Sem aula agora.")
    else: st.error("Rodízio não gerado para hoje.")

# ==========================================
# MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica")
    if not historico_geral: st.info("Sem dados.")
    else:
        df_g = pd.DataFrame(historico_geral)
        alu = st.selectbox("Aluna:", sorted(df_g["Aluna"].unique()))
        df_f = df_g[df_g["Aluna"] == alu]
        
        # Filtra a última análise pedagógica
        df_ped = df_f[df_f["Tipo"] == "Analise_Pedagogica"]
        if not df_ped.empty:
            last = df_ped.iloc[-1]["Dados"]
            with st.container(border=True):
                st.subheader(f"📋 Ficha de Avaliação: {alu}")
                c1, c2 = st.columns(2)
                c1.error(f"**🔹 POSTURA:**\n{last.get('Postura')}")
                c2.warning(f"**🔹 TÉCNICA:**\n{last.get('Técnica')}")
                c1.info(f"**🔹 RITMO:**\n{last.get('Ritmo')}")
                c2.success(f"**🔹 TEORIA:**\n{last.get('Teoria')}")
                st.divider()
                st.markdown(f"**🏢 Resumo Secretaria:** {last.get('Resumo')}")
                st.markdown(f"**💡 Próxima Aula:** {last.get('Meta')}")

                # Exportar PNG
                img = Image.new('RGB', (1000, 700), color=(255, 255, 255))
                draw = ImageDraw.Draw(img)
                txt = f"GEM VILA VERDE - RELATORIO\nALUNA: {alu}\n\nPOSTURA: {last.get('Postura')}\nTECNICA: {last.get('Técnica')}\nRITMO: {last.get('Ritmo')}\nTEORIA: {last.get('Teoria')}\n\nBANCA: {last.get('Resumo')}\nMETA: {last.get('Meta')}"
                draw.text((50, 50), txt, fill=(0,0,0))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.download_button("📥 Exportar PNG Detalhado", buf.getvalue(), f"Analise_{alu}.png")

        st.subheader("📂 Histórico de Aulas")
        st.dataframe(df_f[df_f["Tipo"] == "Aula"][["Data", "Materia", "Licao", "Dificuldades", "Instrutora"]], use_container_width=True)














