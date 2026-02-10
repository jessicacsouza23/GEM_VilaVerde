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

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide")

# Inicialização de Variáveis de Segurança
historico_geral = []
calendario_raw = []

# --- 2. CONEXÃO IA COM ECONOMIA DE QUOTA (CACHE) ---
@st.cache_resource(show_spinner=False)
def inicializar_ia_economica():
    try:
        if "GOOGLE_API_KEY" not in st.secrets: return None, "Chave ausente."
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Lista modelos, mas não faz chamadas de teste desnecessárias
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name), m.name
        return None, "Sem modelo compatível."
    except Exception as e: 
        if "429" in str(e): return None, "Cota diária esgotada (Limite de 20/dia). Tente novamente em alguns minutos."
        return None, str(e)

model, status_ia = inicializar_ia_economica()

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erro Supabase: {e}")

# --- 3. FUNÇÕES DE DADOS ---
@st.cache_data(ttl=60)
def carregar_dados_globais():
    try:
        h = supabase.table("historico_geral").select("*").execute()
        c = supabase.table("calendario").select("*").execute()
        return h.data, c.data
    except:
        return [], []

historico_geral, calendario_raw = carregar_dados_globais()
    
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

def filtrar_por_periodo(df, periodo):
    hoje = datetime.now().date()
    if periodo == "Dia": return df[df['dt_obj'] == hoje]
    elif periodo == "Mês": return df[df['dt_obj'] >= (hoje - timedelta(days=30))]
    elif periodo == "Bimestre": return df[df['dt_obj'] >= (hoje - timedelta(days=60))]
    elif periodo == "Semestre": return df[df['dt_obj'] >= (hoje - timedelta(days=180))]
    elif periodo == "Ano": return df[df['dt_obj'] >= (hoje - timedelta(days=365))]
    return df # Geral
    
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
        
        # 1. Seleção da Data
        data_ch_sel = st.selectbox("Selecione a Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_chamada_unica")
        presenca_padrao = st.toggle("Marcar todas como Presente por padrão", value=True)
        st.write("---")
        
        registros_chamada = []
        alunas_lista = sorted([a for l in TURMAS.values() for a in l])
        
        # 2. Loop Único para construir a lista de chamada
        for idx, aluna in enumerate(alunas_lista):
            col1, col2, col3 = st.columns([2, 3, 3])
            
            col1.write(f"**{aluna}**")
            
            # Chave ÚNICA combinando índice, nome e data para evitar DuplicateKey
            chave_status = f"status_{idx}_{aluna}_{data_ch_sel}"
            
            status = col2.radio(
                f"Status {aluna}", 
                ["Presente", "Ausente", "Justificada"], 
                index=0 if presenca_padrao else 1, 
                key=chave_status, 
                horizontal=True, 
                label_visibility="collapsed"
            )
            
            motivo = ""
            if status == "Justificada":
                # Chave ÚNICA para o input de motivo
                chave_motivo = f"motivo_input_{idx}_{aluna}_{data_ch_sel}"
                motivo = col3.text_input(
                    "Motivo justificativa", 
                    key=chave_motivo, 
                    placeholder="Por que justificou?", 
                    label_visibility="collapsed"
                )
            
            # Adiciona à lista que será salva
            registros_chamada.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        st.write("---")
        
        # 3. Botão de Salvamento (FORA DO LOOP para processar todas as alunas de uma vez)
        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            novos_registros = []
            
            # Como data_ch_sel já vem formatada do selectbox como string, usamos ela direto
            for reg in registros_chamada:
                novos_registros.append({
                    "Data": data_ch_sel,
                    "Aluna": reg["Aluna"],
                    "Tipo": "Chamada",
                    "Status": reg["Status"],
                    "Observacao": reg["Motivo"],
                    "Licao_Atual": "Presença em Aula",
                    "Dificuldades": []
                })
        
            try:
                # Salva no Supabase
                supabase.table("historico_geral").insert(novos_registros).execute()
                
                # Limpa cache para atualizar os gráficos de IA
                st.cache_data.clear()
                
                st.success(f"✅ Chamada de {data_ch_sel} salva com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar no banco de dados: {e}")
        
   
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

        st.divider()
    
