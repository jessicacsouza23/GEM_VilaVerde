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
    "Rebeca R - Vila Ré", "Rebecca A - Vila Verde", 
    "Sarah S - Vila Verde", "Vitória A - Vila Verde", "Vitória Bella - Vila Verde"
])

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
STATUS_LICAO = ["Realizadas - sem pendência", "Realizada - devolvida para refazer", "Não realizada"]

TURMAS = {
    "Turma 1": ["Annie - Vila Verde", "Caroline C - Vila Ré", "Ingrid M - Pq do Carmo II",
                "Mariana - Vila Araguaia", "Mellina S - Jardim Lígia", "Rebecca A - Vila Verde", 
                "Rebeca R - Vila Ré"],
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

# ==========================================
# FUNÇÕES DE BANCO - RODÍZIO EM CÍRCULO (NOVO)
# ==========================================
def db_get_rodizio_ciclo():
    """Retorna dict {professora: {'alunas_dadas': [...], 'ciclo_num': int}}"""
    try:
        res = supabase.table("rodizio_ciclo").select("*").execute()
        return {r["professora"]: {"alunas_dadas": r.get("alunas_dadas") or [],
                                   "ciclo_num": r.get("ciclo_num") or 1} for r in (res.data or [])}
    except Exception:
        return {}

def db_salvar_rodizio_ciclo(estado_ciclo):
    """Persiste o estado do ciclo (fila) de cada professora"""
    try:
        linhas = [{"professora": p, "alunas_dadas": d["alunas_dadas"], "ciclo_num": d["ciclo_num"]}
                  for p, d in estado_ciclo.items()]
        if linhas:
            supabase.table("rodizio_ciclo").upsert(linhas, on_conflict="professora").execute()
    except Exception as e:
        st.error(f"Erro ao salvar estado do rodízio: {e}")

def db_get_ultima_alocacao():
    """Retorna dict {aluna: {'professora':..., 'sala':..., 'data':...}} da última alocação de cada aluna"""
    try:
        res = supabase.table("ultima_alocacao").select("*").execute()
        return {r["aluna"]: {"professora": r.get("professora"), "sala": r.get("sala"), "data": r.get("data")}
                for r in (res.data or [])}
    except Exception:
        return {}

def db_salvar_ultima_alocacao(mapa_ultima):
    try:
        linhas = [{"aluna": a, "professora": d["professora"], "sala": d["sala"], "data": d["data"]}
                  for a, d in mapa_ultima.items()]
        if linhas:
            supabase.table("ultima_alocacao").upsert(linhas, on_conflict="aluna").execute()
    except Exception as e:
        st.error(f"Erro ao salvar última alocação: {e}")

# ==========================================
# FUNÇÕES DE BANCO - MENSAGENS (MURAL + DIRETAS)
# ==========================================
def db_get_mensagens():
    try:
        res = supabase.table("mensagens").select("*").order("id", desc=False).execute()
        return res.data or []
    except Exception:
        return []

def db_enviar_mensagem(de, para, texto):
    try:
        supabase.table("mensagens").insert({"de": de, "para": para, "texto": texto}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar mensagem: {e}")
        return False

# ==========================================
# FUNÇÕES DE BANCO - OBJETIVOS PEDAGÓGICOS (PRÓXIMA AULA)
# ==========================================
def db_get_objetivo(aluna):
    try:
        res = supabase.table("objetivos_pedagogicos").select("*").eq("aluna", aluna).execute()
        if res.data:
            return res.data[0].get("texto", ""), res.data[0].get("professora", "")
        return "", ""
    except Exception:
        return "", ""

def db_salvar_objetivo(aluna, texto, professora):
    try:
        supabase.table("objetivos_pedagogicos").upsert(
            {"aluna": aluna, "texto": texto, "professora": professora},
            on_conflict="aluna"
        ).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar objetivos: {e}")
        return False

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
        res = (
            supabase.table("analises_congeladas")
            .select("*")
            .eq("aluna", aluna)
            .eq("periodo_tipo", periodo_tipo)
            .eq("periodo_id", periodo_id)
            .execute()
        )

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
    menu = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "📊 Analítico IA", "💬 Mensagens"])
