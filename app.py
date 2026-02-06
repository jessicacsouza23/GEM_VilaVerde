import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
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
    try:
        supabase.table("calendario").upsert({"id": d_str, "escala": escala}).execute()
    except Exception as e:
        st.error(f"Erro ao salvar rodízio: {e}")

def db_delete_calendario(d_str):
    supabase.table("calendario").delete().eq("id", d_str).execute()

def db_get_historico():
    try:
        res = supabase.table("historico_geral").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

def db_save_historico(dados):
    # Converte lista de dificuldades em texto para o banco
    if "Dificuldades" in dados and isinstance(dados["Dificuldades"], list):
        dados["Dificuldades"] = ", ".join(dados["Dificuldades"]) if dados["Dificuldades"] else "Nenhuma"
    
    try:
        supabase.table("historico_geral").insert(dados).execute()
        return True
    except Exception as e:
        if "42501" in str(e):
            st.error("🚨 BLOQUEIO DE SEGURANÇA: Vá ao painel do Supabase > Policies > historico_geral e ative a política de INSERT como 'true'.")
        else:
            st.error(f"Erro técnico: {e}")
        return False

# --- DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
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
    tab_gerar, tab_chamada = st.tabs(["🗓️ Rodízio", "📍 Chamada"])

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
                    # GARANTE IGREJA EM PRIMEIRO
                    col_ordem = ["Aluna", "Turma"] + HORARIOS_LABELS
                    st.table(df_view[col_ordem])
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        db_delete_calendario(d_str)
                        st.rerun()

    with tab_chamada:
        st.subheader("📍 Registro de Presença")
        dt_ch = st.selectbox("Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="dt_ch")
        for t_n, alunas in TURMAS.items():
            with st.expander(f"Chamada {t_n}"):
                for aluna in alunas:
                    c1, c2 = st.columns([3, 2])
                    st_ch = c2.radio(f"{aluna}", ["P", "F", "J"], horizontal=True, key=f"v_{aluna}_{dt_ch}")
                    if st.button(f"Salvar {aluna}", key=f"b_{aluna}"):
                        db_save_historico({"Data": dt_ch, "Aluna": aluna, "Tipo": "Chamada", "Status": st_ch})
                        st.toast(f"Presença de {aluna} salva!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Professora:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend = next((l for l in calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            mat = "Teoria" if "Teoria" in atend[h_sel] else ("Solfejo" if "Solfejo" in atend[h_sel] else "Prática")
            st.warning(f"📍 Atendimento: {atend['Aluna'] if mat == 'Prática' else atend['Turma']} ({mat})")
            
            check_alunas = [atend['Aluna']] if mat == "Prática" else [a for a in TURMAS[atend['Turma']] if st.checkbox(a, value=True, key=f"chk_{a}")]
            
            selecionadas = []
            # FORMULÁRIO PEDAGÓGICO COMPLETO
            if mat == "Prática":
                st.subheader("🎹 Dificuldades Técnicas/Posturais")
                lista_dif = [
                    "Postura de Costas/Braços", "Punho alto/baixo", "Quebrando falanges", 
                    "Dedos não arredondados", "Pé esquerdo na pedaleira", "Uso do Pedal",
                    "Dificuldade rítmica", "Leitura Clave Sol", "Leitura Clave Fá",
                    "Articulação/Fraseado", "Não estudou método", "Sem dificuldades"
                ]
            else:
                st.subheader("📚 Dificuldades Teóricas")
                lista_dif = ["Leitura rítmica", "Leitura métrica", "Afinação Solfejo", "Teoria básica", "Exercícios incompletos", "Sem dificuldades"]

            cols = st.columns(2)
            for i, d in enumerate(lista_dif):
                if cols[i % 2].checkbox(d, key=f"f_{i}"): selecionadas.append(d)
            
            l_hj = st.text_input("Lição dada hoje:")
            p_m = st.text_input("Para casa (Método):")
            p_a = st.text_input("Para casa (Apostila):")
            obs_f = st.text_area("Relato Pedagógico (Análise):")

            if st.button("💾 SALVAR AULA", type="primary"):
                sucesso = True
                for aluna in check_alunas:
                    res = db_save_historico({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                        "Licao": l_hj, "Dificuldades": selecionadas, "Obs": obs_f,
                        "Home_M": p_m, "Home_A": p_a, "Instrutora": instr_sel
                    })
                    if not res: sucesso = False
                if sucesso:
                    st.success("Registro de aula salvo com sucesso!")
                    st.balloons()
        else:
            st.info("Você não tem aula agendada neste horário.")
    else:
        st.error("Rodízio não encontrado para esta data.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica - Vila Verde")
    from PIL import Image, ImageDraw, ImageFont
    import io

    if "analises_fixas_salvas" not in st.session_state:
        st.session_state.analises_fixas_salvas = {}
    
    if not historico_geral:
        st.info("Aguardando registros no histórico para iniciar as análises.")
    else:
        df_geral = pd.DataFrame(historico_geral)
        todas_alunas = sorted(df_geral["Aluna"].unique())
        
        # --- FILTROS DE NAVEGAÇÃO ---
        c1, c2, c3 = st.columns([2, 2, 2])
        aluna_sel = c1.selectbox("Selecione a Aluna:", todas_alunas)
        periodo_tipo = c2.selectbox("Tipo de Período:", ["Diário", "Mensal", "Bimestral", "Semestral", "Anual"])
        data_ini_ref = c3.date_input("Data Inicial da Análise:") 

        # Identificador único para o congelamento
        id_analise = f"{aluna_sel}_{data_ini_ref}_{periodo_tipo}"
        
        # Filtragem por data
        from datetime import timedelta
        df_geral['dt_obj'] = pd.to_datetime(df_geral['Data'], format='%d/%m/%Y').dt.date
        delta_dias = {"Diário":0, "Mensal":30, "Bimestral":60, "Semestral":180, "Anual":365}[periodo_tipo]
        d_fim = data_ini_ref + timedelta(days=delta_dias)
        
        # Filtro da Aluna no Período
        df_f = df_geral[(df_geral["Aluna"] == aluna_sel) & (df_geral["dt_obj"] >= data_ini_ref) & (df_geral["dt_obj"] <= d_fim)]

        if not df_f.empty:
            df_aulas = df_f[df_f["Tipo"] == "Aula"].copy()
            df_ch = df_f[df_f["Tipo"] == "Chamada"]

            # --- 1. GRÁFICOS DE DESEMPENHO ---
            st.subheader("📈 Evolução e Frequência")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if not df_aulas.empty:
                    def calc_nota(txt):
                        if "Sem dificuldades" in str(txt): return 100
                        return max(0, 100 - (len(str(txt).split(",")) * 12))
                    df_aulas['Nota'] = df_aulas['Dificuldades'].apply(calc_nota)
                    st.write("**Desenvoltura Técnica por Matéria (%)**")
                    st.bar_chart(df_aulas.groupby('Materia')['Nota'].mean())
            with col_g2:
                if not df_ch.empty:
                    st.write("**Status de Presença (P/F/J)**")
                    st.bar_chart(df_ch["Status"].value_counts())

            st.divider()

            # --- 2. ANÁLISE DETALHADA (CONGELADA) ---
            if id_analise in st.session_state.analises_fixas_salvas:
                d = st.session_state.analises_fixas_salvas[id_analise]
                
                with st.container(border=True):
                    st.markdown(f"### 📋 RELATÓRIO CONSOLIDADO: {aluna_sel}")
                    c_m1, c_m2, c_m3 = st.columns(3)
                    c_m1.metric("Aulas Realizadas", d['qtd_aulas'])
                    c_m2.metric("Frequência Real", f"{d['freq']:.0f}%")
                    c_m3.metric("Última Lição", d['ultima_licao'])

                    st.markdown("---")
                    col_ped1, col_ped2 = st.columns(2)
                    with col_ped1:
                        st.error(f"**⚠️ POSTURA E TÉCNICA:**\n{d['difs_tecnica']}")
                        st.warning(f"**🎵 RITMO E TEORIA:**\n{d['difs_ritmo']}")
                    with col_ped2:
                        st.info(f"**💡 DICA PRÓXIMA AULA:**\n{d['dicas']}")
                        st.success(f"**🎯 METAS PARA BANCA:**\n{d['banca']}")

                # Geração da Imagem PNG
                img = Image.new('RGB', (900, 700), color=(255, 255, 255))
                canvas = ImageDraw.Draw(img)
                txt_img = f"GEM VILA VERDE - RELATORIO PEDAGOGICO\nAluna: {aluna_sel}\nPeriodo: {data_ini_ref} a {d_fim}\n\n"
                txt_img += f"Aulas: {d['qtd_aulas']} | Freq: {d['freq']:.0f}% | Licao: {d['ultima_licao']}\n\n"
                txt_img += f"TECNICA: {d['difs_tecnica']}\n\nTEORIA: {d['difs_ritmo']}\n\nMETAS BANCA: {d['banca']}"
                canvas.text((40, 40), txt_img, fill=(0, 0, 0))
                
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.download_button("📥 Baixar Relatório (PNG)", buf.getvalue(), f"Relatorio_{aluna_sel}.png", "image/png")
                
                if st.button("🗑️ Gerar Nova Análise"):
                    del st.session_state.analises_fixas_salvas[id_analise]
                    st.rerun()
            else:
                if st.button("✨ GERAR E FIXAR ANÁLISE COMPLETA"):
                    def filtrar_dif(palavras):
                        achadas = [d for d in df_aulas['Dificuldades'].astype(str) if any(p in d.lower() for p in palavras)]
                        return ", ".join(set(achadas)) if achadas else "Nenhuma dificuldade registrada."

                    st.session_state.analises_fixas_salvas[id_analise] = {
                        "qtd_aulas": len(df_aulas),
                        "freq": (len(df_ch[df_ch["Status"] == "P"]) / len(df_ch) * 100) if len(df_ch) > 0 else 0,
                        "ultima_licao": df_aulas.iloc[0]['Licao'] if not df_aulas.empty else "N/A",
                        "difs_tecnica": filtrar_dif(["postura", "punho", "dedo", "falange", "articulação", "pedal"]),
                        "difs_ritmo": filtrar_dif(["metrônomo", "rítmica", "clave", "solfejo", "teoria"]),
                        "dicas": "Focar em exercícios de independência e firmar o tempo.",
                        "banca": "Conferir postura de punho e articulação dos dedos nos hinos."
                    }
                    st.rerun()

            st.divider()

            # --- 3. LOGS DETALHADOS (HISTÓRICO BRUTO) ---
            st.subheader("📂 Detalhamento Técnico (Logs de Atividade)")
            
            # Organiza os logs para mostrar o que a professora escreveu em cada aula
            if not df_aulas.empty:
                st.write("**Histórico de Aulas e Lições:**")
                # Seleciona apenas colunas relevantes para o log pedagógico
                df_log_aulas = df_aulas[['Data', 'Materia', 'Licao', 'Dificuldades', 'Obs', 'Instrutora', 'Home_M', 'Home_A']]
                st.dataframe(df_log_aulas, use_container_width=True)
            
            if not df_ch.empty:
                st.write("**Histórico de Frequência (Secretaria):**")
                df_log_freq = df_ch[['Data', 'Status']]
                st.table(df_log_freq)

        else:
            st.error("Nenhum dado encontrado para esta aluna no período selecionado.")