# BLOCO DE LIMPEZA (Alinhado com o st.header acima)
with st.expander("🚨 ÁREA DE PERIGO - Limpeza de Banco de Dados"):
    st.warning("Atenção: As ações abaixo apagam permanentemente os dados do sistema.")
    
    confirmar_limpeza = st.checkbox("Eu entendo que esta ação não pode ser desfeita.", key="conf_limpeza")
    
    if confirmar_limpeza:
        col1, col2 = st.columns(2)
        
        # 1. Limpar Histórico, Presenças e Lições
        if col1.button("🗑️ Apagar Lições e Presenças", use_container_width=True):
            try:
                supabase.table("historico_geral").delete().neq("Aluna", "").execute()
                st.success("✅ Histórico limpo!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro: {e}")

        # 2. Limpar Análises da IA
        if col2.button("🗑️ Apagar Análises da IA", use_container_width=True):
            try:
                supabase.table("analises_congeladas").delete().neq("aluna", "").execute()
                st.success("✅ Memória de IA limpa!")
            except Exception as e:
                st.error(f"Erro: {e}")

        st.write("---")
        
        # 3. Limpar Rodízio
        if st.button("🗑️ Resetar Calendário de Rodízio", use_container_width=True):
            try:
                # Verifique se o nome da sua tabela é 'calendario_geral' ou 'calendario_escalas'
                supabase.table("calendario_geral").delete().neq("id", "").execute()
                st.success("✅ Rodízio apagado!")
            except Exception as e:
                st.error(f"Erro: {e}")
                    
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
            esta_na_escala = any(instr_sel in str(atend) for atend in escala_dia for atend in atend.values())
    
            if not esta_na_escala:
                st.divider()
                st.balloons()
                st.markdown(f'<div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center; border: 2px dashed #ff4b4b;"><h2 style="color: #ff4b4b;">🌸 Hoje não, Irmã {instr_sel}!</h2><p style="font-size: 1.2em;">Hoje é sua folga. Aproveite o seu dia!</p></div>', unsafe_allow_html=True)
            else:
                h_sel = st.radio("Selecione o Horário:", HORARIOS, horizontal=True)
                atendimento = next((r for r in escala_dia if instr_sel in str(r.get(h_sel, ""))), None)
                
                if atendimento:
                    local_info = atendimento[h_sel]
                    aluna_referencia = atendimento['Aluna']
                    turma_aluna = atendimento.get('Turma', 'Turma 1')
    
                    # Identifica se é aula coletiva (Salas 8 ou 9)
                    is_coletiva = "SALA 8" in local_info or "SALA 9" in local_info
                    tipo = "Teoria" if "SALA 8" in local_info else "Solfejo" if "SALA 9" in local_info else "Prática"
                    dif_lista = DIF_TEORIA if tipo == "Teoria" else DIF_SOLFEJO if tipo == "Solfejo" else DIF_PRATICA
                    label_lic = f"Desempenho {tipo}"
    
                    st.success(f"📍 {local_info} | 👤 Referência: {aluna_referencia}")
    
                    # --- SEÇÃO DE CHECKLIST DE ALUNAS ---
                    alunas_selecionadas = []
                    
                    if is_coletiva:
                        st.markdown("### 👥 Chamada da Turma")
                        st.caption("Marque as alunas que estão presentes nesta aula:")
                        alunas_turma = TURMAS.get(turma_aluna, [aluna_referencia])
                        
                        # Cria colunas para os checkboxes de alunas não ocuparem muito espaço vertical
                        cols_alu = st.columns(3)
                        for idx_a, aluna in enumerate(alunas_turma):
                            # Se for a aluna que está na escala principal, já vem marcada
                            default_val = True if aluna == aluna_referencia else True
                            if cols_alu[idx_a % 3].checkbox(aluna, value=default_val, key=f"check_alu_{idx_a}"):
                                alunas_selecionadas.append(aluna)
                    else:
                        alunas_selecionadas = [aluna_referencia]
    
                    # --- FORMULÁRIO DE LANÇAMENTO ---
                    with st.form("f_aula_prof", clear_on_submit=True):
                        st.subheader(f"📝 Registro de {tipo}")
                        
                        lic_vol = st.selectbox(f"{label_lic} - Lição/Volume:", OPCOES_LICOES_NUM)
                        if lic_vol == "Outro": lic_vol = st.text_input("Especifique:")
                        
                        st.markdown("**Dificuldades Detectadas:**")
                        cols_dif = st.columns(2)
                        difs_selecionadas = []
                        for i, d in enumerate(dif_lista):
                            target_col = cols_dif[0] if i < len(dif_lista)/2 else cols_dif[1]
                            if target_col.checkbox(d, key=f"diff_{i}"):
                                difs_selecionadas.append(d)
                        
                        obs_aula = st.text_area("Observações Técnicas para a Turma:")
                        casa_f = st.text_input("Tarefa para casa (Todas):")
    
                        if st.form_submit_button("❄️ CONGELAR E SALVAR AULA"):
                            if not alunas_selecionadas:
                                st.error("⚠️ Nenhuma aluna selecionada para o registro!")
                            else:
                                for aluna in alunas_selecionadas:
                                    db_save_historico({
                                        "Aluna": aluna, "Tipo": f"Aula_{tipo}", "Data": data_prof_str,
                                        "Instrutora": instr_sel, "Licao_Atual": lic_vol, 
                                        "Dificuldades": difs_selecionadas, "Observacao": obs_aula, "Licao_Casa": casa_f
                                    })
                                st.success(f"✅ Aula salva para: {', '.join(alunas_selecionadas)}")
                                st.cache_data.clear()
                else:
                    st.info(f"Irmã {instr_sel}, sem agenda para este horário.")
    else:
        st.error("Rodízio não encontrado.")
            