else:
    menu = st.sidebar.radio("Navegação:", ["👩‍🏫 Minhas Aulas", "📊 Analítico IA", "💬 Mensagens"])
    
    
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

        def _limpar_difs(valor_difs):
            """Normaliza Dificuldades pra sempre virar uma lista de strings reais,
            mesmo se vier None/NaN/string/lista do banco."""
            if isinstance(valor_difs, list):
                return [str(d) for d in valor_difs if d and str(d) != "Não apresentou dificuldades"]
            if isinstance(valor_difs, str) and valor_difs.strip() and valor_difs.strip().lower() != "nan":
                if valor_difs.strip() == "Não apresentou dificuldades":
                    return []
                return [valor_difs.strip()]
            return []

        if not df_historico.empty:
            df_dia = df_historico[df_historico['Data'] == data_visao]
            
            if not df_dia.empty:
                # Loop por Aluna
                for aluna_v in sorted(df_dia['Aluna'].unique()):
                    with st.expander(f"👤 {aluna_v.upper()}", expanded=True):
                        dados_aluna = df_dia[df_dia['Aluna'] == aluna_v]
                        texto_whatsapp += f"👤 *{aluna_v.upper()}*\n"

                        difs_do_dia = []       # todas as dificuldades reais da aluna nesse dia
                        proxima_semana = []     # o que ficou combinado pra próxima semana (lição de casa)

                        # Processar cada registro daquela aluna no dia
                        for _, r in dados_aluna.iterrows():
                            tipo_bruto = str(r.get('Tipo', 'Aula'))
                            tipo = tipo_bruto.replace("Analise_", "").replace("Aula_", "").replace("Casa_", "").replace("_", " ")

                            if tipo_bruto == "Chamada":
                                status = r.get('Status', '---')
                                st.markdown(f"📍 **Presença:** {status}")
                                texto_whatsapp += f"📍 Presença: {status}\n"
                                continue

                            if tipo_bruto == "Controle_Licao" or tipo == "Controle Licao":
                                cat = r.get('Categoria', 'Geral')
                                det = r.get('Licao_Detalhe', '---')
                                obs = r.get('Observacao', '---')
                                st.markdown(f"📘 **{cat}:** {det}\n\n*Nota:* {obs}")
                                texto_whatsapp += f"📘 *{cat}*: {det}\n   └─ {obs}\n"
                                continue

                            # DADOS DA PROFESSORA (Aula_/Analise_/Casa_): onde moram as dificuldades e a lição de casa
                            lic_at = r.get('Licao_Atual', '---')
                            lic_cs = r.get('Licao_Casa', '---')
                            difs_reg = _limpar_difs(r.get('Dificuldades'))

                            difs_do_dia.extend(difs_reg)
                            if lic_cs and str(lic_cs).strip() not in ("---", "", "nan"):
                                proxima_semana.append(f"{tipo}: {lic_cs}")

                            with st.container(border=True):
                                st.markdown(f"🎹 **{tipo}**")
                                st.write(f"**Lição de hoje:** {lic_at}")
                                if difs_reg:
                                    txt_difs = ", ".join(difs_reg)
                                    st.markdown(f"<div style='background-color: #FDEDEC; padding: 8px; border-radius: 5px; border-left: 4px solid #CB4335; color: #943126;'><b>⚠️ Dificuldades:</b> {txt_difs}</div>", unsafe_allow_html=True)
                                    texto_whatsapp += f"• {tipo}: {lic_at}\n   ⚠️ *Dificuldades:* {txt_difs}\n"
                                else:
                                    st.caption("✅ Sem dificuldades registradas nessa aula.")
                                    texto_whatsapp += f"• {tipo}: {lic_at}\n   ✅ Sem dificuldades\n"

                        # --- RESUMO CLARO: DIFICULDADES DO DIA + PRÓXIMA SEMANA ---
                        if difs_do_dia:
                            st.markdown(f"<div style='background-color: #FDEBD0; padding: 10px; border-radius: 6px; margin-top: 8px;'><b>⚠️ Resumo das dificuldades de hoje:</b> {', '.join(sorted(set(difs_do_dia)))}</div>", unsafe_allow_html=True)
                            texto_whatsapp += f"\n⚠️ *Resumo das dificuldades:* {', '.join(sorted(set(difs_do_dia)))}\n"

                        if proxima_semana:
                            st.markdown(f"<div style='background-color: #EAF2F8; padding: 10px; border-radius: 6px; margin-top: 8px;'><b>📅 Para a próxima semana:</b><br>{'<br>'.join(proxima_semana)}</div>", unsafe_allow_html=True)
                            texto_whatsapp += f"📅 *Para a próxima semana:*\n" + "\n".join([f"   - {p}" for p in proxima_semana]) + "\n"

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
    
    # --- ABA 2: PLANEJAMENTO (V107 - CORREÇÃO FIXAS E SALAS) ---
    with tab_plan:
        st.markdown("### 🗓️ Planejamento e Mural")
        
        # 1. GERENCIAMENTO DE ALUNAS FIXAS
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
            key="editor_fixas_v107"
        )
        st.session_state.df_fixas = df_fixas_editado
    
        st.divider()
    
        # 2. SELEÇÃO DE DATA E GERAÇÃO
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano = c2.selectbox("Ano:", [2026, 2027])
        
        sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano, mes) 
                   for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]
        
        if sabados:
            data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados])
            calendario_db = db_get_calendario()
    
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
    
                # --- BOTÃO DE GERAÇÃO — RODÍZIO EM CÍRCULO REAL (V2) ---
                if st.button("🚀 GERAR RODÍZIO AUTOMÁTICO", use_container_width=True, type="primary"):
                    # 1. MAPEAMENTO DE FIXAS (LIMPEZA TOTAL)
                    dict_fixas = {}
                    if not df_fixas_editado.empty:
                        for _, row in df_fixas_editado.iterrows():
                            if pd.notna(row['Aluna']) and pd.notna(row['Prof']):
                                dict_fixas[str(row['Aluna']).strip().lower()] = str(row['Prof']).strip()

                    # 2. UNIVERSO DE ALUNAS QUE ENTRAM NO RODÍZIO (todas menos as fixas)
                    todas_alunas_sistema = [a for turma in TURMAS.values() for a in turma]
                    universo_rodizio = sorted([a for a in todas_alunas_sistema
                                                if str(a).strip().lower() not in dict_fixas])

                    # 3. ESTADO DO CICLO (fila por professora) E ÚLTIMA ALOCAÇÃO (por aluna)
                    estado_ciclo = db_get_rodizio_ciclo()
                    ultima_alocacao = db_get_ultima_alocacao()

                    def garantir_professora(p):
                        if p not in estado_ciclo:
                            estado_ciclo[p] = {"alunas_dadas": [], "ciclo_num": 1}

                    def escolher_professora_para_aluna(aluna, candidatos):
                        """Escolhe, entre os candidatos disponíveis, uma professora que ainda
                        não deu aula para 'aluna' no ciclo atual dela. Se TODAS as candidatas já
                        deram aula pra essa aluna neste ciclo, reinicia o ciclo só das que
                        completaram a volta (deram aula pra todo o universo)."""
                        for p in candidatos:
                            garantir_professora(p)
                            # se essa professora já completou o círculo (deu aula pra todas), reinicia o ciclo dela
                            if set(estado_ciclo[p]["alunas_dadas"]) >= set(universo_rodizio):
                                estado_ciclo[p]["alunas_dadas"] = []
                                estado_ciclo[p]["ciclo_num"] += 1

                        # prioridade 1: professoras que nunca deram aula pra essa aluna neste ciclo
                        cand_1 = [p for p in candidatos if aluna not in estado_ciclo[p]["alunas_dadas"]]
                        # prioridade 2: dentre essas, evita repetir a MESMA professora do sábado passado dessa aluna
                        prof_sabado_passado = ultima_alocacao.get(aluna, {}).get("professora")
                        cand_2 = [p for p in cand_1 if p != prof_sabado_passado]

                        pool_final = cand_2 if cand_2 else (cand_1 if cand_1 else candidatos)
                        return random.choice(pool_final)

                    # 4. MAPEAMENTO INICIAL
                    mapa_final = {a: {"Aluna": a} for turma in TURMAS.values() for a in turma}
                    for aluna in mapa_final:
                        mapa_final[aluna][HORARIOS[0]] = "Roberta | Todas as alunas"

                    profs_base = [p for p in PROFESSORAS_LISTA if p not in folga_ativa]
                    registro_salas_profs = {}
                    novas_ultimas_alocacoes = {}

                    # 5. LOOP DE HORÁRIOS (H1 a H4)
                    for i, h in enumerate(HORARIOS[1:]):
                        p_teoria = pt[i]
                        p_solfejo = ps[i]

                        t_list = list(TURMAS.keys())
                        t_teo, t_sol, t_pra = t_list[i % 3], t_list[(i + 1) % 3], t_list[(i + 2) % 3]

                        # --- A. SALAS COLETIVAS ---
                        for a in TURMAS[t_teo]: mapa_final[a][h] = f"SALA 8 | {p_teoria}"
                        for a in TURMAS[t_sol]: mapa_final[a][h] = f"SALA 9 | {p_solfejo}"

                        # --- B. PRÁTICA INDIVIDUAL (S1 A S7) ---
                        disponiveis_agora = [p for p in profs_base if p not in [p_teoria, p_solfejo]]
                        alunas_na_pratica = list(TURMAS[t_pra])

                        salas_total = [f"SALA {s}" for s in range(1, 8)]
                        registro_salas_profs = {p: s for p, s in registro_salas_profs.items() if p in disponiveis_agora}

                        for p in disponiveis_agora:
                            if p not in registro_salas_profs:
                                # tenta não repetir a sala que essa professora usou no sábado passado
                                sala_passada = None
                                for al_ant, dados_ant in ultima_alocacao.items():
                                    if dados_ant.get("professora") == p:
                                        sala_passada = dados_ant.get("sala")
                                        break
                                s_livres = [s for s in salas_total if s not in registro_salas_profs.values()]
                                s_livres_pref = [s for s in s_livres if s != sala_passada] or s_livres
                                if s_livres_pref:
                                    random.shuffle(s_livres_pref)
                                    registro_salas_profs[p] = s_livres_pref[0]

                        # --- PASSO 1: ALOCAR FIXAS ---
                        alunas_rodizio = []
                        profs_disponiveis = [p for p in disponiveis_agora if p in registro_salas_profs]

                        for a in alunas_na_pratica:
                            a_key = str(a).strip().lower()
                            p_fixa = dict_fixas.get(a_key)

                            if p_fixa and p_fixa in profs_disponiveis:
                                s_f = registro_salas_profs.get(p_fixa)
                                mapa_final[a][h] = f"{s_f} | {p_fixa}"
                                profs_disponiveis.remove(p_fixa)
                                novas_ultimas_alocacoes[a] = {"professora": p_fixa, "sala": s_f, "data": data_sel_str}
                            elif p_fixa:
                                # professora fixa indisponível hoje: entra no rodízio normal em vez de ir pra secretaria
                                alunas_rodizio.append(a)
                            else:
                                alunas_rodizio.append(a)

                        # --- PASSO 2: RODÍZIO EM CÍRCULO (não repete até dar aula pra todas) ---
                        random.shuffle(alunas_rodizio)
                        for a in alunas_rodizio:
                            if profs_disponiveis:
                                p_esc = escolher_professora_para_aluna(a, profs_disponiveis)
                                s_e = registro_salas_profs.get(p_esc)
                                mapa_final[a][h] = f"{s_e} | {p_esc}"
                                profs_disponiveis.remove(p_esc)

                                garantir_professora(p_esc)
                                if a not in estado_ciclo[p_esc]["alunas_dadas"]:
                                    estado_ciclo[p_esc]["alunas_dadas"].append(a)
                                novas_ultimas_alocacoes[a] = {"professora": p_esc, "sala": s_e, "data": data_sel_str}
                            else:
                                mapa_final[a][h] = f"SECRETARIA | {a}"

                    # 6. SALVAMENTO
                    try:
                        lista_final = list(mapa_final.values())
                        supabase.table("calendario").upsert({"id": data_sel_str, "escala": lista_final}).execute()

                        # Verifica quais alunas já têm registro de histórico nessa data (evita duplicar ao regerar)
                        try:
                            ja_existe_res = supabase.table("historico_geral").select("Aluna").eq("Data", data_sel_str).execute()
                            alunas_ja_registradas = {r["Aluna"] for r in (ja_existe_res.data or [])}
                        except Exception:
                            alunas_ja_registradas = set()

                        novos_h = []
                        for a_n, dados in mapa_final.items():
                            if a_n in alunas_ja_registradas:
                                continue
                            for hor, valor in dados.items():
                                v_str = str(valor)
                                # SALVA APENAS O NOME DA PROFESSORA, SEM SALA, SEM PIANO, SEM NADA
                                if "|" in v_str and "SALA 8" not in v_str and "SALA 9" not in v_str:
                                    prof_pura = v_str.split("|")[-1].strip()
                                    novos_h.append({"Aluna": a_n, "Instrutora": prof_pura, "Data": data_sel_str})

                        if novos_h:
                            supabase.table("historico_geral").insert(novos_h).execute()

                        # Persiste o estado do rodízio em círculo e a última alocação de cada aluna
                        db_salvar_rodizio_ciclo(estado_ciclo)
                        db_salvar_ultima_alocacao(novas_ultimas_alocacoes)

                        st.success("Rodízio em círculo gerado! Nenhuma professora repete aluna até dar aula pra todas.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                    
            # --- MURAL E EDITOR FINAL CONTINUAM ABAIXO... ---
                    
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
                    # Só entra na correção da secretaria o que é lição de casa/apostila/teoria
                    # lançado como "Casa_..." — os registros "Analise_..." são a aula em si
                    # (dificuldades da professora), não passam por correção da secretaria.
                    df_alu = df_alu[~df_alu['Tipo'].str.startswith("Analise_", na=False)]

                    # Filtro de materiais permitidos (só o que a secretaria corrige: apostila da prática e teoria)
                    materiais_foco = ["teoria", "apostila"]
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
                    status_ok = ["Realizada", "Realizadas - sem pendência", "Realizada - sem pendência"]
                    mask = (
                        ultimos_status['tipo_lower'].str.contains('|'.join(materiais_foco)) & 
                        (~ultimos_status['Status'].isin(status_ok))
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
                condicao = ((df_historico['Aluna'] == aluna) &
                           (df_historico['Data'] == data_corr_str) &
                           (df_historico['Tipo'].str.contains("Casa_")))
                match = df_historico[condicao]
                if not match.empty:
                    registro_previo = match.iloc[-1].to_dict()
                    st.warning(f"⚠️ Editando registro existente de hoje ({data_corr_str}).")
        
            with st.form("f_nova_atividade_v10", clear_on_submit=False):
                st.markdown("### ✍️ Registrar Nova Atividade / Meta")
                
                c_cat, c_det = st.columns([1, 2])
                
                # Define as categorias conforme sua lista padrão
                opcoes_cat = ["Apostila", "Teoria"]
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

        # O calendário só guarda o nome da aluna, nunca a turma dela — descobrimos
        # a turma a partir do mapa TURMAS (aluna -> nome da turma).
        aluna_para_turma = {a: t for t, lst in TURMAS.items() for a in lst}

        aulas_listagem = []
        vistos_turma = set()

        if dt_str in cal_db:
            for reg in cal_db[dt_str]:
                for h in HORARIOS:
                    cont = str(reg.get(h, ""))
                    if cont and n_bus in limpar_texto(cont).lower():
                        tipo = "Teoria" if "SALA 8" in cont.upper() else "Solfejo" if "SALA 9" in cont.upper() else "Prática"
                        sala = cont.split('|')[0].strip()
                        turma_aluna = aluna_para_turma.get(reg.get("Aluna"))
                        
                        if tipo == "Prática":
                            label = f"🎹 {h} | {reg.get('Aluna')} ({sala})"
                            id_unica = f"{h}_P_{reg.get('Aluna')}"
                        else:
                            id_turma = f"{h}_{tipo}_{turma_aluna}"
                            if id_turma not in vistos_turma:
                                label = f"📚 {h} | {tipo} - {turma_aluna} ({sala})"
                                id_unica = id_turma
                                vistos_turma.add(id_turma)
                            else: continue
                        
                        aulas_listagem.append({"label": label, "id": id_unica, "h": h, "tipo": tipo, "al": reg.get("Aluna"), "tr": turma_aluna, "loc": sala})

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
                tipo_aula = d_sel["tipo"]

                # FILTRO DINÂMICO DE MÉTODOS POR CATEGORIA (fora do form, pra poder reagir na hora)
                metodos_filtrados = df_metodos_db[df_metodos_db['categoria'] == tipo_aula]['nome'].tolist() if not df_metodos_db.empty else []
                if tipo_aula == "Prática":
                    m_list = ["Selecione...", "Apostila"] + metodos_filtrados
                else:
                    m_list = ["Selecione...", "MSA", "Folha Extra"] + metodos_filtrados

                st.markdown(f"### 📝 Registro: {tipo_aula}")
                mat_focado = st.selectbox("Material usado hoje:", m_list, key=f"mat_{d_sel['id']}")

                # Busca registro já lançado hoje PARA ESSE MÉTODO ESPECÍFICO (não mistura com outro método)
                dados_hoje = {}
                if not df_hist_local.empty and mat_focado != "Selecione...":
                    f_ex = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) &
                                         (df_hist_local['Data'] == dt_str) &
                                         (df_hist_local['Tipo'] == f"Analise_{tipo_aula}") &
                                         (df_hist_local['Licao_Atual'].str.startswith(f"{mat_focado}:", na=False))]
                    if not f_ex.empty: dados_hoje = f_ex.iloc[-1].to_dict()

                with st.form(key=f"form_v58_{d_sel['id']}_{mat_focado}"):
                    lic_db = dados_hoje.get('Licao_Atual', "").split(":")[-1].strip() if ":" in dados_hoje.get('Licao_Atual', "") else ""
                    lic_hoje = st.text_input("Página/Lição trabalhada:", value=lic_db)

                    # Dificuldades — compartilhada pra toda a turma (Teoria/Solfejo) ou pra
                    # aluna única (Prática). A seleção de quem participa é só a Chamada acima.
                    st.markdown("**Dificuldades:**")
                    lista_difs = DIF_TEORIA if tipo_aula == "Teoria" else DIF_SOLFEJO if tipo_aula == "Solfejo" else DIF_PRATICA
                    difs_db = []
                    if not df_hist_local.empty and als_selecionadas and mat_focado != "Selecione...":
                        f_al = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) &
                                             (df_hist_local['Data'] == dt_str) &
                                             (df_hist_local['Tipo'] == f"Analise_{tipo_aula}") &
                                             (df_hist_local['Licao_Atual'].str.startswith(f"{mat_focado}:", na=False))]
                        if not f_al.empty:
                            difs_db = f_al.iloc[-1].get('Dificuldades', []) or []
                    cols_d = st.columns(3)
                    difs_sel = [
                        d for i, d in enumerate(lista_difs)
                        if cols_d[i % 3].checkbox(d, value=(d in difs_db), key=f"d_v58_{i}_{d_sel['id']}_{mat_focado}_{dt_str}")
                    ]

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

                    # Campo principal — o que a secretaria corrige (Apostila na prática / Teoria e Solfejo nas coletivas)
                    label_principal = "Apostila" if tipo_aula == "Prática" else tipo_aula
                    tarefas_casa[label_principal] = col_c1.text_input(f"🏠 {label_principal}:", value=get_c_v58(label_principal))

                    # Campo de Método — biblioteca cadastrada em "⚙️ Configurar Métodos".
                    # NÃO entra na correção da secretaria (método é diferente de apostila/folha de teoria).
                    opcoes_metodo_casa = ["Nenhum"] + metodos_filtrados
                    metodo_casa_sel = col_c2.selectbox("🏠 Método (opcional):", opcoes_metodo_casa, key=f"met_casa_{d_sel['id']}")
                    if metodo_casa_sel != "Nenhum":
                        metodo_casa_pag = col_c2.text_input(
                            "Página/lição do método:",
                            value=get_c_v58(f"Metodo_{metodo_casa_sel}"),
                            key=f"met_pag_{d_sel['id']}"
                        )
                        if metodo_casa_pag:
                            tarefas_casa[f"Metodo_{metodo_casa_sel}"] = metodo_casa_pag

                    obs_db = dados_hoje.get('Observacao', "")
                    obs_geral = st.text_area("Observações Pedagógicas:", value=obs_db)

                    if st.form_submit_button("💾 SALVAR E CONGELAR ANÁLISE", use_container_width=True):
                        if mat_focado == "Selecione...":
                            st.error("Selecione o material da aula antes de salvar.")
                        else:
                            difs_reais = [d for d in difs_sel if d != "Não apresentou dificuldades"]
                            status_analise = "Realizada - com dificuldades" if difs_reais else "Realizada - sem pendência"
                            for al_f in als_selecionadas:
                                # Registro Principal (mesma dificuldade pra toda a turma)
                                db_save_historico({
                                    "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                    "Tipo": f"Analise_{tipo_aula}",
                                    "Licao_Atual": f"{mat_focado}: {lic_hoje}",
                                    "Licao_Casa": "---", "Dificuldades": difs_sel,
                                    "Observacao": obs_geral, "Status": status_analise
                                })
                                # Lições de Casa (compartilhada pra toda a turma/aluna selecionada)
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
            # --- CÁLCULO DE APROVEITAMENTO (CORRIGIDO: agora reflete dificuldades reais) ---
            pedag_rows = df_aluna[df_aluna['Tipo'].str.contains("Prática|Teoria|Solfejo", case=False, na=False)].copy()

            def _tem_dificuldade_real(valor_difs):
                if isinstance(valor_difs, list):
                    return any(d for d in valor_difs if d and d != "Não apresentou dificuldades")
                if isinstance(valor_difs, str) and valor_difs.strip():
                    return valor_difs.strip() != "Não apresentou dificuldades"
                return False

            pedag_rows['tem_dificuldade'] = pedag_rows['Dificuldades'].apply(_tem_dificuldade_real)
            total_pedag = len(pedag_rows)
            sem_dificuldade = int((~pedag_rows['tem_dificuldade']).sum())
            aprov_valor = int((sem_dificuldade / total_pedag * 100)) if total_pedag > 0 else 0

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

            # --- 4.5 EVOLUÇÃO DAS DIFICULDADES AO LONGO DO TEMPO (NOVO) ---
            st.divider()
            st.markdown("### 📉 Evolução das Dificuldades")
            linhas_evolucao = []
            for _, row in df_aluna.iterrows():
                mes_ano = row['dt_obj'].strftime("%Y-%m")
                lista_dif = row.get('Dificuldades')
                if isinstance(lista_dif, list):
                    for d_item in lista_dif:
                        linhas_evolucao.append({"Mês": mes_ano, "Dificuldade": d_item})

            if linhas_evolucao:
                df_evol = pd.DataFrame(linhas_evolucao)
                df_evol = df_evol[~df_evol['Dificuldade'].str.contains("Não apresentou dificuldades|Não participou", case=False, na=False)]
                if not df_evol.empty:
                    contagem = df_evol.groupby(['Mês', 'Dificuldade']).size().reset_index(name='Ocorrências')
                    fig_evol = px.bar(contagem, x="Mês", y="Ocorrências", color="Dificuldade",
                                       title="Frequência de cada dificuldade por mês")
                    st.plotly_chart(fig_evol, use_container_width=True)

                    # Comparação simples: primeira metade do período vs segunda metade
                    meses_ordenados = sorted(df_evol['Mês'].unique())
                    if len(meses_ordenados) >= 2:
                        metade = len(meses_ordenados) // 2
                        meses_antes = set(meses_ordenados[:metade]) if metade > 0 else set()
                        meses_depois = set(meses_ordenados[metade:])
                        cont_antes = df_evol[df_evol['Mês'].isin(meses_antes)]['Dificuldade'].value_counts()
                        cont_depois = df_evol[df_evol['Mês'].isin(meses_depois)]['Dificuldade'].value_counts()
                        melhorou = [d for d in cont_antes.index if cont_depois.get(d, 0) < cont_antes.get(d, 0)]
                        piorou = [d for d in cont_depois.index if cont_depois.get(d, 0) > cont_antes.get(d, 0)]
                        col_m, col_p = st.columns(2)
                        with col_m:
                            st.success("📈 **Melhorou:** " + (", ".join(melhorou) if melhorou else "Sem melhora clara ainda."))
                        with col_p:
                            st.warning("📌 **Precisa de atenção:** " + (", ".join(piorou) if piorou else "Nenhuma piora identificada."))
                else:
                    st.success("✅ Sem dificuldades registradas para gerar histórico de evolução.")
            else:
                st.info("ℹ️ Ainda não há dificuldades registradas nesse período para montar o gráfico de evolução.")

            # --- 4.6 PRÓXIMOS OBJETIVOS (NOVO) ---
            st.divider()
            st.markdown("### 🎯 Próximos Objetivos Pedagógicos")
            objetivo_atual, quem_definiu = db_get_objetivo(aluna_sel)
            with st.form(f"form_objetivos_{aluna_sel}"):
                novo_objetivo = st.text_area(
                    "O que a aluna deve focar nas próximas aulas:",
                    value=objetivo_atual,
                    height=100,
                    help="Visível para a secretaria e para as professoras que derem aula a essa aluna."
                )
                if quem_definiu:
                    st.caption(f"Última atualização por: {quem_definiu}")
                if st.form_submit_button("💾 Salvar Objetivos"):
                    if db_salvar_objetivo(aluna_sel, novo_objetivo, st.session_state.nome_logado):
                        st.success("✅ Objetivos salvos!")
                        st.rerun()

            # --- 5. RESUMO FINAL E DICAS ---
            st.divider()
            st.info(f"💡 **Dicas para Próxima Aula:** Foque em resolver as dificuldades de " + 
                    (", ".join(list(set(difs))[:2]) if difs else "técnica e postura") + ".")
            
            status_aluna = "Ótimo desempenho!" if aprov_valor > 80 else "Atenção necessária às lições."
            st.success(f"📌 **Como a aluna está indo:** {status_aluna} (Aproveitamento: {aprov_valor}%)")

        else:
            st.warning("Selecione uma aluna ou mude o filtro para ver os registros.")

