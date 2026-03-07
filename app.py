import streamlit as st
import pandas as pd
import calendar
from supabase import create_client, Client
from PIL import Image, ImageDraw
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime, timedelta, date
from fpdf import FPDF
import io
import streamlit as st


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

supabase = None

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()
    
# --- 3. FUNÇÕES DE DADOS ---
@st.cache_data(ttl=60)
def carregar_dados_globais():
    try:
        h = supabase.table("historico_geral").select("*").execute()
        c = supabase.table("calendario").select("*").execute()
        return h.data, c.data
    except:
        return [], []


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
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla", "Renata"]
SECRETARIAS_LISTA = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"]
ALUNAS_LISTA = sorted([
    "Mariana - Vila Araguaia", "Annie - Vila Verde", "Ana Marcela S. - Vila Verde", 
    "Caroline C. - Vila Ré", "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá Velha", 
    "Gabrielly V. - Vila Verde", "Heloísa R. - Vila Verde", "Ingrid M. - Pq do Carmo II", 
    "Júlia Cristina - União de Vila Nova", "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá Velha", 
    "Mellina S. - Jardim Lígia", "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", 
    "Rebeca R. - Vila Ré", "Rebecca A. - Vila Verde", "Rebeka S. - Jardim Lígia", 
    "Sarah S. - Vila Verde", "Vitória A. - Vila Verde", "Vitória Bella T. - Vila Verde"
])

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
STATUS_LICAO = ["Realizadas - sem pendência", "Realizada - devolvida para refazer", "Não realizada"]