# ==========================================
# MÓDULO ANÁLISE DE IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.title("📊 Análise Pedagógica e Rodízio")
    
    # 1. SELEÇÃO DA ALUNA
    alu_ia = st.selectbox("Selecione a Aluna:", ALUNAS_LISTA)
    
    # 2. DEFINIÇÃO DO TIPO DE PERÍODO
    tipo_periodo = st.radio(
        "Selecione o tipo de análise:",
        ["Diária", "Mensal", "Bimestral", "Semestral", "Anual", "Geral"],
        horizontal=True
    )
    
    df = pd.DataFrame(historico_geral)
    df['dt_obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce').dt.date
    df_aluna = df[df["Aluna"] == alu_ia]

    # 3. FILTROS ESPECÍFICOS POR SELEÇÃO
    df_f = pd.DataFrame() # Inicializa vazio
    
    if tipo_periodo == "Diária":
        datas_disponiveis = sorted(df_aluna['dt_obj'].unique(), reverse=True)
        dia_sel = st.selectbox("Escolha o dia da aula:", datas_disponiveis)
        df_f = df_aluna[df_aluna['dt_obj'] == dia_sel]
        
    elif tipo_periodo == "Mensal":
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_sel = st.selectbox("Escolha o mês:", meses, index=datetime.now().month - 1)
        # Filtra pelo mês e ano atual
        df_f = df_aluna[(pd.to_datetime(df_aluna['dt_obj']).dt.month == meses.index(mes_sel) + 1) & 
                        (pd.to_datetime(df_aluna['dt_obj']).dt.year == 2026)]
        
    elif tipo_periodo == "Bimestral":
        bim_sel = st.selectbox("Escolha o Bimestre:", ["1º Bimestre (Jan/Fev)", "2º Bimestre (Mar/Abr)", "3º Bimestre (Mai/Jun)", "4º Bimestre (Jul/Ago)", "5º Bimestre (Set/Out)", "6º Bimestre (Nov/Dez)"])
        # Lógica de meses para cada bimestre
        mapa_bim = {"1º Bimestre (Jan/Fev)": [1,2], "2º Bimestre (Mar/Abr)": [3,4], "3º Bimestre (Mai/Jun)": [5,6], "4º Bimestre (Jul/Ago)": [7,8], "5º Bimestre (Set/Out)": [9,10], "6º Bimestre (Nov/Dez)": [11,12]}
        df_f = df_aluna[pd.to_datetime(df_aluna['dt_obj']).dt.month.isin(mapa_bim[bim_sel])]
        
    elif tipo_periodo == "Semestral":
        sem_sel = st.selectbox("Escolha o Semestre:", ["1º Semestre", "2º Semestre"])
        meses_sem = [1,2,3,4,5,6] if sem_sel == "1º Semestre" else [7,8,9,10,11,12]
        df_f = df_aluna[pd.to_datetime(df_aluna['dt_obj']).dt.month.isin(meses_sem)]
        
    elif tipo_periodo == "Anual":
        ano_sel = st.selectbox("Escolha o Ano:", [2025, 2026, 2027], index=1)
        df_f = df_aluna[pd.to_datetime(df_aluna['dt_obj']).dt.year == ano_sel]
        
    else: # Geral
        df_f = df_aluna

    # --- EXIBIÇÃO DOS RESULTADOS ---
    if df_f.empty:
        st.info(f"Nenhum registro encontrado para {alu_ia} neste período.")
    else:
        # Indicadores Visuais (KPIs)
        total = len(df_f)
        aprov = len(df_f[df_f['Status'] == "Realizadas - sem pendência"])
        perc = (aprov/total*100) if total > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Registros", total)
        c2.metric("Aproveitamento", f"{perc:.1f}%")
        c3.metric("Faltas/Pendências", len(df_f[df_f['Status'] != "Realizadas - sem pendência"]))

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df_f, names='Tipo', hole=0.5, title="Áreas Focadas"), use_container_width=True)
        with g2:
            difs = [d for sub in df_f['Dificuldades'].dropna() for d in sub if d != "Não apresentou dificuldades"]
            if difs:
                df_d = pd.Series(difs).value_counts().reset_index()
                st.plotly_chart(px.bar(df_d.head(5), x=0, y='index', orientation='h', title="Top Dificuldades"), use_container_width=True)

        # --- RODÍZIO LIMPO (Usando a alu_ia selecionada) ---
        st.markdown("---")
        st.subheader("🔄 Escala para a Próxima Aula")
        
        proxima_aula, proxima_prof = "Não definida", "Não definida"
        if calendario_raw:
            cal_df = pd.DataFrame(calendario_raw)
            cal_df['dt_format'] = pd.to_datetime(cal_df['id'], format='%d/%m/%Y', errors='coerce').dt.date
            futuros = cal_df[cal_df['dt_format'] >= datetime.now().date()].sort_values('dt_format')
            
            if not futuros.empty:
                proxima_aula = futuros.iloc[0]['id']
                escala_bruta = futuros.iloc[0]['escala']
                if isinstance(escala_bruta, list):
                    dados_aluna = next((item for item in escala_bruta if item.get('Aluna') == alu_ia), None)
                    if dados_aluna:
                        proxima_prof = f"**H2:** {dados_aluna.get('09h35 (H2)')} | **H3:** {dados_aluna.get('10h10 (H3)')} | **H4:** {dados_aluna.get('10h45 (H4)')}"
        
        st.info(f"📍 **Próxima Aula:** {proxima_aula}")
        st.success(f"👩‍🏫 **Professoras de {alu_ia}:** {proxima_prof}")

       # --- 🚀 SISTEMA DE ANÁLISE COM MEMÓRIA (CACHE NO BANCO) ---
        st.markdown("---")
        st.subheader("📝 Relatório Pedagógico Congelado")

        # Função para buscar análise já existente
        def buscar_analise_salva(aluna, periodo):
            try:
                res = supabase.table("analises_congeladas")\
                    .select("*")\
                    .eq("aluna", aluna)\
                    .eq("periodo", periodo)\
                    .order("data_geracao", descending=True)\
                    .limit(1).execute()
                return res.data[0] if res.data else None
            except: return None

        # Tenta carregar do banco primeiro
        analise_existente = buscar_analise_salva(alu_ia, tipo_periodo)

        if analise_existente:
            st.success(f"✅ Análise carregada da memória (Salva em: {analise_existente['data_geracao'][:10]})")
            st.markdown(analise_existente['conteudo'])
            
            if st.button("🔄 Gerar Nova (Atualizar com IA)"):
                # Se clicar aqui, ele ignora o cache e força a IA a rodar (cuidado com a cota!)
                analise_existente = None 
                
        # --- 🔄 LÓGICA DE RODÍZIO FILTRADA (PROTEGIDA) ---
        st.markdown("---")
        st.subheader("🔄 Informação de Transferência")
        
        # 1. Garantimos que a variável 'alu_ia' existe antes de prosseguir
        if 'alu_ia' in locals() or 'alu_ia' in globals():
            proxima_aula = "Não agendada"
            proxima_prof = "Não definida"
        
            if calendario_raw:
                try:
                    cal_df = pd.DataFrame(calendario_raw)
                    # Converte 'id' (data) para objeto de data para comparar
                    cal_df['dt_format'] = pd.to_datetime(cal_df['id'], format='%d/%m/%Y', errors='coerce').dt.date
                    
                    # Pega apenas datas futuras ou hoje
                    hoje_ref = datetime.now().date()
                    futuros = cal_df[cal_df['dt_format'] >= hoje_ref].sort_values('dt_format')
                    
                    if not futuros.empty:
                        proxima_aula = futuros.iloc[0]['id']
                        escala_bruta = futuros.iloc[0]['escala']
                        
                        # Se a escala for uma lista de dicionários (o seu caso)
                        if isinstance(escala_bruta, list):
                            # Procuramos a aluna selecionada dentro da lista da secretaria
                            dados_aluna = next((item for item in escala_bruta if item.get('Aluna') == alu_ia), None)
                            
                            if dados_aluna:
                                h2 = dados_aluna.get('09h35 (H2)', 'N/A')
                                h3 = dados_aluna.get('10h10 (H3)', 'N/A')
                                h4 = dados_aluna.get('10h45 (H4)', 'N/A')
                                proxima_prof = f"**H2:** {h2} | **H3:** {h3} | **H4:** {h4}"
                            else:
                                proxima_prof = "Aluna não encontrada na escala desta data."
                        else:
                            proxima_prof = "Escala não está no formato de lista esperado."
                except Exception as e:
                    proxima_prof = f"Erro ao processar escala: {e}"
        
            # Exibição Final
            st.info(f"📍 **Próxima Aula:** {proxima_aula}")
            st.success(f"👩‍🏫 **Escala de {alu_ia}:** {proxima_prof}")
        else:
            st.warning("⚠️ Selecione uma aluna acima para visualizar a escala de rodízio.")
        
        # Se não existe análise ou se pediu para atualizar
        if not analise_existente:
            if st.button("✨ GERAR ANÁLISE COMPLETA (IA)"):
                if model:
                    try:
                        with st.spinner("IA processando relatório técnico..."):
                            dados_texto = df_f[['Data', 'Tipo', 'Licao_Atual', 'Dificuldades', 'Observacao']].to_string(index=False)
                            
                            prompt = f"""
                            Aja como Coordenadora Pedagógica Master. Gere uma análise técnica para: {proxima_prof}.
                            ALUNA: {alu_ia} | PERÍODO: {tipo_periodo} | PRÓXIMA AULA: {proxima_aula}.

                            ESTRUTURA OBRIGATÓRIA:
                            1. 🎹 POSTURA E TÉCNICA: Detalhes de dedilhado e forma.
                            2. 🥁 RITMO: Uso do metrônomo e divisão.
                            3. 📖 TEORIA: Progresso nos métodos.
                            4. 🏠 SECRETARIA: Resumo de faltas/pendências.
                            5. 🎯 METAS: O que cobrar em {proxima_aula}.
                            6. 🏛️ BANCA: Dicas para o exame semestral.

                            DADOS: {dados_texto}
                            """
                            
                            res = model.generate_content(prompt)
                            texto_gerado = res.text
                            
                            # SALVAR NO SUPABASE PARA NÃO GASTAR COTA DE NOVO
                            nova_analise = {
                                "aluna": alu_ia,
                                "periodo": tipo_periodo,
                                "conteudo": texto_gerado,
                                "professoras_escala": proxima_prof
                            }
                            supabase.table("analises_congeladas").insert(nova_analise).execute()
                            
                            st.markdown(texto_gerado)
                            st.balloons()
                            st.rerun() # Recarrega para mostrar como "carregada da memória"

                    except Exception as e:
                        if "429" in str(e) or "ResourceExhausted" in str(e):
                            st.error("⚠️ Cota atingida. Use as análises já salvas ou aguarde 1 minuto.")
                        else:
                            st.error(f"Erro: {e}")




with st.sidebar.expander("ℹ️ Limites da IA"):
    st.write("• **Limite:** 15 análises por minuto.")
    st.write("• **Custo:** R$ 0,00 (Plano Free).")
    st.caption("Se aparecer erro 429, aguarde 60 segundos.")













