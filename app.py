import streamlit as st
import pandas as pd
import calendar
from supabase import create_client, Client
from PIL import Image, ImageDraw
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime, timedelta, date
import io
import streamlit as st
import unicodedata
import json
import time # <--- ESSENCIAL PARA O SLEEP FUNCIONAR
import random
import streamlit.components.v1 as components
from streamlit_pills import pills # NOVO: Precisa instalar (pip install streamlit-pills)

# Verificação de Segurança
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except KeyError:
    st.error("⚠️ As credenciais do banco de dados não foram encontradas nas Secrets!")
    st.stop()
    
def limpar_texto(txt):
    """Remove acentos, espaços extras e coloca em maiúsculo para comparação"""
    if not txt: return ""
    txt = str(txt).strip().upper()
    # Remove acentos
    return "".join(c for c in unicodedata.normalize('NFD', txt) 
                  if unicodedata.category(c) != 'Mn')

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide")

# ============================================================
# FUNÇÃO DE SUPORTE - BUSCA MÉTODOS CADASTRADOS
# ============================================================
def db_get_metodos_cadastrados():
    try:
        # Tenta buscar os dados da tabela config_metodos
        res = supabase.table("config_metodos").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
        # Se a tabela existir mas estiver vazia, retorna colunas padrão
        return pd.DataFrame(columns=["nome", "categoria"])
    except Exception as e:
        # Se a tabela não existir ou houver erro de conexão, retorna vazio para não travar o app
        return pd.DataFrame(columns=["nome", "categoria"])

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

# --- 3. SISTEMA DE USUÁRIOS E PERMISSÕES ---
# Adicione aqui todas as professoras conforme sua lista
USUARIOS = {
    "secretaria": {"senha": "123", "perfil": "Secretaria", "nome_real": "Coordenação"},
    "cassia": {"senha": "456", "perfil": "Cassia", "nome_real": "Cassia"},
    "teta": {"senha": "456", "perfil": "Téta", "nome_real": "Téta"},
    "roberta": {"senha": "456", "perfil": "Roberta", "nome_real": "Roberta"},
    "ester": {"senha": "456", "perfil": "Ester", "nome_real": "Ester"},
    "elaine": {"senha": "456", "perfil": "Elaine", "nome_real": "Elaine"},
    "vanessa": {"senha": "456", "perfil": "Vanessa", "nome_real": "Vanessa"},
    "luciene": {"senha": "456", "perfil": "Luciene", "nome_real": "Luciene"},
    "patricia": {"senha": "456", "perfil": "Patricia", "nome_real": "Patricia"},
    "flavia": {"senha": "456", "perfil": "Flavia", "nome_real": "Flavia"},
    "kamyla": {"senha": "456", "perfil": "Kamila", "nome_real": "Kamyla"},
    "renata": {"senha": "456", "perfil": "Renata", "nome_real": "Renata"},
    # ... adicione as demais seguindo o padrão: "login": {"senha": "...", "perfil": "Professora", "nome_real": "Nome Exato na Lista"}
}


    
def login_sistema():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔐 GEM Vila Verde - Acesso Restrito")
        with st.form("login_form"):
            u = st.text_input("Usuário").lower().strip()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if u in USUARIOS and USUARIOS[u]["senha"] == s:
                    st.session_state.autenticado = True
                    st.session_state.perfil = USUARIOS[u]["perfil"]
                    st.session_state.nome_logado = USUARIOS[u]["nome_real"]
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha inválidos.")
        st.stop()

login_sistema()

# --- 3. FUNÇÕES DE DADOS ---
@st.cache_data(ttl=60)
def carregar_dados_globais():
    try:
        h = supabase.table("historico_geral").select("*").execute()
        c = supabase.table("calendario").select("*").execute()
        return h.data, c.data
    except:
        return [], []
        


# --- 2. DADOS MESTRE ---
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla", "Renata"]
SECRETARIAS_LISTA = ["Esther", "Jéssica", "Larissa", "Lurdes", "Natasha", "Roseli"]
ALUNAS_LISTA = sorted([
    "Annie - Vila Verde", "Ana Marcela S - Vila Verde", 
    "Caroline C - Vila Ré", "Elisa F - Vila Verde", "Emilly O - Vila Curuçá Velha", 
    "Gabrielly V - Vila Verde", "Heloísa R - Vila Verde", "Ingrid M - Pq do Carmo II", 
    "Júlia C - União de Vila Nova", "Júlia S. - Vila Verde", "Julya O - Vila Curuçá Velha", 
    "Mariana - Vila Araguaia", "Mellina S - Jardim Lígia", "Micaelle S - Vila Verde", "Raquel L - Vila Verde", 
    "Rebeca R - Vila Ré", "Rebecca A - Vila Verde", "Rebeka S - Jardim Lígia", 
    "Sarah S - Vila Verde", "Vitória A - Vila Verde", "Vitória Bella - Vila Verde"
])

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
STATUS_LICAO = ["Realizadas - sem pendência", "Realizada - devolvida para refazer", "Não realizada"]

TURMAS = {
    "Turma 1": ["Annie - Vila Verde", "Caroline C - Vila Ré", "Ingrid M - Pq do Carmo II",
                "Mariana - Vila Araguaia", "Mellina S - Jardim Lígia", "Rebecca A - Vila Verde", 
                "Rebeca R - Vila Ré", "Rebeka S - Jardim Lígia"],
    "Turma 2": ["Vitória A - Vila Verde", "Elisa F - Vila Verde", "Sarah S - Vila Verde", "Gabrielly V - Vila Verde", 
                "Emilly O - Vila Curuçá Velha", "Julya O - Vila Curuçá Velha"],
    "Turma 3": ["Heloísa R - Vila Verde", "Ana Marcela S - Vila Verde", "Vitória Bella - Vila Verde", 
                "Júlia S - Vila Verde", "Micaelle S - Vila Verde", "Raquel L - Vila Verde", "Júlia C - União de Vila Nova"]
}
HORARIOS = ["08h45 (Igreja)", "09h35(H2)", "10h10(H3)", "10h45(H4)"]
OPCOES_LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# ==========================================
# FUNÇÕES DE BANCO DE DADOS (SUPABASE)
# ==========================================

def db_get_historico():
    try:
        res = supabase.table("historico_geral").select("*").execute()
        return res.data
    except Exception as e:
        # Se der erro de conexão, retorna uma lista vazia e avisa de forma amigável
        st.error("🔄 Erro de conexão com o banco. Tente atualizar a página (F5).")
        return []

def db_get_calendario():
    try:
        response = supabase.table("calendario").select("*").execute()
        cal_dict = {}
        
        if response.data:
            for item in response.data:
                # 1. Pega o ID bruto (Data)
                data_bruta = str(item.get("id", "")).strip()
                escala = item.get("escala", [])
                
                # 2. Tenta padronizar para DD/MM/AAAA (Ex: 7/3/2026 -> 07/03/2026)
                try:
                    if "/" in data_bruta:
                        d, m, y = data_bruta.split("/")
                        data_padrao = f"{int(d):02d}/{int(m):02d}/{y}"
                        cal_dict[data_padrao] = escala
                    else:
                        cal_dict[data_bruta] = escala
                except:
                    cal_dict[data_bruta] = escala
                    
        return cal_dict
    except Exception as e:
        st.error(f"Erro no banco: {e}")
        return {}
        