TURMAS = {
    "Turma 1": ["Mariana - Vila Araguaia","Rebecca A. - Vila Verde", "Annie - Vila Verde", "Ingrid M. - Pq do Carmo II", "Rebeka S. - Jardim Lígia", 
                "Mellina S. - Jardim Lígia", "Caroline C. - Vila Ré", "Rebeca R. - Vila Ré"],
    "Turma 2": ["Vitória A. - Vila Verde", "Elisa F. - Vila Verde", "Sarah S. - Vila Verde", "Gabrielly V. - Vila Verde", 
                "Emilly O. - Vila Curuçá Velha", "Julya O. - Vila Curuçá Velha"],
    "Turma 3": ["Heloísa R. - Vila Verde", "Ana Marcela S. - Vila Verde", "Vitória Bella T. - Vila Verde", 
                "Júlia S. - Vila Verde", "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", "Júlia Cristina - União de Vila Nova"]
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

def carregar_planejamento():
    try:
        # Busca o registro mais recente do planejamento
        res = supabase.table("planejamento").select("*").order("created_at", descending=True).limit(1).execute()
        if res.data:
            # Retorna a coluna onde você guarda o JSON da escala
            return res.data[0]['dados_escala'] 
        return []
    except:
        return []

def salvar_analise_congelada(aluna, periodo_tipo, periodo_id, conteudo, user_id):
    try:
        supabase.table("analises_congeladas").upsert(
            {
                "aluna": aluna,
                "periodo_tipo": periodo_tipo,
                "periodo_id": periodo_id,
                "conteudo": conteudo,
                "user_id": user_id
            },
            on_conflict=["aluna", "periodo_tipo", "periodo_id"]
        ).execute()

        st.success("✅ Análise congelada salva com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar análise congelada: {e}")

def buscar_analise_congelada(aluna, periodo_tipo, periodo_id):
    try:
        res = supabase.table("analises_congeladas") \
            .select("*") \
            .eq("aluna", aluna) \
            .eq("periodo_tipo", periodo_tipo) \
            .eq("periodo_id", periodo_id) \
            .execute()

        if res.data:
            return res.data[0].get("conteudo")
        return None

    except Exception as e:
        st.error("❌ Erro ao buscar relatório congelado no Supabase.")
        st.write("📌 Aluna:", aluna)
        st.write("📌 Período tipo:", periodo_tipo)
        st.write("📌 Período id:", periodo_id)
        st.exception(e)
        return None



def buscar_mensais_congelados(aluna, ano, meses):
    textos = []
    meses_faltando = []

    for mes in meses:
        periodo_id = f"{ano}-{mes:02d}"
        conteudo = buscar_analise_congelada(aluna, "mensal", periodo_id)
        if conteudo:
            textos.append((periodo_id, conteudo))
        else:
            meses_faltando.append(periodo_id)

    return textos, meses_faltando


def obter_bimestre(mes):
    return (mes - 1) // 2 + 1

def obter_semestre(mes):
    return 1 if mes <= 6 else 2

def meses_do_bimestre(bimestre):
    inicio = (bimestre - 1) * 2 + 1
    return [inicio, inicio + 1]
    
def meses_do_semestre(semestre):
    if semestre == 1:
        return [1, 2, 3, 4, 5, 6]
    else:
        return [7, 8, 9, 10, 11, 12]

historico_geral, calendario_raw = carregar_dados_globais()
df = pd.DataFrame(historico_geral)

calendario_db = {item.get('id'): item.get('escala', []) for item in calendario_raw if item.get("id")}

# historico_geral = db_get_historico()
# calendario_db = db_get_calendario()

def gerar_pdf(texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)

    # Substituições seguras
    texto = texto.replace("—", "-").replace("–", "-")
    texto = texto.replace("“", '"').replace("”", '"')
    texto = texto.replace("’", "'").replace("•", "-")
    texto = texto.replace("\t", "    ")

    linhas = texto.split("\n")

    for linha in linhas:
        # Remove caracteres invisíveis estranhos
        linha = linha.replace("\r", "")

        # Converte para latin-1 seguro
        linha = linha.encode("latin-1", "replace").decode("latin-1")

        # Se a linha tiver "um bloco grande" sem espaço, quebra em pedaços menores
        while len(linha) > 0:
            pdf.multi_cell(0, 8, linha[:100])
            linha = linha[100:]

    return pdf.output(dest="S").encode("latin-1")
    
def limpar_nome_arquivo(texto):
    return "".join(c for c in texto if c.isalnum() or c in ["_", "-"]).replace(" ", "_")

def normalizar_periodo(tipo):
    mapa = {
        "Diária": "diaria",
        "Mensal": "mensal",
        "Bimestral": "bimestral",
        "Semestral": "semestral",
        "Anual": "anual"
    }
    return mapa.get(tipo, tipo.lower())


# ==========================================
# MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    # CORREÇÃO: Agora as 4 variáveis correspondem aos 4 itens da lista
    tab_plan, tab_cham, tab_licao = st.tabs([
        "🗓️ Planejamento", 
        "📍 Chamada", 
        "📝 Controle de Lições"
    ])
    
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
                supabase.table("historico_geral").delete()\
                    .eq("Data", data_ch_sel)\
                    .eq("Tipo", "Chamada")\
                    .execute()
                
                supabase.table("historico_geral").insert(novos_registros).execute()
                
                                
                # Limpa cache para atualizar os gráficos de IA
                st.cache_data.clear()
                
                st.success(f"✅ Chamada de {data_ch_sel} salva com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar no banco de dados: {e}")
        aluna = None
        
    with tab_licao:
        st.subheader("Registro de Correção de Lições")
        
        # Garante o histórico para consulta
        df_historico = pd.DataFrame(historico_geral)
        data_hj = datetime.now()
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            aluna = st.selectbox("Selecione a Aluna:", ALUNAS_LISTA, key="sec_aluna")
            if st.button("❄️ Congelar análise"):
                if not aluna:
                    st.error("⚠️ Selecione uma aluna antes de salvar.")
                else:
                    # Pegando UID do usuário logado para RLS
                    user_id = st.session_state.get("user_id", None)
                    if not user_id:
                        st.error("⚠️ Usuário não autenticado. Não é possível salvar.")
                    else:
                        # Dados mínimos de exemplo; ajuste conforme sua lógica
                        periodo_tipo = "diaria"
                        periodo_id = datetime.now().strftime("%Y-%m-%d")
                        conteudo = "Análise congelada de teste."  # Substitua pelo conteúdo real
        
                        try:
                            supabase.table("analises_congeladas").insert({
                                "aluna": aluna,
                                "periodo_tipo": periodo_tipo,
                                "periodo_id": periodo_id,
                                "conteudo": conteudo,
                                "user_id": user_id
                            }).execute()
                            st.success("✅ Análise congelada salva com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao salvar análise congelada: {e}")
        with c2:
            sec_resp = st.selectbox("Responsável:", SECRETARIAS_LISTA, key="sec_resp")
        with c3:
            data_corr = st.date_input("Data:", data_hj, key="sec_data")
            data_corr_str = data_corr.strftime("%d/%m/%Y")

        # --- LÓGICA DE PENDÊNCIAS ---
        pendencias_reais = []
        if not df_historico.empty:
            df_alu = df_historico[df_historico['Aluna'] == aluna]
            if not df_alu.empty:
                # Pega o último status de cada lição/categoria
                df_alu["dt_obj"] = pd.to_datetime(df_alu["Data"], format="%d/%m/%Y", errors="coerce")
                ultimos_status = (
                    df_alu.sort_values("dt_obj")
                    .groupby(["Categoria", "Licao_Detalhe"])
                    .last()
                    .reset_index()
                )
                
                pendencias_reais = ultimos_status[ultimos_status['Status'] != "Realizadas - sem pendência"].to_dict('records')

        # --- EXIBIÇÃO DAS PENDÊNCIAS ---
        if pendencias_reais:
            st.error(f"🚨 LIÇÕES PENDENTES PARA {aluna.upper()}")
            for p in pendencias_reais:
                with st.container(border=True):
                    col_info, col_acao = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"📖 **{p['Categoria']}** | {p.get('Licao_Detalhe', '---')}")
                        st.caption(f"📅 Desde: {p['Data']} | Status: {p['Status']}")
                    with col_acao:
                        with st.expander("✅ Resolver"):
                            key_id = f"{p['Categoria']}_{p['Licao_Detalhe']}".replace(" ", "_")
                            st_res = st.selectbox("Nova Situação:", STATUS_LICAO, key=f"st_{key_id}")
                            obs_res = st.text_area("Obs entrega:", key=f"obs_{key_id}")
                            if st.button("Salvar Atualização", key=f"btn_{key_id}"):
                                db_save_historico({
                                    "Aluna": aluna, "Tipo": "Controle_Licao", "Data": data_corr_str,
                                    "Secretaria": sec_resp, "Categoria": p["Categoria"],
                                    "Licao_Detalhe": p["Licao_Detalhe"], "Status": st_res, "Observacao": obs_res
                                })
                                st.rerun()
        else:
            st.success("✅ Nenhuma pendência encontrada.")

        st.divider()

        # --- VERIFICAÇÃO DE REGISTRO EXISTENTE ---
        registro_previo = None
        if not df_historico.empty:
            condicao = (df_historico['Aluna'] == aluna) & \
                       (df_historico['Data'] == data_corr_str) & \
                       (df_historico['Tipo'] == "Controle_Licao")
            match = df_historico[condicao]
            if not match.empty:
                registro_previo = match.iloc[-1].to_dict()
                st.warning(f"⚠️ Já existe um registro para hoje. Editando registro anterior.")

        # --- FORMULÁRIO PARA NOVAS ATIVIDADES ---
        with st.form("f_nova_atividade", clear_on_submit=False):
            st.markdown("### ✍️ Registrar Nova Atividade")
            
            c_cat, c_det = st.columns([1, 2])
            idx_cat = 0
            if registro_previo and registro_previo.get('Categoria') in CATEGORIAS_LICAO:
                idx_cat = CATEGORIAS_LICAO.index(registro_previo['Categoria'])
            
            cat_sel = c_cat.radio("Categoria:", CATEGORIAS_LICAO, index=idx_cat)
            det_lic = c_det.text_input("Lição / Página:", 
                                      value=registro_previo.get('Licao_Detalhe', "") if registro_previo else "",
                                      placeholder="Ex: Lição 02, pág 05")
            
            st.divider()
            
            idx_stat = 0
            if registro_previo and registro_previo.get('Status') in STATUS_LICAO:
                idx_stat = STATUS_LICAO.index(registro_previo['Status'])
                
            status_sel = st.radio("Status hoje:", STATUS_LICAO, horizontal=True, index=idx_stat)
            obs_hoje = st.text_area("Observação Técnica:", 
                                   value=registro_previo.get('Observacao', "") if registro_previo else "")
            
            btn_label = "🔄 ATUALIZAR REGISTRO" if registro_previo else "❄️ CONGELAR E SALVAR"
            
            if st.form_submit_button(btn_label):
                if not det_lic:
                    st.error("⚠️ Informe a Lição/Página!")
                else:
                    sucesso = db_save_historico({
                        "Aluna": aluna, "Tipo": "Controle_Licao", "Data": data_corr_str,
                        "Secretaria": sec_resp, "Categoria": cat_sel, "Licao_Detalhe": det_lic,
                        "Status": status_sel, "Observacao": obs_hoje
                    })
                    if sucesso:
                        st.success("✅ Registro processado!")
                        st.cache_data.clear()
                        st.rerun()

                    
