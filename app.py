import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from supabase import create_client, Client
import io
from PIL import Image, ImageDraw
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# --- 1. CONFIGURAÇÕES E CONEXÕES SEGURAS ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide")

# Carrega chaves dos Secrets do Streamlit
try:
    GENAI_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    
    # Inicializa IA
    genai.configure(api_key=GENAI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Inicializa Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"❌ Erro de Configuração: Verifique os Secrets do Streamlit. Detalhe: {e}")
    st.stop()

# Conexão Supabase
# SUPABASE_URL = "https://ixaqtoyqoianumczsjai.supabase.co"
# SUPABASE_KEY = "sb_publishable_HwYONu26I0AzTR96yoy-Zg_nVxTlJD1"

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

# --- 3. DEFINIÇÃO DE VARIÁVEIS GLOBAIS (FIX PARA NAMEERROR) ---
data_hj = datetime.now().strftime("%d/%m/%Y")
calendario_db = db_get_calendario()

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
OPCOES_LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# --- 3. INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# Listas de Dificuldades (Restauradas conforme seu envio)
DIF_PRATICA = ["Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos dos métodos", 
               "Dificuldade ritmica", "Dificuldade em distinguir os nomes das figuras ritmicas", "Está adentrando às teclas", 
               "Dificuldade com a postura (costas, ombros e braços)", "Está deixando o punho alto ou baixo", "Não senta no centro da banqueta", 
               "Está quebrando as falanges", "Unhas muito compridas", "Dificuldade em deixar os dedos arredondados", 
               "Esquece de colocar o pé direito no pedal de expressão", "Faz movimentos desnecessários com o pé esquerdo na pedaleira", 
               "Dificuldade com o uso do metrônomo", "Estuda sem o metrônomo", "Dificuldades em ler as notas na clave de sol", 
               "Dificuldades em ler as notas na clave de fá", "Não realizou as atividades da apostila", "Dificuldade em fazer a articulação ligada e semiligada",
               "Dificuldade com as respirações", "Dificuldade com as respirações sobre passagem", 
               "Dificuldades em recurso de dedilhado (passagem, alargamento, contração, mudança ou substituição)", "Dificuldade em fazer nota de apoio", 
               "Não apresentou dificuldades"]

DIF_TEORIA = ["Não assistiu os vídeos complementares", "Não apresentou dificuldades", "Não participou da aula", "Dificuldade em utilizar o metrônomo", 
              "Não compreende o que é música na igreja", "Não compreende o que é música", "Não compreende o que é som", "Dificuldade em compreender os elementos da música", 
              "Dificuldade em compreender as propriedades do som", "Dificuldade de leitura de clave de sol", "Dificuldade de leitura de clave de fá", 
              "Não realizou as atividades da apostila", "Não estudou", "Não realizou as atividades para casa", "Ficou dispersa durante a aula", 
              "Não realizou as atividades durante a aula", "Não trouxe o material necessário", "Demonstra insegurança ao lidar com o conteúdo"]

DIF_SOLFEJO = ["Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol", "Dificuldades em ler as notas na clave de fá", 
               "Está com dificuldades no uso do metrônomo", "Estuda em metrônomo", "Não realizou as atividades", "Dificuldade em leitura ritmica", 
               "Dificuldades em leitura métrica", "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão", 
               "Dificuldades na ordem das notas, ascendente e descendente", "Não realizou as atividades da apostila", "Não estudou nada", 
               "Estudou de forma insatisfatória", "Não apresentou dificuldades"]

