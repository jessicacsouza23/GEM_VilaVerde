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
    tab_plan, tab_cham, tab_ped = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Análise Pedagógica"])
    
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
            
            folgas = st.multiselect("Professoras de Folga:", PROFESSORAS_LISTA)

            if st.button("🚀 Gerar Rodízio"):
                escala = []
                # Configuração fixa das turmas por horário
                fluxo = {
                    HORARIOS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "ITeo": p_t[0], "ISol": p_s[0]},
                    HORARIOS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "ITeo": p_t[1], "ISol": p_s[1]},
                    HORARIOS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "ITeo": p_t[2], "ISol": p_s[2]}
                }

                for t_nome, alunas in TURMAS.items():
                    for idx_alu, aluna in enumerate(alunas):
                        row = {"Aluna": aluna, "Turma": t_nome, HORARIOS[0]: "⛪ Igreja"}
                        
                        for h_idx in [1, 2, 3]:
                            h_lab = HORARIOS[h_idx]
                            cfg = fluxo[h_lab]
                            
                            # 1. Verificar se a turma está em aula coletiva
                            if cfg["Teo"] == t_nome:
                                row[h_lab] = f"📚 SALA 8 | {cfg['ITeo']}"
                            elif cfg["Sol"] == t_nome:
                                row[h_lab] = f"🔊 SALA 9 | {cfg['ISol']}"
                            else:
                                # 2. Aula Prática: Filtrar professoras realmente disponíveis neste horário
                                ocupadas = [cfg["ITeo"], cfg["ISol"]] + folgas
                                disponiveis = [p for p in PROFESSORAS_LISTA if p not in ocupadas]
                                
                                # 3. Distribuição para evitar repetição de professora e sala
                                # Usamos o índice da aluna dentro da turma para rotacionar
                                p_index = (idx_alu) % len(disponiveis)
                                instrutora = disponiveis[p_index]
                                
                                # 4. Definir Sala de Prática (1 a 7) baseada na posição da instrutora na lista oficial
                                num_sala = (PROFESSORAS_LISTA.index(instrutora) % 7) + 1
                                row[h_lab] = f"🎹 SALA {num_sala} | {instrutora}"
                        
                        escala.append(row)
                
                supabase.table("calendario").upsert({"id": data_sel, "escala": escala}).execute()
                st.success("Rodízio gerado com sucesso!")
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

    with tab_ped:
        st.subheader("✅ Análise Pedagógica Completa")
        alu_ped = st.selectbox("Aluna:", ALUNAS_LISTA, key="alu_ped_sec")
        with st.form("f_ped_completo"):
            c1, c2 = st.columns(2)
            d_pos = c1.text_area("Postura (Mãos/Coluna/Pés):")
            d_tec = c2.text_area("Técnica (Dedilhado/Articulação):")
            d_rit = c1.text_area("Ritmo (Metrônomo/Métrica):")
            d_teo = c2.text_area("Teoria (Leitura/Claves):")
            resumo = st.text_area("Resumo Secretaria (Banca Semestral):")
            meta = st.text_input("Dicas para a próxima aula:")
            if st.form_submit_button("❄️ CONGELAR ANÁLISE"):
                db_save_historico({
                    "Aluna": alu_ped, "Tipo": "Analise_Pedagogica", "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Dados": {"Postura": d_pos, "Técnica": d_tec, "Ritmo": d_rit, "Teoria": d_teo, "Meta": meta, "Resumo": resumo}
                })
                st.success("Análise congelada!")

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