# ============================================================
# MÓDULO MENSAGENS - MURAL GERAL + DIRETAS (NOVO)
# ============================================================
elif menu == "💬 Mensagens":
    st.markdown("<h1 style='text-align: center; color: #2E4053;'>💬 Mensagens</h1>", unsafe_allow_html=True)

    eh_secretaria = st.session_state.perfil == "Secretaria"
    meu_nome = st.session_state.nome_logado
    # ID usado para enviar/filtrar mensagens: a secretaria usa sempre "Secretaria",
    # independente do nome de exibição do login (ex: "Coordenação"), pra bater
    # com o destinatário que as professoras selecionam.
    meu_id_msg = "Secretaria" if eh_secretaria else meu_nome

    # Checagem: avisa claramente se a tabela ainda não foi criada no Supabase
    try:
        supabase.table("mensagens").select("id").limit(1).execute()
        tabela_ok = True
    except Exception:
        tabela_ok = False

    if not tabela_ok:
        st.error("⚠️ A tabela 'mensagens' ainda não existe (ou não está acessível) no Supabase. "
                  "Rode o script `sql_novas_tabelas.sql` no SQL Editor do Supabase e recarregue a página.")
        st.stop()

    tab_mural, tab_direto = st.tabs(["📢 Mural Geral", "✉️ Conversa Direta"])

    todas_mensagens = db_get_mensagens()

    # --- MURAL GERAL (visível para todos, só secretaria posta) ---
    with tab_mural:
        st.caption("Avisos gerais da secretaria para todas as professoras.")
        msgs_mural = [m for m in todas_mensagens if m.get("para") == "TODOS"]
        if eh_secretaria:
            with st.form("form_mural", clear_on_submit=True):
                texto_mural = st.text_area("Novo aviso para todas:")
                if st.form_submit_button("📢 Publicar no Mural") and texto_mural.strip():
                    db_enviar_mensagem(meu_id_msg, "TODOS", texto_mural.strip())
                    st.rerun()
        if msgs_mural:
            for m in reversed(msgs_mural):
                with st.container(border=True):
                    st.write(f"**{m.get('de')}** — {m.get('created_at', '')}")
                    st.write(m.get("texto"))
        else:
            st.info("Nenhum aviso publicado ainda.")

    # --- CONVERSA DIRETA (secretaria <-> professora) ---
    with tab_direto:
        if eh_secretaria:
            contato = st.selectbox("Conversar com:", PROFESSORAS_LISTA)
        else:
            contato = "Secretaria"
            st.caption("Conversando com a Secretaria.")

        def eh_dessa_conversa(m):
            return ((m.get("de") == meu_id_msg and m.get("para") == contato) or
                   (m.get("de") == contato and m.get("para") == meu_id_msg))

        msgs_conversa = [m for m in todas_mensagens if eh_dessa_conversa(m)]

        for m in msgs_conversa:
            alinhamento = "🟢 Você" if m.get("de") == meu_id_msg else f"🔵 {m.get('de')}"
            with st.container(border=True):
                st.write(f"**{alinhamento}** — {m.get('created_at', '')}")
                st.write(m.get("texto"))

        with st.form("form_direto", clear_on_submit=True):
            texto_direto = st.text_area(f"Mensagem para {contato}:")
            if st.form_submit_button("✉️ Enviar") and texto_direto.strip():
                db_enviar_mensagem(meu_id_msg, contato, texto_direto.strip())
                st.rerun()