def db_save_historico(dados):
    """Salva um novo registro no histórico"""
    try:
        response = supabase.table("historico_geral").insert(dados).execute()
        return response
    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")
        return None

# Inicialização de Variáveis de Segurança
historico_geral = db_get_historico()
calendario_db = db_get_calendario()
df_historico = pd.DataFrame(historico_geral)

    
# --- 3. DEFINIÇÃO DE VARIÁVEIS GLOBAIS (FIX PARA NAMEERROR) ---
data_hj = datetime.now().strftime("%d/%m/%Y")
calendario_db = db_get_calendario()


# --- 3. INTERFACE ---
# --- st.title("🎼 GEM Vila Verde - Gestão 2026")---
# --- perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])---

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

# --- 5. INTERFACE E NAVEGAÇÃO ---
st.sidebar.title(f"👋 {st.session_state.nome_logado}")
if st.session_state.perfil == "Secretaria":
    menu = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "📊 Analítico IA"])
else:
    menu = st.sidebar.radio("Navegação:", ["👩‍🏫 Minhas Aulas", "📊 Analítico IA"])
    
    
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# ==========================================
# MÓDULO SECRETARIA - LÓGICA ORIGINAL CARROSSEL
# ==========================================
if menu == "🏠 Secretaria":
    # 1. Carregamento e Vacina de Dados
    historico_raw = db_get_historico()
    df_historico = pd.DataFrame(historico_raw)
    if not df_historico.empty:
        df_historico['dt_obj'] = pd.to_datetime(df_historico['Data'], format='%d/%m/%Y', errors='coerce')

    tab_consolidado, tab_plan, tab_cham, tab_licao, tab_ajustes = st.tabs([
        "📊 Visão Geral Diária", "🗓️ Planejamento", "📍 Chamada", "📝 Controle de Lições", "🛠️ Ajustar Registros"
    ])

    # --- ABA 1: VISÃO GERAL DIÁRIA (TOTALIZADA) ---
    with tab_consolidado:
        c1, c2 = st.columns([1, 2])
        data_visao = c1.date_input("📅 Data da Análise:", datetime.now(), key="sec_v_dia_vfinal").strftime("%d/%m/%Y")
        
        st.markdown(f"""
            <div style='text-align: center; background: linear-gradient(90deg, #1B2631, #2E4053); padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
                <h2 style='margin: 0; color: #D5D8DC; font-size: 24px;'>🎼 RELATÓRIO COMPLETO VILA VERDE</h2>
                <p style='margin: 5px; color: #AEB6BF;'>Status e Dificuldades Pedagógicas • {data_visao}</p>
            </div>
        """, unsafe_allow_html=True)
        
        texto_whatsapp = f"🎼 *RELATÓRIO PEDAGÓGICO - {data_visao}*\n\n"

        if not df_historico.empty:
            df_dia = df_historico[df_historico['Data'] == data_visao]
            
            if not df_dia.empty:
                # Loop por Aluna
                for aluna_v in sorted(df_dia['Aluna'].unique()):
                    with st.expander(f"👤 {aluna_v.upper()}", expanded=True):
                        dados_aluna = df_dia[df_dia['Aluna'] == aluna_v]
                        texto_whatsapp += f"👤 *{aluna_v.upper()}*\n"
                        
                        # Processar cada registro daquela aluna no dia
                        for _, r in dados_aluna.iterrows():
                            tipo = str(r.get('Tipo', 'Aula')).replace("Aula_", "").replace("_", " ")
                            
                            if tipo == "Chamada":
                                status = r.get('Status', '---')
                                st.markdown(f"📍 **Presença:** {status}")
                                texto_whatsapp += f"📍 Presença: {status}\n"
                            
                            elif tipo == "Controle Licao":
                                cat = r.get('Categoria', 'Geral')
                                det = r.get('Licao_Detalhe', '---')
                                obs = r.get('Observacao', '---')
                                st.markdown(f"📘 **{cat}:** {det}\n\n*Análise:* {obs}")
                                texto_whatsapp += f"📘 *{cat}*: {det}\n   └─ {obs}\n"
                            
                            else:
                                # DADOS DA PROFESSORA (Onde moram as dificuldades)
                                lic_at = r.get('Licao_Atual', '---')
                                lic_cs = r.get('Licao_Casa', '---')
                                difs = r.get('Dificuldades', []) # Geralmente uma lista ou string
                                
                                # Visual no Streamlit
                                with st.container(border=True):
                                    st.markdown(f"🎹 **{tipo}**")
                                    st.write(f"**Lição:** {lic_at} | **Para Casa:** {lic_cs}")
                                    
                                    # Se houver dificuldades, exibe com destaque
                                    if difs:
                                        # Trata se for lista ou string
                                        txt_difs = ", ".join(difs) if isinstance(difs, list) else str(difs)
                                        st.markdown(f"<div style='background-color: #FDEDEC; padding: 8px; border-radius: 5px; border-left: 4px solid #CB4335; color: #943126;'><b>⚠️ Dificuldades:</b> {txt_difs}</div>", unsafe_allow_html=True)
                                        texto_whatsapp += f"• {tipo}: {lic_at}\n   ⚠️ *Dificuldades:* {txt_difs}\n   🏠 *Casa:* {lic_cs}\n"
                                    else:
                                        texto_whatsapp += f"• {tipo}: {lic_at}\n   🏠 *Casa:* {lic_cs}\n"
                                    
                        texto_whatsapp += "\n"
                
                st.divider()
                st.subheader("📋 Enviar para WhatsApp")
                st.text_area("Texto pronto para cópia:", value=texto_whatsapp, height=250)
            else:
                st.info("Nenhum dado encontrado para esta data.")
        else:
            st.warning("O banco de dados está vazio.")
            
        import base64

    import base64
    
    # --- ABA 2: PLANEJAMENTO (V94 - MURAL RESTAURADO E ORDENADO) ---
    with tab_plan:
        st.markdown("### 🗓️ Planejamento e Mural")
        
        # 1. GERENCIAMENTO DE ALUNAS FIXAS (SELEÇÃO SIMPLIFICADA)
        st.subheader("📌 Configurar Alunas Fixas")
        
        todas_alunas = sorted([aluna for turma in TURMAS.values() for aluna in turma])
        lista_professoras = sorted(PROFESSORAS_LISTA)
    
        if 'df_fixas' not in st.session_state:
            st.session_state.df_fixas = pd.DataFrame(columns=["Aluna", "Prof"])
    
        config_colunas = {
            "Aluna": st.column_config.SelectboxColumn("Nome da Aluna", options=todas_alunas, required=True),
            "Prof": st.column_config.SelectboxColumn("Professora Fixa", options=lista_professoras, required=True)
        }
    
        df_fixas_editado = st.data_editor(
            st.session_state.df_fixas,
            column_config=config_colunas,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_fixas_v94"
        )
        st.session_state.df_fixas = df_fixas_editado
    
        st.divider()
    
        # 2. SELEÇÃO DE DATA
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano = c2.selectbox("Ano:", [2026, 2027])
        
        sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano, mes) 
                   for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]
        
        if sabados:
            data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados])
            calendario_db = db_get_calendario()
    
            # CASO A: NÃO EXISTE ESCALA NO BANCO (MOSTRA INTERFACE DE GERAÇÃO)
            if data_sel_str not in calendario_db:
                st.info(f"Nenhuma escala encontrada para {data_sel_str}. Configure e gere abaixo.")
                col_t, col_s = st.columns(2)
                with col_t:
                    st.write("**📚 Teoria (Sala 8)**")
                    pt = [st.selectbox(f"Prof {h}", PROFESSORAS_LISTA, index=i, key=f"pt{i}") for i, h in enumerate(HORARIOS[1:])]
                with col_s:
                    st.write("**🔊 Solfejo (Sala 9)**")
                    ps = [st.selectbox(f"Prof {h}", PROFESSORAS_LISTA, index=i+3, key=f"ps{i}") for i, h in enumerate(HORARIOS[1:])]
                
                folga_ativa = st.multiselect("Folgas (Professoras Ausentes):", PROFESSORAS_LISTA)
    
                if st.button("🚀 GERAR RODÍZIO AUTOMÁTICO", use_container_width=True, type="primary"):
                    mapa = {aluna: {"Aluna": aluna} for t in TURMAS.values() for aluna in t}
                    
                    # 1. Horário 0: Geral
                    for a in mapa: mapa[a][HORARIOS[0]] = "Roberta | Todas as alunas"
                    
                    profs_base = [p for p in PROFESSORAS_LISTA if p not in folga_ativa]
                    
                    # --- BUSCA HISTÓRICO PARA NÃO REPETIR DUPLAS ---
                    historico_df = pd.DataFrame(db_get_historico())
                    
                    # --- FIXAR SALAS (1 a 7) - UMA PROFESSORA POR SALA ---
                    salas_pratica = [1, 2, 3, 4, 5, 6, 7]
                    random.shuffle(salas_pratica)
                    dict_salas_fixas = {}
                    
                    # Sorteamos as salas 1-7. Se tiver 8 professoras, a 8ª fica sem sala (ou apoio)
                    profs_para_sorteio = profs_base.copy()
                    random.shuffle(profs_para_sorteio)
                    
                    for p in profs_para_sorteio:
                        if salas_pratica:
                            dict_salas_fixas[p] = f"SALA {salas_pratica.pop(0)}"
                        else:
                            dict_salas_fixas[p] = "SALA 1 (Apoio)" # Evita erro se houver muitas profs

                    # --- LOOP DE HORÁRIOS ---
                    for i, h in enumerate(HORARIOS[1:]):
                        prof_t, prof_s = pt[i], ps[i] # Professoras da Teoria e Solfejo neste horário
                        
                        turmas_list = list(TURMAS.keys())
                        t_teo = turmas_list[i % 3]
                        t_sol = turmas_list[(i + 1) % 3]
                        t_pra = turmas_list[(i + 2) % 3]

                        # --- SALAS 8 E 9 (NUNCA REPETEM COM AS DE PRÁTICA) ---
                        for a in TURMAS[t_teo]: mapa[a][h] = f"SALA 8 | {prof_t}"
                        for a in TURMAS[t_sol]: mapa[a][h] = f"SALA 9 | {prof_s}"
                        
                        # --- PRÁTICA INDIVIDUAL (SALAS 1-7) ---
                        # Disponíveis = todas menos quem está na 8 ou 9 agora
                        disponiveis_p = [p for p in profs_base if p not in [prof_t, prof_s]]
                        alunas_pratica = list(TURMAS[t_pra])
                        random.shuffle(alunas_pratica) 

                        for a in alunas_pratica:
                            # 1. Verifica Professora Fixa
                            fixa = next((row['Prof'] for _, row in df_fixas_editado.iterrows() if row['Aluna'] == a), None)
                            
                            p_escolhida = None
                            
                            if fixa and fixa in disponiveis_p:
                                p_escolhida = fixa
                                disponiveis_p.remove(fixa)
                            elif disponiveis_p:
                                # 2. Lógica de Não Repetição (Histórico)
                                p_ja_atenderam = []
                                if not historico_df.empty and 'Aluna' in historico_df.columns:
                                    # Pega todas as professoras que já deram aula para essa aluna
                                    p_ja_atenderam = historico_df[historico_df['Aluna'] == a]['Instrutora'].unique().tolist()
                                
                                # Filtra candidatas que NUNCA pegaram essa aluna
                                candidatas_novas = [p for p in disponiveis_p if p not in p_ja_atenderam]
                                
                                if candidatas_novas:
                                    p_escolhida = random.choice(candidatas_novas)
                                else:
                                    # Se todas as disponíveis já deram aula para ela, pega a que faz mais tempo
                                    p_escolhida = random.choice(disponiveis_p)
                                
                                disponiveis_p.remove(p_escolhida)
                            
                            # ATRIBUIÇÃO NO MAPA
                            if p_escolhida:
                                # Usa a sala fixa que a professora recebeu lá no topo
                                sala_uso = dict_salas_fixas.get(p_escolhida)
                                mapa[a][h] = f"{sala_uso} | {p_escolhida}"
                            else:
                                # Se não houver professora para a aluna, ela vai pelo nome para a secretaria
                                mapa[a][h] = "SECRETARIA | Atividade Autônoma"

                    # Salva e Reinicia
                    supabase.table("calendario").upsert({"id": data_sel_str, "escala": list(mapa.values())}).execute()
                    st.rerun()
    
           # --- ABA 2: PLANEJAMENTO (V106 - BOTÃO MÁGICO COM CAPTURA FIEL DA TELA) ---
            else:
                df_escala = pd.DataFrame(calendario_db[data_sel_str])
                
                st.markdown(f"### 📸 Mural para Print - {data_sel_str}")
                
                # --- 1. BOTÃO ÚNICO DE ALTA PERFORMANCE ---
                # Este bloco cria o botão que "enxerga" o que você vê na tela e transforma em foto
                js_master = f"""
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <script>
                async function baixarTudoEstilizado() {{
                    const numColunas = {len(HORARIOS)};
                    for (let i = 0; i < numColunas; i++) {{
                        const divId = 'mural_export_' + i;
                        const container = window.parent.document.getElementById(divId);
                        
                        if (container) {{
                            // Captura exatamente o que está na tela com o dobro de nitidez
                            const canvas = await html2canvas(container, {{ 
                                scale: 2, 
                                backgroundColor: "#ffffff",
                                logging: false
                            }});
                            
                            const link = window.parent.document.createElement('a');
                            const hNome = container.querySelector('.horario-titulo').innerText.trim().replace(':', 'h');
                            link.download = 'Mural_' + hNome + '.png';
                            link.href = canvas.toDataURL("image/png");
                            link.click();
                            
                            // Espera meio segundo para o navegador processar o próximo "print"
                            await new Promise(r => setTimeout(r, 500));
                        }}
                    }}
                }}
                </script>
                <button onclick="baixarTudoEstilizado()" style="width:100%; background: linear-gradient(90deg, #0078d4, #005a9e); color:white; border:none; padding:18px; border-radius:12px; font-weight:bold; cursor:pointer; font-size:20px; margin-bottom:25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    📸 Gerar e Baixar Todas as Imagens (Fiel à Tela)
                </button>
                """
                st.components.v1.html(js_master, height=100)
    
                # --- 2. MONTAGEM DAS COLUNAS (O QUE APARECE NA TELA) ---
                termos_excluir = ["FALTA", "NÃO PRESENTE", "AUSENTE", "NINGUÉM", "VAZIO"]
                cores = {"SALA 1": "#dbeafe", "SALA 2": "#dcfce7", "SALA 3": "#fef9c3", "SALA 4": "#fee2e2", "SALA 5": "#f3e8ff", "SALA 6": "#ccfbf1", "SALA 7": "#e0f2fe", "SALA 8": "#ffedd5", "SALA 9": "#e0e7ff", "SECRETARIA": "#fef3c7"}
    
                cols_mural = st.columns(len(HORARIOS))
    
                for idx, h_col in enumerate(HORARIOS):
                    with cols_mural[idx]:
                        div_id = f"mural_export_{idx}"
                        
                        html_cards = ""
                        grupos = {}
                        for _, r in df_escala.iterrows():
                            info = str(r[h_col])
                            if info not in grupos: grupos[info] = []
                            grupos[info].append(r['Aluna'])
                        
                        chaves_ordenadas = sorted(grupos.keys(), key=lambda x: (
                            0 if "SALA" in x.upper() and any(i in x for i in "1234567") else 
                            1 if "SALA 8" in x.upper() else 
                            2 if "SALA 9" in x.upper() else 3, 
                            x
                        ))
                        
                        for local_prof in chaves_ordenadas:
                            local_up = local_prof.upper()
                            if any(t in local_up for t in termos_excluir) and "SECRETARIA" not in local_up: continue
    
                            # Adiciona a matéria conforme sua solicitação
                            local_exibicao = local_prof
                            if "SALA 8" in local_up: local_exibicao = f"{local_prof} (Teoria)"
                            elif "SALA 9" in local_up: local_exibicao = f"{local_prof} (Solfejo)"
    
                            bg = "#ffffff"
                            for sala, cor in cores.items():
                                if sala in local_up: bg = cor; break
                            
                            alunas_gp = grupos[local_prof]
                            if h_col == HORARIOS[0]: text_alunas = "Todas as alunas"
                            else:
                                presentes = [t for t, lista in TURMAS.items() if any(a in alunas_gp for a in lista)]
                                text_alunas = " + ".join(sorted(presentes)) if len(alunas_gp) > 1 else alunas_gp[0]
    
                            # Construção do card fiel ao print
                            html_cards += f'<div style="background-color:{bg}; border:2px solid #000; padding:10px; margin-bottom:10px; border-radius:10px; font-family:sans-serif;">'
                            html_cards += f'<b style="font-size:18px; color:#000; display:block; line-height:1.2;">{local_exibicao}</b>'
                            html_cards += f'<span style="font-size:16px; color:#1a1a1a; font-weight:800;">{text_alunas}</span>'
                            html_cards += '</div>'
    
                        # O container que o botão vai "fotografar"
                        mural_visual = f"""
                        <div id="{div_id}" style="background:white; padding:15px; border:4px solid #000; border-radius:15px; width:100%;">
                            <div class="horario-titulo" style="background:#262730; color:white; padding:10px; border-radius:8px; text-align:center; font-size:24px; font-weight:bold; margin-bottom:15px; font-family:sans-serif;">
                                {h_col}
                            </div>
                            {html_cards}
                        </div>
                        """
                        st.write(mural_visual, unsafe_allow_html=True)
    
                st.divider()
                
            # ... (Restante do código do editor de tabela continua igual)    
                # --- PARTE 2: EDITOR DE TABELA ---
                st.subheader("⚙️ Editor da Escala (Tabela)")
                df_editado_final = st.data_editor(
                    df_escala,
                    use_container_width=True,
                    key=f"edit_final_{data_sel_str}"
                )
                
                c_save1, c_save2 = st.columns(2)
                if c_save1.button("💾 Salvar Alterações", use_container_width=True):
                    lista_ajustada = df_editado_final.to_dict('records')
                    supabase.table("calendario").upsert({"id": data_sel_str, "escala": lista_ajustada}).execute()
                    st.success("Escala atualizada!")
                    st.rerun()
    
                if c_save2.button("🗑️ Apagar e Reiniciar", use_container_width=True):
                    supabase.table("calendario").delete().eq("id", data_sel_str).execute()
                    st.rerun()
                    
    # --- ABA 3: CHAMADA GERAL ---
    with tab_cham:
        st.subheader("📍 Chamada Geral")
        data_ch_sel = st.selectbox("Selecione a Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_chamada_unica")
        presenca_padrao = st.toggle("Marcar todas como Presente por padrão", value=True)
        
        registros_chamada = []
        alunas_lista = sorted([a for l in TURMAS.values() for a in l])
        
        for idx, aluna in enumerate(alunas_lista):
            col1, col2, col3 = st.columns([2, 3, 3])
            col1.write(f"**{aluna}**")
            chave_status = f"status_{idx}_{aluna}_{data_ch_sel}"
            status = col2.radio(f"Status {aluna}", ["Presente", "Ausente", "Justificada"], index=0 if presenca_padrao else 1, key=chave_status, horizontal=True, label_visibility="collapsed")
            motivo = ""
            if status == "Justificada":
                chave_motivo = f"motivo_{idx}_{aluna}_{data_ch_sel}"
                motivo = col3.text_input("Motivo", key=chave_motivo, placeholder="Justificativa", label_visibility="collapsed")
            registros_chamada.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            novos_ch = [{"Data": data_ch_sel, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Observacao": r["Motivo"], "Licao_Atual": "Presença em Aula"} for r in registros_chamada]
            supabase.table("historico_geral").delete().eq("Data", data_ch_sel).eq("Tipo", "Chamada").execute()
            supabase.table("historico_geral").insert(novos_ch).execute()
            st.success("✅ Chamada Salva!"); st.cache_data.clear()

    # --- ABA 4: CONTROLE DE LIÇÕES E PENDÊNCIAS (ESTILO CONGELADO) ---
        with tab_licao:
            st.subheader("📋 Registro de Correção de Lições")
            
            # Garante o histórico atualizado
            df_historico = pd.DataFrame(db_get_historico())
            data_hj = datetime.now()
            
            # Cabeçalho de Seleção
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                aluna = st.selectbox("Selecione a Aluna:", ALUNAS_LISTA, key="sec_aluna_v10")
                
            with c2:
                sec_resp = st.selectbox("Responsável Secretaria:", SECRETARIAS_LISTA, key="sec_resp_v10")
                
            with c3:
                data_corr = st.date_input("Data da Conferência:", data_hj, key="sec_data_v10")
                data_corr_str = data_corr.strftime("%d/%m/%Y")
        
            st.divider()
        
            # --- LÓGICA DE PENDÊNCIAS REAIS ---
            # Filtra o que é Teoria, Solfejo ou Apostila e que NÃO está realizado
            pendencias_reais = []
            if not df_historico.empty:
                df_alu = df_historico[df_historico['Aluna'] == aluna].copy()
                if not df_alu.empty:
                    # Filtro de materiais permitidos
                    materiais_foco = ["teoria", "solfejo", "apostila", "extra"]
                    df_alu['tipo_lower'] = df_alu['Tipo'].str.lower()
                    
                    # Converte data para ordenação
                    df_alu["dt_obj"] = pd.to_datetime(df_alu["Data"], format="%d/%m/%Y", errors="coerce")
                    
                    # Pega a última situação de cada lição específica
                    ultimos_status = (
                        df_alu.sort_values("dt_obj")
                        .groupby(["Tipo", "Licao_Casa"])
                        .last()
                        .reset_index()
                    )
                    
                    # Filtra apenas o que é do interesse e não está pronto
                    mask = (
                        ultimos_status['tipo_lower'].str.contains('|'.join(materiais_foco)) & 
                        (~ultimos_status['Status'].isin(["Realizada", "Realizadas - sem pendência"]))
                    )
                    pendencias_reais = ultimos_status[mask].to_dict('records')
        
            # --- EXIBIÇÃO DAS PENDÊNCIAS (Estilo Erro/🚨) ---
            if pendencias_reais:
                st.error(f"🚨 ATIVIDADES PENDENTES PARA {aluna.upper()}")
                for p in pendencias_reais:
                    with st.container(border=True):
                        col_info, col_acao = st.columns([2, 1])
                        with col_info:
                            tipo_p = p['Tipo'].replace('Casa_', '').upper()
                            st.markdown(f"📖 **{tipo_p}** | {p['Licao_Casa']}")
                            st.caption(f"📅 Lançado em: {p['Data']} | Status Atual: {p['Status']}")
                            if p.get('Observacao'):
                                st.info(f"💬 Nota: {p['Observacao']}")
                        
                        with col_acao:
                            with st.expander("✅ Resolver"):
                                # Key única baseada no ID do banco para evitar conflitos
                                key_id = f"res_{p['id']}"
                                st_res = st.radio("Nova Situação:", ["Pendente", "Realizada", "Não Realizada", "Devolvida"], key=f"st_{key_id}", horizontal=True)
                                obs_res = st.text_area("Obs da Secretaria:", key=f"obs_{key_id}")
                                
                                if st.button("Atualizar Status", key=f"btn_{key_id}", use_container_width=True):
                                    supabase.table("historico_geral").update({
                                        "Status": st_res,
                                        "Observacao": f"{p.get('Observacao', '')} | Sec: {obs_res}" if obs_res else p.get('Observacao'),
                                        "Secretaria": sec_resp,
                                        "Data": data_corr_str # Atualiza para a data da correção
                                    }).eq("id", p['id']).execute()
                                    st.success("Atualizado!"); st.cache_data.clear(); st.rerun()
            else:
                st.success(f"✅ Nenhuma pendência de Teoria ou Apostila para {aluna}.")
        
            st.divider()
        
            # --- FORMULÁRIO PARA NOVAS ATIVIDADES (Estilo "Congelar e Salvar") ---
            # Verifica se já existe algo lançado hoje para editar ou criar novo
            registro_previo = None
            if not df_historico.empty:
                condicao = (df_historico['Aluna'] == aluna) & \
                           (df_historico['Data'] == data_corr_str) & \
                           (df_historico['Tipo'].str.contains("Casa_"))
                match = df_historico[condicao]
                if not match.empty:
                    registro_previo = match.iloc[-1].to_dict()
                    st.warning(f"⚠️ Editando registro existente de hoje ({data_corr_str}).")
        
            with st.form("f_nova_atividade_v10", clear_on_submit=False):
                st.markdown("### ✍️ Registrar Nova Atividade / Meta")
                
                c_cat, c_det = st.columns([1, 2])
                
                # Define as categorias conforme sua lista padrão
                opcoes_cat = ["Apostila", "Teoria", "Solfejo", "Extra"]
                idx_cat = 0
                if registro_previo:
                    tipo_limpo = registro_previo['Tipo'].replace('Casa_', '')
                    if tipo_limpo in opcoes_cat:
                        idx_cat = opcoes_cat.index(tipo_limpo)
                
                cat_sel = c_cat.radio("Material:", opcoes_cat, index=idx_cat)
                det_lic = c_det.text_input("Lição / Página Target:", 
                                             value=registro_previo.get('Licao_Casa', "") if registro_previo else "",
                                             placeholder="Ex: Lição 05, pág 12")
                
                st.divider()
                
                status_sel = st.radio("Status Inicial:", ["Pendente", "Em Treinamento", "Realizada"], horizontal=True)
                obs_hoje = st.text_area("Observações Técnicas / Dicas:", 
                                       value=registro_previo.get('Observacao', "") if registro_previo else "")
                
                btn_label = "🔄 ATUALIZAR REGISTRO" if registro_previo else "❄️ CONGELAR E SALVAR"
                
                if st.form_submit_button(btn_label, use_container_width=True, type="primary"):
                    if not det_lic:
                        st.error("⚠️ Informe a Lição/Página!")
                    else:
                        dados_save = {
                            "Aluna": aluna, 
                            "Tipo": f"Casa_{cat_sel}", 
                            "Data": data_corr_str,
                            "Secretaria": sec_resp, 
                            "Licao_Casa": det_lic,
                            "Status": status_sel, 
                            "Observacao": obs_hoje
                        }
                        
                        if registro_previo:
                            supabase.table("historico_geral").update(dados_save).eq("id", registro_previo['id']).execute()
                        else:
                            supabase.table("historico_geral").insert(dados_save).execute()
                        
                        st.success("✅ Registro processado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
        
                    
            # ============================================================
            # MÓDULO AJUSTES - V62 (CORREÇÃO UUID + ORGANIZAÇÃO)
            # ============================================================
            with tab_ajustes:
                st.subheader("🛠️ Gestão do Banco de Dados")
                
                # --- SEÇÃO 1: APAGAR TUDO (CORRIGIDO PARA UUID) ---
                with st.expander("🚨 ÁREA CRÍTICA: Limpar Banco de Dados", expanded=False):
                    st.error("Esta ação apagará TODO o histórico do sistema. Cuidado!")
                    confirma_geral = st.checkbox("Confirmar reset total do banco de dados.")
                    
                    if st.button("🔥 LIMPAR TUDO", type="secondary", use_container_width=True, disabled=not confirma_geral):
                        try:
                            # CORREÇÃO: Usamos .not_.is_("id", "null") que funciona para qualquer tipo de ID (UUID ou Int)
                            supabase.table("historico_geral").delete().not_.is_("id", "null").execute()
                            
                            st.success("💥 O banco de dados foi limpo com sucesso!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao limpar banco: {e}")
            
                st.divider()
            
                # --- SEÇÃO 2: AJUSTAR REGISTROS INDIVIDUAIS ---
                st.markdown("### 📝 Ajustar Registros por Aluna")
                al_aj = st.selectbox("Selecione a Aluna:", ALUNAS_LISTA, key="aj_al_v62")
                
                if not df_historico.empty:
                    # 1. Preparação e Ordenação
                    df_historico['dt_obj'] = pd.to_datetime(df_historico['Data'], format='%d/%m/%Y', errors='coerce')
                    df_f = df_historico[df_historico['Aluna'] == al_aj].copy()
                    
                    if not df_f.empty:
                        df_f = df_f.sort_values('dt_obj', ascending=False)
                        
                        # 2. Rótulo detalhado para identificação fácil
                        def formatar_label(row):
                            data = row.get('Data', '00/00/0000')
                            tipo = str(row.get('Tipo', '')).upper()
                            instr = row.get('Instrutora', '---')
                            
                            # Identifica o conteúdo principal para mostrar no nome
                            conteudo = row.get('Licao_Casa') or row.get('Licao_Atual') or row.get('Observacao') or "Registro"
                            # Limita o tamanho do texto do conteúdo
                            conteudo_resumo = (str(conteudo)[:30] + '...') if len(str(conteudo)) > 30 else conteudo
                            
                            # Ícones por categoria
                            icon = "🎹" if "PRATICA" in tipo else "📚" if "TEORIA" in tipo else "⏱️" if "SOLFEJO" in tipo else "🏠" if "CASA" in tipo else "📌"
                            if "FALTA" in tipo: icon = "❌"
                            
                            return f"{icon} {data} | {tipo} | {conteudo_resumo} (Prof. {instr})"
            
                        df_f['display'] = df_f.apply(formatar_label, axis=1)
                        
                        # 3. Seletor Melhorado
                        idx_sel = st.selectbox(
                            "Qual registro deseja remover?", 
                            range(len(df_f)), 
                            format_func=lambda x: df_f['display'].iloc[x]
                        )
                        
                        reg = df_f.iloc[idx_sel]
                        
                        # Card de visualização para não apagar o errado
                        with st.container(border=True):
                            c1, c2 = st.columns(2)
                            c1.write(f"**Data:** {reg['Data']}")
                            c1.write(f"**Tipo:** {reg['Tipo']}")
                            c2.write(f"**Instrutora:** {reg.get('Instrutora')}")
                            c2.write(f"**Status:** {reg.get('Status', '---')}")
                            st.info(f"**Conteúdo:** {reg.get('Licao_Casa', reg.get('Licao_Atual', '---'))}")
            
                        if st.button("❌ EXCLUIR ESTE REGISTRO", type="primary", use_container_width=True):
                            try:
                                # Aqui o ID vai como string (UUID), o que o Supabase aceita perfeitamente
                                id_remocao = str(reg['id'])
                                supabase.table("historico_geral").delete().eq("id", id_remocao).execute()
                                
                                st.success("✅ Registro apagado com sucesso!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao apagar: {e}")
                    else:
                        st.info(f"Nenhum dado encontrado para {al_aj}.")
  
                        
# ============================================================
# MÓDULO PROFESSORA - V58 (INTEGRADO E CORRIGIDO)
# ============================================================
elif menu == "👩‍🏫 Minhas Aulas":
    st.header(f"👩‍🏫 Painel da Professora: {st.session_state.nome_logado}")
    
    # Definição das Tabs
    tab_aula, tab_config = st.tabs(["📝 Registro de Aula", "⚙️ Configurar Métodos"])

    # 1. BUSCA MÉTODOS PARA AMBAS AS ABAS
    df_metodos_db = db_get_metodos_cadastrados()

    # --- ABA DE CONFIGURAÇÃO ---
    with tab_config:
        st.subheader("⚙️ Gerenciar Biblioteca de Métodos")
        st.caption("Cadastre aqui os livros e métodos que aparecerão nos registros de aula.")
        
        df_editado = st.data_editor(
            df_metodos_db,
            column_config={
                "nome": st.column_config.TextColumn("Nome do Método", help="Ex: Kohler, Burgmüller, MSA", required=True),
                "categoria": st.column_config.SelectboxColumn("Área", options=["Prática", "Teoria", "Solfejo"], required=True)
            },
            num_rows="dynamic",
            use_container_width=True,
            key="editor_metodos_v58"
        )

        if st.button("💾 Salvar Biblioteca", use_container_width=True, type="primary"):
            try:
                novos_dados = df_editado.to_dict('records')
                # Limpeza e inserção no Supabase
                supabase.table("config_metodos").delete().neq("nome", "---").execute()
                if novos_dados:
                    supabase.table("config_metodos").insert(novos_dados).execute()
                st.success("✅ Biblioteca atualizada!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
                
    # --- ABA DE REGISTRO DE AULA ---
    with tab_aula:
        instr_sel = st.session_state.get('nome_logado', 'Selecione...')
        dt_input = st.date_input("Data da Aula:", datetime.now(), key="dt_v58")
        dt_str = dt_input.strftime("%d/%m/%Y")

        cal_db = db_get_calendario()
        n_bus = limpar_texto(instr_sel).lower().strip()
        
        aulas_listagem = []
        vistos_turma = set()

        if dt_str in cal_db:
            for reg in cal_db[dt_str]:
                for h in HORARIOS:
                    cont = str(reg.get(h, ""))
                    if cont and n_bus in limpar_texto(cont).lower():
                        tipo = "Teoria" if "SALA 8" in cont.upper() else "Solfejo" if "SALA 9" in cont.upper() else "Prática"
                        sala = cont.split('|')[0].strip()
                        
                        if tipo == "Prática":
                            label = f"🎹 {h} | {reg.get('Aluna')} ({sala})"
                            id_unica = f"{h}_P_{reg.get('Aluna')}"
                        else:
                            id_turma = f"{h}_{tipo}_{reg.get('Turma')}"
                            if id_turma not in vistos_turma:
                                label = f"📚 {h} | {tipo} - {reg.get('Turma')} ({sala})"
                                id_unica = id_turma
                                vistos_turma.add(id_turma)
                            else: continue
                        
                        aulas_listagem.append({"label": label, "id": id_unica, "h": h, "tipo": tipo, "al": reg.get("Aluna"), "tr": reg.get("Turma"), "loc": sala})

        # --- LÓGICA DE EXIBIÇÃO DE FOLGA ---
        if not aulas_listagem:
            # 1. Primeiro disparar a animação
            st.balloons() 
            
            # 2. Depois mostrar a interface visual
            st.markdown(f"""
                <div style="text-align: center; padding: 40px; background-color: #f8f9fa; border-radius: 20px; border: 2px dashed #d1d5db; margin-top: 20px;">
                    <h1 style="font-size: 60px; margin-bottom: 0;">🎈</h1>
                    <h1 style="color: #2c3e50; margin-top: 10px;">Dia de Descanso!</h1>
                    <p style="color: #7f8c8d; font-size: 18px;">Olá, <b>{instr_sel}</b>!</p>
                    <p style="color: #7f8c8d;">Não encontramos aulas agendadas para você em <b>{dt_str}</b>.</p>
                    <div style="display: inline-block; padding: 5px 15px; background-color: #e9ecef; border-radius: 15px; color: #495057; font-weight: bold; margin-top: 15px;">
                        📅 {dt_str}
                    </div>
                    <p style="margin-top: 30px; color: #95a5a6; font-style: italic; font-size: 14px;">
                        "O descanso é o tempero que torna o trabalho mais saboroso."
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # 3. Aviso complementar do Streamlit
            st.info("Sua agenda está livre para esta data.")
            
        else:
            aulas_ordenadas = sorted(aulas_listagem, key=lambda x: x['h'])
            sel_lbl = st.radio("Selecione a Aula:", [x["label"] for x in aulas_ordenadas], key="rd_v58")
            d_sel = next(x for x in aulas_listagem if x["label"] == sel_lbl)
            
            st.divider()
            
            # Chamada e Pendências
            als_ref = TURMAS.get(d_sel["tr"], [d_sel["al"]]) if d_sel["tipo"] != "Prática" else [d_sel["al"]]
            als_selecionadas = []
            df_hist_local = pd.DataFrame(db_get_historico())

            st.markdown(f"### 👥 Chamada: {d_sel['loc']}")
            for al in als_ref:
                c_ch, c_info = st.columns([1, 3])
                if c_ch.checkbox(al, value=True, key=f"ch_{al}_{d_sel['id']}"):
                    als_selecionadas.append(al)
                    if not df_hist_local.empty:
                        pends = df_hist_local[(df_hist_local['Aluna'] == al) & (df_hist_local['Status'] == 'Pendente')]
                        if not pends.empty:
                            with c_info.expander(f"⚠️ Pendências de {al}"):
                                for _, p in pends.iterrows(): st.caption(f"• {p['Licao_Casa']}")

            if als_selecionadas:
                dados_hoje = {}
                if not df_hist_local.empty:
                    f_ex = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) & 
                                         (df_hist_local['Data'] == dt_str) & 
                                         (df_hist_local['Tipo'] == f"Analise_{d_sel['tipo']}")]
                    if not f_ex.empty: dados_hoje = f_ex.iloc[-1].to_dict()

                with st.form(key=f"form_v58_{d_sel['id']}"):
                    st.subheader(f"📝 Registro: {d_sel['tipo']}")
                    
                    # FILTRO DINÂMICO DE MÉTODOS POR CATEGORIA
                    tipo_aula = d_sel["tipo"]
                    metodos_filtrados = df_metodos_db[df_metodos_db['categoria'] == tipo_aula]['nome'].tolist() if not df_metodos_db.empty else []
                    
                    # Lista de materiais baseada no banco de dados + fixos
                    if tipo_aula == "Prática":
                        m_list = ["Selecione...", "Apostila"] + metodos_filtrados
                    else:
                        m_list = ["Selecione...", "MSA", "Folha Extra"] + metodos_filtrados

                    mat_db = dados_hoje.get('Licao_Atual', "").split(":")[0] if dados_hoje else "Selecione..."
                    idx_mat = m_list.index(mat_db) if mat_db in m_list else 0
                    mat_focado = st.selectbox("Material usado hoje:", m_list, index=idx_mat)
                    
                    lic_db = dados_hoje.get('Licao_Atual', "").split(":")[-1].strip() if ":" in dados_hoje.get('Licao_Atual', "") else ""
                    lic_hoje = st.text_input("Página/Lição trabalhada:", value=lic_db)

                    # Dificuldades (Usa as constantes globais)
                    st.markdown("**Dificuldades:**")
                    lista_difs = DIF_TEORIA if tipo_aula == "Teoria" else DIF_SOLFEJO if tipo_aula == "Solfejo" else DIF_PRATICA
                    difs_db = dados_hoje.get('Dificuldades', [])
                    cols_d = st.columns(3)
                    difs_sel = [d for i, d in enumerate(lista_difs) if cols_d[i%3].checkbox(d, value=(d in difs_db), key=f"d_v58_{i}_{d_sel['id']}")]

                    st.divider()
                    st.subheader("🏠 Lição de Casa")
                    
                    def get_c_v58(m):
                        if not df_hist_local.empty:
                            c = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) & 
                                              (df_hist_local['Data'] == dt_str) & 
                                              (df_hist_local['Tipo'] == f"Casa_{m}")]
                            return c.iloc[-1]['Licao_Casa'] if not c.empty else ""
                        return ""

                    tarefas_casa = {}
                    col_c1, col_c2 = st.columns(2)
                    
                    # Define labels das lições de casa
                    m1_label = "Apostila" if tipo_aula == "Prática" else "Principal"
                    m2_label = "Método/Hino" if tipo_aula == "Prática" else "Extra"
                    
                    tarefas_casa[m1_label] = col_c1.text_input(f"🏠 {m1_label}:", value=get_c_v58(m1_label))
                    tarefas_casa[m2_label] = col_c2.text_input(f"🏠 {m2_label}:", value=get_c_v58(m2_label))

                    obs_db = dados_hoje.get('Observacao', "")
                    obs_geral = st.text_area("Observações Pedagógicas:", value=obs_db)

                    if st.form_submit_button("💾 SALVAR E CONGELAR ANÁLISE", use_container_width=True):
                        if mat_focado == "Selecione...":
                            st.error("Selecione o material da aula antes de salvar.")
                        else:
                            for al_f in als_selecionadas:
                                # Registro Principal
                                db_save_historico({
                                    "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                    "Tipo": f"Analise_{tipo_aula}",
                                    "Licao_Atual": f"{mat_focado}: {lic_hoje}",
                                    "Licao_Casa": "---", "Dificuldades": difs_sel,
                                    "Observacao": obs_geral, "Status": "Realizada"
                                })
                                # Lições de Casa
                                for mat_nome, conteudo in tarefas_casa.items():
                                    if conteudo:
                                        db_save_historico({
                                            "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                            "Tipo": f"Casa_{mat_nome}",
                                            "Licao_Atual": "Definido", "Licao_Casa": conteudo,
                                            "Dificuldades": [], "Observacao": obs_geral, "Status": "Pendente"
                                        })
                            st.success("✅ Registro concluído com sucesso!")
                            time.sleep(1)
                            st.rerun()

# ============================================================
# MÓDULO ANÁLISE DE IA - V72 (CORREÇÃO APROV + GRÁFICOS)
# ============================================================
elif menu == "📊 Analítico IA":
    st.markdown(f"<h1 style='text-align: center; color: #2E4053;'>📊 Prontuário Pedagógico Master</h1>", unsafe_allow_html=True)
    
    historico_raw = db_get_historico()
    df_base = pd.DataFrame(historico_raw)

    if df_base.empty:
        st.info("ℹ️ O banco de dados está vazio.")
    else:
        # 1. TRATAMENTO DE DATAS
        df_base['dt_obj'] = pd.to_datetime(df_base['Data'], format="%d/%m/%Y", errors='coerce')
        df_base = df_base.dropna(subset=['dt_obj']).sort_values('dt_obj', ascending=False)

        with st.sidebar:
            st.header("🔍 Filtros de Auditoria")
            aluna_sel = st.selectbox("👤 Selecione a Aluna:", ALUNAS_LISTA, key="analise_v72")
            tipo_p = st.selectbox("📅 Período:", ["Tudo", "Mensal", "Bimestral", "Semestral", "Por Dia Específico", "Personalizado"])
            
            hoje = datetime.now().date()
            if tipo_p == "Por Dia Específico": data_ini = data_fim = st.date_input("Dia da Aula:", hoje)
            elif tipo_p == "Mensal": data_ini, data_fim = hoje - timedelta(days=30), hoje
            elif tipo_p == "Bimestral": data_ini, data_fim = hoje - timedelta(days=60), hoje
            elif tipo_p == "Semestral": data_ini, data_fim = hoje - timedelta(days=180), hoje
            elif tipo_p == "Personalizado":
                data_ini = st.date_input("De:", hoje - timedelta(days=30))
                data_fim = st.date_input("Até:", hoje)
            else: data_ini, data_fim = datetime(2024, 1, 1).date(), hoje + timedelta(days=1)

        # Filtragem Base
        mask = (df_base['Aluna'] == aluna_sel) & (df_base['dt_obj'].dt.date >= data_ini) & (df_base['dt_obj'].dt.date <= data_fim)
        df_aluna = df_base[mask].copy()

        if not df_aluna.empty:
            # --- CÁLCULO DE APROVEITAMENTO (DEFINIDO NO TOPO PARA EVITAR ERRO) ---
            pedag_rows = df_aluna[df_aluna['Tipo'].str.contains("Prática|Teoria|Solfejo", case=False, na=False)]
            realizadas = len(pedag_rows[pedag_rows['Status'].str.contains("Realizada", na=False)])
            total_pedag = len(pedag_rows)
            aprov_valor = int((realizadas / total_pedag * 100)) if total_pedag > 0 else 0

            # --- PROCESSAMENTO DE STATUS E FREQUÊNCIA ---
            def identificar_v72(row):
                s, t = str(row.get('Status','')).upper(), str(row.get('Tipo','')).upper()
                if 'AUSENTE' in s or 'FALTA' in s: return 'F'
                if 'JUSTIFICADA' in s: return 'J'
                return 'P'

            df_aluna['st_calc'] = df_aluna.apply(identificar_v72, axis=1)
            resumo_dias = df_aluna.groupby('Data')['st_calc'].first()
            v_pres, v_falt, v_just = (resumo_dias=='P').sum(), (resumo_dias=='F').sum(), (resumo_dias=='J').sum()

            # --- 1. RESUMO DE DESEMPENHO (DASHBOARD) ---
            st.subheader(f"📈 Resumo de Desempenho - {aluna_sel}")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Frequência", f"{int((v_pres+v_just)/len(resumo_dias)*100) if len(resumo_dias)>0 else 0}%")
            k2.metric("Aulas/Chamadas", len(resumo_dias))
            k3.metric("Faltas (N/J)", f"{v_falt} / {v_just}")
            k4.metric("Aproveitamento", f"{aprov_valor}%")

            # --- 2. GRÁFICOS (RESTAURADOS) ---
            st.divider()
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                st.write("**Linha do Tempo de Assiduidade**")
                chart_ts = pd.DataFrame({'Data': resumo_dias.index, 'Nivel': resumo_dias.map({'P':1, 'J':0.5, 'F':0}).values})
                st.line_chart(chart_ts, x='Data', y='Nivel', color="#2E4053")
            
            with col_g2:
                st.write("**Status de Frequência**")
                chart_bar = pd.DataFrame({'Status': ['Presença', 'Falta', 'Justificada'], 'Qtd': [v_pres, v_falt, v_just]})
                st.bar_chart(chart_bar, x='Status', y='Qtd', color="#27AE60")

            # --- 3. DIFICULDADES E PENDÊNCIAS ---
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### ⚠️ Dificuldades Técnicas")
                difs = []
                for d in df_aluna['Dificuldades'].dropna():
                    if isinstance(d, list): difs.extend(d)
                    else: difs.append(str(d))
                
                if difs:
                    for d_u in sorted(list(set(difs))):
                        st.error(f"❌ {d_u}")
                else: st.success("✅ Sem dificuldades reportadas.")

            with c2:
                st.markdown("### 📚 Lições Pendentes")
                pendencias = df_aluna[(~df_aluna['Status'].str.contains("Realizada", na=False)) & 
                                      (df_aluna['Tipo'].str.contains("Teoria|Solfejo|Prática", case=False, na=False))]
                if not pendencias.empty:
                    for _, p in pendencias.iterrows():
                        st.warning(f"📖 **{p['Tipo']}**: {p['Licao_Casa'] if p.get('Licao_Casa') else p.get('Licao_Atual')}")
                else: st.success("✅ Lições em dia.")

            # --- 4. FEEDBACK DETALHADO (PROFESSORAS E SECRETARIA) ---
            st.divider()
            tab_p, tab_s = st.tabs(["👩‍🏫 Feedback Pedagógico", "🏢 Notas da Secretaria"])
            
            with tab_p:
                aulas = df_aluna[df_aluna['Tipo'].str.contains("Prática|Teoria|Solfejo", case=False, na=False)]
                for _, r in aulas.iterrows():
                    with st.container(border=True):
                        st.write(f"📅 **{r['Data']} - {r['Tipo']}**")
                        st.write(f"📝 {r.get('Observacao', 'Sem notas')}")
            
            with tab_s:
                sec = df_aluna[df_aluna['Tipo'].str.contains("Chamada|Correção", case=False, na=False)]
                for _, r in sec.iterrows():
                    with st.container(border=True):
                        st.write(f"📅 **{r['Data']} - {r['Tipo']}**")
                        st.info(f"📌 {r.get('Observacao', 'Sem observações')}")

            # --- 5. RESUMO FINAL E DICAS ---
            st.divider()
            st.info(f"💡 **Dicas para Próxima Aula:** Foque em resolver as dificuldades de " + 
                    (", ".join(list(set(difs))[:2]) if difs else "técnica e postura") + ".")
            
            status_aluna = "Ótimo desempenho!" if aprov_valor > 80 else "Atenção necessária às lições."
            st.success(f"📌 **Como a aluna está indo:** {status_aluna} (Aproveitamento: {aprov_valor}%)")

        else:
            st.warning("Selecione uma aluna ou mude o filtro para ver os registros.")