# ==========================================
# MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Controle de Desempenho")
    
    # Garante que o histórico existe para consulta
    df_historico = pd.DataFrame(historico_geral)
    
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
                    aluna_ref = atendimento['Aluna']
                    turma_aluna = atendimento.get('Turma', 'Turma Única')
    
                    is_coletiva = "SALA 8" in local_info or "SALA 9" in local_info
                    tipo_aula = "Teoria" if "SALA 8" in local_info else "Solfejo" if "SALA 9" in local_info else "Prática"
                    dif_lista = DIF_TEORIA if tipo_aula == "Teoria" else DIF_SOLFEJO if tipo_aula == "Solfejo" else DIF_PRATICA
                    
                    # --- EXIBIÇÃO DA REFERÊNCIA E TURMA ---
                    info_cabecalho = f"📍 {local_info} | 👤 Referência: {aluna_ref}"
                    if is_coletiva:
                        info_cabecalho += f" | 👥 Turma: {turma_aluna}"
                    st.success(info_cabecalho)

                    # --- VERIFICAÇÃO DE REGISTROS DA TURMA ---
                    alunas_na_turma = TURMAS.get(turma_aluna, [aluna_ref]) if is_coletiva else [aluna_ref]
                    registro_existente = None
                    total_preenchido = 0
                    
                    if not df_historico.empty:
                        # Filtra registros deste dia, horário e tipo para alunas desta turma
                        condicao = (df_historico['Aluna'].isin(alunas_na_turma)) & \
                                   (df_historico['Data'] == data_prof_str) & \
                                   (df_historico['Tipo'] == f"Aula_{tipo_aula}")
                        
                        match = df_historico[condicao]
                        total_preenchido = len(match['Aluna'].unique())
                        
                        if not match.empty:
                            registro_existente = match.iloc[-1].to_dict()
                            
                            if is_coletiva:
                                if total_preenchido >= len(alunas_na_turma):
                                    st.info(f"✅ **A turma {turma_aluna} já foi totalmente preenchida!** ({total_preenchido}/{len(alunas_na_turma)})")
                                else:
                                    st.warning(f"⚠️ Registro parcial: {total_preenchido} de {len(alunas_na_turma)} alunas preenchidas.")
                            else:
                                st.warning(f"⚠️ Registro já existente para **{aluna_ref}**.")

                    # --- CHAMADA ---
                    alunas_selecionadas = []
                    if is_coletiva:
                        st.markdown("### 👥 Chamada da Turma")
                        cols_alu = st.columns(3)
                        for idx_a, aluna in enumerate(alunas_na_turma):
                            # Se já existe no banco hoje, deixa marcado por padrão
                            ja_tem = False
                            if not df_historico.empty:
                                ja_tem = not df_historico[(df_historico['Aluna'] == aluna) & (df_historico['Data'] == data_prof_str) & (df_historico['Tipo'] == f"Aula_{tipo_aula}")].empty
                            
                            # Se for novo registro (nada no banco), todas vêm marcadas. Se for edição, mantém quem está.
                            def_val = ja_tem if total_preenchido > 0 else True
                            
                            if cols_alu[idx_a % 3].checkbox(aluna, value=def_val, key=f"chk_{aluna}_{h_sel}"):
                                alunas_selecionadas.append(aluna)
                    else:
                        alunas_selecionadas = [aluna_ref]
    
                    # --- FORMULÁRIO ---
                    with st.form("f_aula_prof", clear_on_submit=False):
                        st.subheader(f"📝 Registro de {tipo_aula}")
                        
                        idx_lic = 0
                        if registro_existente:
                            lic_salva = str(registro_existente.get('Licao_Atual', ""))
                            if lic_salva in OPCOES_LICOES_NUM:
                                idx_lic = OPCOES_LICOES_NUM.index(lic_salva)
                        
                        lic_vol = st.selectbox("Lição/Volume Atual:", OPCOES_LICOES_NUM, index=idx_lic)
                        
                        st.markdown("**Dificuldades Detectadas:**")
                        cols_dif = st.columns(2)
                        difs_selecionadas = []
                        difs_previa = registro_existente.get('Dificuldades', []) if registro_existente else []
                        if isinstance(difs_previa, str): difs_previa = [difs_previa]
                        
                        for i, d in enumerate(dif_lista):
                            target_col = cols_dif[0] if i < len(dif_lista)/2 else cols_dif[1]
                            is_checked = d in difs_previa
                            if target_col.checkbox(d, value=is_checked, key=f"diff_{d}_{h_sel}"):
                                difs_selecionadas.append(d)
                        
                        obs_val = registro_existente.get('Observacao', "") if registro_existente else ""
                        obs_aula = st.text_area("Observações Técnicas:", value=obs_val)

                        st.markdown("---")
                        st.subheader("🏠 Tarefa para Casa")
                        
                        if tipo_aula == "Prática":
                            col_c1, col_c2 = st.columns(2)
                            p_prat = col_c1.text_input("Lição Prática (Método):")
                            p_apos = col_c2.text_input("Lição da Apostila:")
                            casa_f = f"Método: {p_prat} | Apostila: {p_apos}"
                        elif tipo_aula == "Teoria":
                            col_t1, col_t2, col_t3 = st.columns(3)
                            t_msa = col_t1.text_input("Lição MSA:")
                            t_apos = col_t2.text_input("Lição Apostila:")
                            t_extra = col_t3.text_input("Atividade Extra:")
                            casa_f = f"MSA: {t_msa} | Apostila: {t_apos} | Extra: {t_extra}"
                        elif tipo_aula == "Solfejo":
                            col_s1, col_s2 = st.columns(2)
                            s_msa = col_s1.text_input("Lição MSA:")
                            s_extra = col_s2.text_input("Atividade Extra:")
                            casa_f = f"MSA: {s_msa} | Extra: {s_extra}"

                        if registro_existente:
                            st.caption(f"📌 Tarefa salva anteriormente: {registro_existente.get('Licao_Casa', 'N/A')}")

                        btn_label = "🔄 ATUALIZAR REGISTROS" if registro_existente else "❄️ CONGELAR E SALVAR AULA"
                        if st.form_submit_button(btn_label):
                            if not alunas_selecionadas:
                                st.error("⚠️ Nenhuma aluna selecionada!")
                            else:
                                with st.spinner("Salvando..."):
                                    for aluna in alunas_selecionadas:
                                        supabase.table("historico_geral").delete()\
                                            .eq("Data", data_prof_str)\
                                            .eq("Tipo", f"Aula_{tipo_aula}")\
                                            .eq("Aluna", aluna)\
                                            .execute()
                                        db_save_historico({
                                            "Aluna": aluna, "Tipo": f"Aula_{tipo_aula}", "Data": data_prof_str,
                                            "Instrutora": instr_sel, "Licao_Atual": lic_vol, 
                                            "Dificuldades": difs_selecionadas, "Observacao": obs_aula, "Licao_Casa": casa_f
                                        })
                                st.success(f"✅ Registro de {len(alunas_selecionadas)} aluna(s) processado!")
                                st.cache_data.clear()
                                st.rerun()
                else:
                    st.info(f"Irmã {instr_sel}, sem agenda para este horário.")
            