# --- FUNÇÃO PARA FILTRAR POR PERÍODO ---
def filtrar_por_periodo(df, aluna, periodo, data_especifica=None):
    if df.empty:
        return df
    
    # Converte coluna Data para datetime
    df['dt_obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
    df_aluna = df[df["Aluna"] == aluna].sort_values("dt_obj", ascending=False)
    
    hoje = datetime.now()
    
    if periodo == "Dia" and data_especifica:
        return df_aluna[df_aluna['dt_obj'].dt.date == data_especifica]
    elif periodo == "Mês":
        return df_aluna[df_aluna['dt_obj'] > (hoje - timedelta(days=30))]
    elif periodo == "Bimestre":
        return df_aluna[df_aluna['dt_obj'] > (hoje - timedelta(days=60))]
    elif periodo == "Semestre":
        return df_aluna[df_aluna['dt_obj'] > (hoje - timedelta(days=180))]
    elif periodo == "Ano":
        return df_aluna[df_aluna['dt_obj'] > (hoje - timedelta(days=365))]
    return df_aluna # Geral

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

    # --- ABA 2: CHAMADA GERAL ---
    with tab_cham:
        st.subheader("📍 Chamada Geral")
        data_ch_sel = st.selectbox("Selecione a Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_chamada_unica")
        presenca_padrao = st.toggle("Marcar todas como Presente por padrão", value=True)
        st.write("---")
        registros_chamada = []
        alunas_lista = sorted([a for l in TURMAS.values() for a in l])
        for aluna in alunas_lista:
            col1, col2, col3 = st.columns([2, 3, 3])
            col1.write(f"**{aluna}**")
            status = col2.radio(f"Status {aluna}", ["Presente", "Falta", "Justificada"], index=0 if presenca_padrao else 1, key=f"status_{aluna}_{data_ch_sel}", horizontal=True, label_visibility="collapsed")
            motivo = ""
            if status == "Justificada":
                motivo = col3.text_input(f"Motivo justificativa", key=f"motivo_{aluna}_{data_ch_sel}", placeholder="Informe o motivo...", label_visibility="collapsed")
            registros_chamada.append({"Aluna": aluna, "Status": status, "Motivo": motivo})
        
        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            for reg in registros_chamada:
                st.session_state.historico_geral.append({"Data": data_ch_sel, "Aluna": reg["Aluna"], "Tipo": "Chamada", "Status": reg["Status"], "Motivo": reg["Motivo"]})
            st.success(f"Chamada de {data_ch_sel} salva!")
   
    with tab_lição:
        st.subheader("📝 Controle de Lições e Pendências")
        
        c1, c2 = st.columns(2)
        sec_resp = c1.selectbox("Secretária responsável:", SECRETARIAS_LISTA)
        data_hj = c2.date_input("Data de Hoje:", datetime.now())
        
        alu_sel = st.selectbox("Selecione a Aluna:", ["Selecione..."] + ALUNAS_LISTA)
        
        if alu_sel != "Selecione...":
            df_hist = pd.DataFrame(historico_geral)
            if not df_hist.empty:
                df_hist['dt_comparar'] = pd.to_datetime(df_hist['Data'], format='%d/%m/%Y').dt.date
                
                # 1. Busca registros com pendência
                pendentes_bruto = df_hist[
                    (df_hist["Aluna"] == alu_sel) & 
                    (df_hist["Tipo"] == "Controle_Licao") & 
                    (df_hist["Status"].isin(["Realizada - devolvida para refazer", "Não realizada"]))
                ].sort_values("dt_comparar", ascending=False)

                # 2. Busca registros de sucesso
                sucessos = df_hist[
                    (df_hist["Aluna"] == alu_sel) & 
                    (df_hist["Status"] == "Realizadas - sem pendência")
                ]
                
                # 3. Filtra apenas o que NÃO foi resolvido ainda
                pendencias_reais = []
                for _, p in pendentes_bruto.iterrows():
                    resolvida = sucessos[
                        (sucessos["Categoria"] == p["Categoria"]) & 
                        (sucessos["Licao_Detalhe"] == p["Licao_Detalhe"]) & 
                        (sucessos["dt_comparar"] >= p["dt_comparar"])
                    ]
                    if resolvida.empty:
                        pendencias_reais.append(p)

                # --- EXIBIÇÃO DAS PENDÊNCIAS COM BOTÃO DE RESOLUÇÃO ---
                if pendencias_reais:
                    st.error("🚨 LIÇÕES PENDENTES - ATUALIZE ABAIXO SE ENTREGUE HOJE")
                    for p in pendencias_reais:
                        with st.container(border=True):
                            col_info, col_acao = st.columns([2, 1])
                            
                            with col_info:
                                st.markdown(f"📖 **{p['Categoria']}**")
                                st.markdown(f"**Lição:** {p.get('Licao_Detalhe', '---')}")
                                st.caption(f"📅 Primeira correção em: {p['Data']} | Motivo: {p['Status']}")
                                st.info(f"Obs Antiga: {p.get('Observacao', '-')}")
                            
                            with col_acao:
                                # Mini formulário para resolver a pendência específica
                                with st.expander("✅ Resolver esta pendência"):
                                    status_resolv = st.selectbox("Nova Situação:", STATUS_LICAO, key=f"st_{p['id']}")
                                    obs_resolv = st.text_area("Observação da entrega:", key=f"obs_{p['id']}")
                                    if st.button("Salvar Atualização", key=f"btn_{p['id']}"):
                                        dados_update = {
                                            "Aluna": alu_sel,
                                            "Tipo": "Controle_Licao",
                                            "Data": data_hj.strftime("%d/%m/%Y"),
                                            "Secretaria": sec_resp,
                                            "Categoria": p["Categoria"],
                                            "Licao_Detalhe": p["Licao_Detalhe"],
                                            "Status": status_resolv,
                                            "Observacao": obs_resolv
                                        }
                                        if db_save_historico(dados_update):
                                            st.success("Salvo com sucesso!")
                                            st.rerun()
                else:
                    st.success("✅ Nenhuma pendência encontrada para esta aluna.")

            st.divider()
            
            # --- FORMULÁRIO PARA NOVAS ATIVIDADES ---
            with st.form("f_nova_atividade", clear_on_submit=True):
                st.markdown("### ✍️ Registrar Nova Atividade (Diferente das Pendências)")
                c_cat, c_det = st.columns([1, 2])
                cat_sel = c_cat.radio("Categoria:", CATEGORIAS_LICAO)
                det_lic = c_det.text_input("Lição / Página:", placeholder="Ex: Lição 02, pág 05")
                
                st.divider()
                status_sel = st.radio("Status hoje:", STATUS_LICAO, horizontal=True)
                obs_hoje = st.text_area("Observação Técnica (p/ Análise IA):")
                
                if st.form_submit_button("❄️ CONGELAR E SALVAR"):
                    sucesso = db_save_historico({
                        "Aluna": alu_sel,
                        "Tipo": "Controle_Licao",
                        "Data": data_hj.strftime("%d/%m/%Y"),
                        "Secretaria": sec_resp,
                        "Categoria": cat_sel,
                        "Licao_Detalhe": det_lic,
                        "Status": status_sel,
                        "Observacao": obs_hoje
                    })
                    if sucesso:
                        st.success("✅ Registro salvo com sucesso!")
                        st.balloons()
                        st.rerun()
                        
# ==========================================
# MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Controle de Desempenho")
    c1, c2 = st.columns(2)
    with c1:
        instr_sel = st.selectbox("Identifique-se:", ["Selecione..."] + PROFESSORAS_LISTA)
    with c2:
        hoje_dt = datetime.now()
        sab_p = hoje_dt + timedelta(days=(5 - hoje_dt.weekday()) % 7)
        data_prof = st.date_input("Data da Aula:", sab_p)
        data_prof_str = data_prof.strftime("%d/%m/%Y")

    if instr_sel != "Selecione...":
        if data_prof_str in calendario_db:
            escala_dia = calendario_db[data_prof_str]
            
            # --- VERIFICAÇÃO DE FOLGA ---
            # Verifica se o nome da professora aparece em QUALQUER horário da escala daquele dia
            esta_na_escala = any(instr_sel in str(atend) for atend in escala_dia for atend in atend.values())

            if not esta_na_escala:
                st.divider()
                st.balloons()
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center; border: 2px dashed #ff4b4b;">
                    <h2 style="color: #ff4b4b;">🌸 Hoje não, Irmã {instr_sel}!</h2>
                    <p style="font-size: 1.2em; color: #31333f;">
                        <b>Hoje é sua folga. Aproveite o seu dia para descansar!</b> ✨
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # --- SE ELA TIVER ESCALA, MOSTRA OS HORÁRIOS ---
                h_sel = st.radio("Selecione o Horário:", HORARIOS, horizontal=True)
                atendimento = next((r for r in escala_dia if instr_sel in str(r.get(h_sel, ""))), None)
                
                if atendimento:
                    aluna_atual = atendimento['Aluna']
                    local_info = atendimento[h_sel]
                    st.success(f"📍 {local_info} | 👤 Aluna: {aluna_atual}")

                    if "SALA 8" in local_info:
                        tipo, dif_lista, label_lic = "Teoria", DIF_TEORIA, "Desempenho Teoria"
                    elif "SALA 9" in local_info:
                        tipo, dif_lista, label_lic = "Solfejo", DIF_SOLFEJO, "Desempenho Solfejo"
                    else:
                        tipo, dif_lista, label_lic = "Prática", DIF_PRATICA, "Prática Instrumental"

                    with st.form("f_aula_prof", clear_on_submit=True):
                        st.subheader(f"Controle de {tipo}")
                        lic_vol = st.selectbox(f"{label_lic} - Lição/Volume:", OPCOES_LICOES_NUM)
                        if lic_vol == "Outro": lic_vol = st.text_input("Especifique:")
                        
                        st.markdown("**Dificuldades Detectadas:**")
                        cols_check = st.columns(2)
                        difs_selecionadas = []
                        for i, d in enumerate(dif_lista):
                            target_col = cols_check[0] if i < len(dif_lista)/2 else cols_check[1]
                            if target_col.checkbox(d, key=f"p_{i}"):
                                difs_selecionadas.append(d)
                        
                        obs_aula = st.text_area("Observações Técnicas:")
                        st.divider()
                        if tipo == "Prática":
                            col_v, col_a = st.columns(2)
                            casa_v = col_v.selectbox("Volume Casa:", ["Nenhum"] + OPCOES_LICOES_NUM)
                            casa_a = col_a.text_input("Apostila Casa:")
                            casa_f = f"Vol: {casa_v} | Apo: {casa_a}"
                        else:
                            casa_f = st.text_input("Tarefa para casa:")

                        if st.form_submit_button("❄️ CONGELAR E SALVAR AULA"):
                            db_save_historico({
                                "Aluna": aluna_atual, "Tipo": f"Aula_{tipo}", "Data": data_prof_str,
                                "Instrutora": instr_sel, "Licao_Atual": lic_vol, 
                                "Dificuldades": difs_selecionadas, "Observacao": obs_aula, "Licao_Casa": casa_f
                            })
                            st.success("✅ Aula salva!")
                else:
                    st.info(f"Irmã {instr_sel}, você não tem aula agendada para o horário de {h_sel}.")
        else:
            st.error("Rodízio não encontrado para esta data.")
            
# ==========================================
# MÓDULO ANÁLISE DE IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica Vila Verde")
    
    if not historico_geral:
        st.warning("⚠️ O banco de dados está vazio.")
    else:
        df = pd.DataFrame(historico_geral)
        df['dt_obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce').dt.date
        
        c1, c2 = st.columns([2,1])
        alu_ia = c1.selectbox("Selecione a Aluna:", ALUNAS_LISTA)
        per_ia = c2.selectbox("Período:", ["Geral", "Dia", "Mês", "Bimestre", "Semestre"])
        
        df_f = df[df["Aluna"] == alu_ia]
        
        if df_f.empty:
            st.info(f"Sem registros para {alu_ia}.")
        else:
            # --- 📈 DASHBOARDS ---
            st.subheader("🎯 Visão de Desempenho")
            g1, g2 = st.columns(2)
            
            with g1:
                # Radar de Equilíbrio
                tipos = df_f['Tipo'].value_counts()
                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=tipos.values,
                    theta=tipos.index,
                    fill='toself'
                ))
                fig_radar.update_layout(title="Foco por Área (Prática/Teoria/Solfejo)")
                st.plotly_chart(fig_radar, use_container_width=True)
                
            with g2:
                # Barras de Dificuldades
                difs = [d for sub in df_f['Dificuldades'].dropna() for d in sub if isinstance(sub, list)]
                if difs:
                    df_d = pd.Series(difs).value_counts().reset_index()
                    df_d.columns = ['Dificuldade', 'Qtd']
                    fig_bar = px.bar(df_d.head(10), x='Qtd', y='Dificuldade', orientation='h', title="Dificuldades Recorrentes")
                    st.plotly_chart(fig_bar, use_container_width=True)

            st.divider()

            # --- 🚀 BOTÃO GERADOR DE RELATÓRIO ---
            if st.button("✨ GERAR ANÁLISE COMPLETA (13 SEÇÕES)"):
                with st.spinner("IA processando dados técnicos e pedagógicos..."):
                    # Formata os dados para a IA entender melhor
                    dados_texto = df_f[['Data', 'Tipo', 'Licao_Atual', 'Dificuldades', 'Observacao']].to_string(index=False)
                    
                    prompt = f"""
                    Você é a Coordenadora Pedagógica Master de Órgão Eletrônico.
                    Analise o histórico da aluna {alu_ia} e gere o relatório pedagógico completo com 13 seções.
                    
                    DADOS:
                    {dados_texto}
                    
                    REQUISITOS:
                    - Separe as dificuldades por: Postura, Técnica, Ritmo e Teoria.
                    - Inclua o resumo da secretaria.
                    - Defina metas mensuráveis.
                    - Dê dicas específicas para a banca semestral.
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("### 📝 Relatório Analítico Final")
                        st.markdown(response.text)
                        st.download_button("📥 Baixar Análise Congelada", response.text, f"Analise_{alu_ia}.txt")
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
