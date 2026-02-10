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
    st.header("👩‍🏫 Painel da Professora")
    instr_sel = st.selectbox("Selecione seu nome:", ["Selecione..."] + PROFESSORAS_LISTA)

    if instr_sel != "Selecione...":
        # --- VERIFICAÇÃO DE ESCALA ---
        if data_hj in calendario_db:
            st.info(f"📅 Hoje: {data_hj}")
            h_sel = st.radio("Selecione o Horário da Aula:", HORARIOS, horizontal=True)
            
            # Busca quem a professora atende neste horário
            atendimento = next((r for r in calendario_db[data_hj] if instr_sel in str(r.get(h_sel, ""))), None)
            
            if atendimento:
                aluna_atual = atendimento['Aluna']
                local_aula = atendimento[h_sel] # Ex: "🎹 SALA 1 | Roberta" ou "📚 SALA 8 | Roberta"
                
                st.success(f"📍 **Local:** {local_aula.split('|')[0]} | **Aluna:** {aluna_atual}")
                
                # Define o Tipo de Aula baseado no Local
                tipo_aula = "Prática"
                dificuldades_lista = DIF_PRATICA
                if "SALA 8" in local_aula: 
                    tipo_aula = "Teoria"
                    dificuldades_lista = DIF_TEORIA
                elif "SALA 9" in local_aula: 
                    tipo_aula = "Solfejo"
                    dificuldades_lista = DIF_SOLFEJO

                st.divider()
                st.subheader(f"📝 Controle de Desempenho - {tipo_aula}")

                with st.form("f_aula_prof", clear_on_submit=True):
                    # --- CAMPOS COMUNS ---
                    lic_vol = st.selectbox("Lição/Volume Atual:", OPCOES_LICOES)
                    if lic_vol == "Outro":
                        lic_vol = st.text_input("Especifique a Lição/Volume:")
                    
                    dif_selecionadas = st.multiselect("Dificuldades Observadas:", dificuldades_lista)
                    obs_aula = st.text_area("Observações Pedagógicas:")

                    # --- CAMPOS EXCLUSIVOS PRÁTICA ---
                    casa_vol = ""
                    casa_apo = ""
                    if tipo_aula == "Prática":
                        c1, c2 = st.columns(2)
                        casa_vol = c1.selectbox("Lição de Casa - Volume:", ["Nenhuma"] + OPCOES_LICOES)
                        casa_apo = c2.text_input("Lição de Casa - Apostila:")
                    else:
                        casa_vol = st.text_input("Lição de Casa:")

                    if st.form_submit_button("❄️ CONGELAR E SALVAR AULA"):
                        dados_aula = {
                            "Aluna": aluna_atual,
                            "Tipo": f"Aula_{tipo_aula}",
                            "Data": data_hj,
                            "Instrutora": instr_sel,
                            "Licao_Atual": lic_vol,
                            "Dificuldades": dif_selecionadas,
                            "Observacao": obs_aula,
                            "Licao_Casa": f"Volume: {casa_vol} | Apo: {casa_apo}" if tipo_aula == "Prática" else casa_vol
                        }
                        if db_save_historico(dados_aula):
                            st.success(f"✅ Aula de {tipo_aula} para {aluna_atual} salva com sucesso!")
                            st.balloons()
            else:
                st.warning("Você não está em escala para este horário.")
        else:
            st.error("O rodízio de hoje ainda não foi gerado pela secretaria.")
            
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

