# ==========================================
# MÓDULO ANALÍTICO (TUDO NA TELA PRINCIPAL)
# ==========================================
if perfil == "📊 Analítico IA":
    st.header("📊 Painel Pedagógico de Performance")
    
    # Carregamento de dados
    historico_raw = db_get_historico()
    calendario_db = db_get_calendario()
    df = pd.DataFrame(historico_raw)

    if df.empty:
        st.info("ℹ️ Nenhum dado registrado no histórico.")
    else:
        # Tratamento de datas
        df['dt_obj'] = pd.to_datetime(df['Data'], format="%d/%m/%Y", errors='coerce')
        df = df.dropna(subset=['dt_obj']).sort_values('dt_obj', ascending=False)

        # --- SELEÇÃO DE ALUNA (NO CORPO DA PÁGINA) ---
        c_aluna, c_periodo = st.columns([2, 1])
        with c_aluna:
            aluna_sel = st.selectbox("🎯 Selecione a Aluna para Análise:", ALUNAS_LISTA)
        with c_periodo:
            periodo = st.selectbox("📅 Período:", ["Geral", "Mensal", "Bimestral", "Semestral"])

        df_aluna = df[df['Aluna'] == aluna_sel]

        # --- 1. RESUMO DE FALTAS E FREQUÊNCIA ---
        st.subheader("📌 Indicadores de Frequência")
        
        # Filtros de segurança para evitar NameError
        try:
            # Filtra apenas registros do tipo 'Chamada'
            df_chamada = df_aluna[df_aluna['Tipo'] == 'Chamada']
            
            faltas = len(df_chamada[df_chamada['Status'] == 'Ausente'])
            presencas = len(df_chamada[df_chamada['Status'] == 'Presente'])
            # Se a coluna 'Status' não tiver 'Justificada', ele apenas contará 0
            justificativas = len(df_chamada[df_chamada['Status'].str.contains('Justificada', na=False)])
        except Exception:
            faltas = 0
            presencas = 0
            justificativas = 0

        m1, m2, m3 = st.columns(3)
        # Corrigindo a exibição das métricas
        m1.metric("Total de Faltas", f"{faltas}", delta="Crítico" if faltas > 3 else None, delta_color="inverse")
        m2.metric("Presenças", presencas)
        m3.metric("Justificativas", justificativas)

        # --- 2. RELATÓRIO DETALHADO POR DATA (ESTILO EXEMPLO ENVIADO) ---
        st.subheader(f"📝 Diário Pedagógico Detalhado: {aluna_sel}")
        
        datas_aluna = df_aluna['Data'].unique()
        if len(datas_aluna) > 0:
            data_hist = st.selectbox("Escolha uma data para ver os detalhes das aulas:", datas_aluna)
            dados_dia = df_aluna[df_aluna['Data'] == data_hist]

            # Layout de 3 Colunas: Prática, Teoria e Solfejo
            col1, col2, col3 = st.columns(3)

            # --- PRÁTICA ---
            with col1:
                st.markdown("#### 🎹 Prática")
                p_data = dados_dia[dados_dia['Tipo'] == 'Aula_Pratica']
                if not p_data.empty:
                    p = p_data.iloc[0]
                    st.write(f"**Instrutora:** {p.get('Professor', '---')}")
                    st.write(f"**Lição:** {p.get('Licao_Atual', '---')}")
                    st.error(f"**Dificuldades:** {', '.join(p.get('Dificuldades', []))}")
                    st.info(f"**Lição de Casa:** {p.get('Metas', '---')}")
                    st.caption(f"Obs: {p.get('Observacao', '---')}")
                else: st.caption("Sem registro de Prática")

            # --- TEORIA ---
            with col2:
                st.markdown("#### 📝 Teoria")
                t_data = dados_dia[dados_dia['Tipo'] == 'Aula_Teoria']
                if not t_data.empty:
                    t = t_data.iloc[0]
                    st.write(f"**Instrutora:** {t.get('Professor', '---')}")
                    st.write(f"**Volume:** {t.get('Licao_Atual', '---')}")
                    st.error(f"**Dificuldades:** {', '.join(t.get('Dificuldades', []))}")
                    st.info(f"**Lição de Casa:** {t.get('Metas', '---')}")
                else: st.caption("Sem registro de Teoria")

            # --- SOLFEJO ---
            with col3:
                st.markdown("#### 🗣️ Solfejo")
                s_data = dados_dia[dados_dia['Tipo'] == 'Aula_Solfejo']
                if not s_data.empty:
                    s = s_data.iloc[0]
                    st.write(f"**Instrutora:** {s.get('Professor', '---')}")
                    st.write(f"**Volume:** {s.get('Licao_Atual', '---')}")
                    st.error(f"**Dificuldades:** {', '.join(s.get('Dificuldades', []))}")
                    st.info(f"**Lição de Casa:** {s.get('Metas', '---')}")
                else: st.caption("Sem registro de Solfejo")
            
            # --- STATUS SECRETARIA ---
            st.markdown("---")
            st.markdown("#### ✅ Situação das Lições (Secretaria)")
            sec_data = dados_dia[dados_dia['Tipo'] == 'Controle_Licao']
            if not sec_data.empty:
                for _, row in sec_data.iterrows():
                    st.write(f"**{row['Categoria']}:** {row['Status']} (Obs: {row['Observacao']})")
            else: st.caption("Sem registros de secretaria para esta data.")

        st.divider()

        # --- 3. GRÁFICOS DE EVOLUÇÃO ---
        st.subheader("📈 Gráficos de Evolução")
        g1, g2 = st.columns(2)
        
        with g1:
            # Gráfico de Faltas vs Presenças
            fig_freq = px.pie(names=['Presenças', 'Faltas', 'Justificativas'], 
                              values=[presencas, faltas, justificativas], 
                              title="Engajamento da Aluna", hole=0.5,
                              color_discrete_sequence=['#2ecc71', '#e74c3c', '#f1c40f'])
            st.plotly_chart(fig_freq, use_container_width=True)

        with g2:
            # Evolução de lições "Sem Pendência" por mês
            df_evo = df_aluna[df_aluna['Status'] == 'Realizadas - sem pendência'].copy()
            if not df_evo.empty:
                df_evo['Mes'] = df_evo['dt_obj'].dt.strftime('%m/%Y')
                evo_count = df_evo.groupby('Mes').size().reset_index(name='Qtd')
                fig_evo = px.line(evo_count, x='Mes', y='Qtd', title="Volume de Lições Concluídas/Mês", markers=True)
                st.plotly_chart(fig_evo, use_container_width=True)
            else:
                st.write("Ainda não há lições concluídas para gerar o gráfico de evolução.")

        # --- 4. RODÍZIO E ESCALA FUTURA ---
        st.divider()
        st.subheader("📅 Próximas Aulas (Rodízio)")
        hoje = datetime.now()
        sab_futuro = (hoje + timedelta(days=(5 - hoje.weekday()) % 7)).strftime("%d/%m/%Y")
        
        if sab_futuro in calendario_db:
            escala = pd.DataFrame(calendario_db[sab_futuro])
            minha_escala = escala[escala['Aluna'] == aluna_sel]
            if not minha_escala.empty:
                st.info(f"Para o próximo sábado ({sab_futuro}), o rodízio da aluna é:")
                st.table(minha_escala[['Aluna', 'Turma', '08h45 (Igreja)', '09h35 (H2)', '10h10 (H3)', '10h45 (H4)']])
            else:
                st.warning("Aluna não encontrada na escala deste sábado.")
        else:
            st.error("🚨 Rodízio não gerado para o próximo sábado.")

# (Manter os módulos de Secretaria e Professora como estão, apenas movendo a lógica de análise)
elif perfil == "🏠 Secretaria":
    st.write("Módulo de Secretaria - Use as abas acima para Chamada e Lições.")
elif perfil == "👩‍🏫 Professora":
    st.write("Módulo de Professora - Registre o desempenho das alunas aqui.")










