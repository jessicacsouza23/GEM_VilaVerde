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
import itertools
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

# ==========================================
# FUNÇÕES DE BANCO - PROFESSORAS E ALUNAS (CADASTRO DINÂMICO)
# ==========================================
@st.cache_data(ttl=30)
def db_get_professoras_todas():
    """Todas as professoras cadastradas (inclusive inativas) — login já checa aqui"""
    try:
        res = supabase.table("professoras").select("*").execute()
        return res.data or []
    except Exception:
        return []

@st.cache_data(ttl=30)
def db_get_alunas_todas():
    """Todas as alunas cadastradas (inclusive inativas)"""
    try:
        res = supabase.table("alunas").select("*").execute()
        return res.data or []
    except Exception:
        return []

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
# A secretaria continua fixa por segurança. As professoras agora são
# cadastradas na tabela "professoras" (aba "👥 Turmas e Pessoas").
SENHA_SECRETARIA = "123"

def login_sistema():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔐 GEM Vila Verde - Acesso Restrito")
        with st.form("login_form"):
            u = st.text_input("Usuário").lower().strip()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if u == "secretaria" and s == SENHA_SECRETARIA:
                    st.session_state.autenticado = True
                    st.session_state.perfil = "Secretaria"
                    st.session_state.tipo_usuario = "secretaria"
                    st.session_state.nome_logado = "Coordenação"
                    st.rerun()
                else:
                    profs = db_get_professoras_todas()
                    match = next((p for p in profs if (p.get("login") or "").lower().strip() == u
                                  and p.get("senha") == s and p.get("ativo", True)), None)
                    if match:
                        st.session_state.autenticado = True
                        st.session_state.perfil = match["nome"]
                        st.session_state.tipo_usuario = "professora"
                        st.session_state.nome_logado = match["nome"]
                        st.rerun()
                    else:
                        # Login de aluna — usa os campos "login"/"senha" cadastrados
                        # na aba "👥 Turmas e Pessoas" (Alunas e Turmas).
                        alunas_login = db_get_alunas_todas()
                        match_al = next((a for a in alunas_login if (a.get("login") or "").lower().strip() == u
                                          and a.get("senha") == s and a.get("ativo", True)), None)
                        if match_al:
                            st.session_state.autenticado = True
                            st.session_state.perfil = match_al["nome"]
                            st.session_state.tipo_usuario = "aluna"
                            st.session_state.nome_logado = match_al["nome"]
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
        


# --- 2. DADOS MESTRE (dinâmico — cadastrado pela secretaria em "👥 Turmas e Pessoas") ---
def carregar_professoras_alunas_turmas():
    profs_raw = db_get_professoras_todas()
    alunas_raw = db_get_alunas_todas()

    profs_lista = sorted([p["nome"] for p in profs_raw if p.get("ativo", True)])
    alunas_ativas = [a for a in alunas_raw if a.get("ativo", True)]
    alunas_lista = sorted([a["nome"] for a in alunas_ativas])

    turmas = {}
    for a in alunas_ativas:
        t = a.get("turma") or "Sem Turma"
        turmas.setdefault(t, []).append(a["nome"])
    for t in turmas:
        turmas[t] = sorted(turmas[t])

    return profs_lista, alunas_lista, turmas

PROFESSORAS_LISTA, ALUNAS_LISTA, TURMAS = carregar_professoras_alunas_turmas()
SECRETARIAS_LISTA = ["Esther", "Jéssica", "Larissa", "Lurdes", "Natasha", "Roseli"]

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
STATUS_LICAO = ["Realizadas - sem pendência", "Realizada - devolvida para refazer", "Não realizada"]
STATUS_OK_LICAO = ["Realizada", "Realizadas - sem pendência", "Realizada - sem pendência"]

# Critério ÚNICO de "aula sem dificuldade", usado tanto no Prontuário Individual
# quanto no Quadro de Desempenho, pra os dois números do sistema baterem sempre.
# Olha a lista real de Dificuldades marcada pela professora (fonte primária),
# em vez do texto de Status (que é só uma cópia derivada dela).
def _tem_dificuldade_real(valor_difs):
    if isinstance(valor_difs, list):
        return any(d for d in valor_difs if d and d != "Não apresentou dificuldades")
    if isinstance(valor_difs, str) and valor_difs.strip():
        return valor_difs.strip() != "Não apresentou dificuldades"
    return False
# Únicos tipos de lição de casa que entram na fila de correção da secretaria:
# folha avulsa de Teoria e a apostila da Prática. Método (qualquer aula) e a
# lição de casa de Solfejo NUNCA entram aqui — quem acompanha é a professora.
TIPOS_CORRECAO_SECRETARIA = ["Casa_Apostila", "Casa_Teoria"]

# ==========================================
# CATEGORIZAÇÃO DE LIÇÃO DE CASA (usada no painel da aluna e no relatório da
# secretaria) — agrupa por disciplina e identifica o material/método exato.
# ==========================================
def _categoria_licao_casa(tipo_bruto):
    if tipo_bruto == "Casa_MSA":
        return "Solfejo"
    if tipo_bruto in ("Casa_Teoria", "Casa_Teoria_Prof"):
        return "Teoria"
    if tipo_bruto in ("Casa_Apostila", "Casa_Apostila_Prof"):
        return "Prática"
    if tipo_bruto.startswith("Casa_Metodo_"):
        return "Prática"
    return "Outra atividade"

def _metodo_ou_material(tipo_bruto):
    if tipo_bruto in ("Casa_Apostila", "Casa_Apostila_Prof"):
        return "Apostila"
    if tipo_bruto.startswith("Casa_Metodo_"):
        return tipo_bruto.replace("Casa_Metodo_", "")
    if tipo_bruto == "Casa_MSA":
        return "MSA"
    if tipo_bruto in ("Casa_Teoria", "Casa_Teoria_Prof"):
        return "Folha Avulsa"
    return "Atividade"

def _renderizar_pendencias_casa(pendentes_df):
    """Mostra as lições de casa pendentes de uma aluna, agrupadas por disciplina
    e por professora responsável. Na Prática, detalha o método e a lição exata.
    Usado tanto no painel da própria aluna quanto no relatório da secretaria."""
    if pendentes_df.empty:
        st.success("✅ Nenhuma lição de casa pendente.")
        return

    pendentes_df = pendentes_df.copy()
    pendentes_df['_dt_tmp'] = pd.to_datetime(pendentes_df['Data'], format='%d/%m/%Y', errors='coerce')
    pendentes_df['_disciplina'] = pendentes_df['Tipo'].apply(_categoria_licao_casa)
    pendentes_df['_material'] = pendentes_df['Tipo'].apply(_metodo_ou_material)

    # A lição mais recente de cada combinação disciplina+material é "pra próxima
    # aula"; as mais antigas que ainda estão pendentes ficam "atrasadas".
    chave_grupo = pendentes_df['_disciplina'] + "|" + pendentes_df['_material']
    mais_recente = pendentes_df.groupby(chave_grupo)['_dt_tmp'].transform('max')
    pendentes_df['_eh_atual'] = pendentes_df['_dt_tmp'] == mais_recente

    icones_disciplina = {"Prática": "🎹", "Teoria": "📚", "Solfejo": "🔊", "Outra atividade": "📖"}

    for disciplina in ["Prática", "Teoria", "Solfejo", "Outra atividade"]:
        bloco_disc = pendentes_df[pendentes_df['_disciplina'] == disciplina]
        if bloco_disc.empty:
            continue
        st.markdown(f"**{icones_disciplina.get(disciplina, '📖')} {disciplina}**")

        for professora in sorted(bloco_disc['Instrutora'].dropna().unique()):
            st.caption(f"👩‍🏫 Professora: {professora}")
            bloco_prof = bloco_disc[bloco_disc['Instrutora'] == professora].sort_values('_dt_tmp', ascending=False)
            for _, linha in bloco_prof.iterrows():
                with st.container(border=True):
                    if linha['_eh_atual']:
                        st.info(f"📌 **Para a próxima aula** (lançada em {linha['Data']})")
                    else:
                        st.warning(f"⚠️ **Atrasada de aula anterior** (lançada em {linha['Data']})")
                    if disciplina == "Prática":
                        st.write(f"**Método:** {linha['_material']}")
                    st.write(f"**Lição:** {linha.get('Licao_Casa', '---')}")

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

def sincronizar_ciclo_e_alocacao_da_escala(lista_escala, data_str):
    """Lê a escala como ela REALMENTE ficou salva (depois de qualquer edição
    manual) e atualiza rodizio_ciclo + ultima_alocacao a partir disso — assim
    um ajuste manual não fica "esquecido" e não se repete errado no sábado
    seguinte."""
    estado_ciclo = db_get_rodizio_ciclo()
    novas_alocacoes = {}

    for linha in lista_escala:
        aluna = linha.get("Aluna")
        if not aluna:
            continue
        for chave, valor in linha.items():
            if chave == "Aluna":
                continue
            v_str = str(valor)
            # Só conta como prática individual: tem "SALA" + número (1-7) + professora.
            # Ignora SALA 8/9 (coletivas), SECRETARIA e o horário inicial (Roberta | Todas).
            if "|" not in v_str:
                continue
            sala_parte = v_str.split("|")[0].strip().upper()
            if sala_parte in ("SALA 8", "SALA 9") or "SECRETARIA" in sala_parte or "TODAS" in v_str.upper():
                continue
            if not sala_parte.startswith("SALA"):
                continue
            professora = v_str.split("|")[-1].strip()
            if not professora or professora.upper() == aluna.upper():
                continue

            novas_alocacoes[aluna] = {"professora": professora, "sala": sala_parte, "data": data_str}

            if professora not in estado_ciclo:
                estado_ciclo[professora] = {"alunas_dadas": [], "ciclo_num": 1}
            if aluna not in estado_ciclo[professora]["alunas_dadas"]:
                estado_ciclo[professora]["alunas_dadas"].append(aluna)

    if novas_alocacoes:
        db_salvar_rodizio_ciclo(estado_ciclo)
        db_salvar_ultima_alocacao(novas_alocacoes)

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

# ==========================================
# FUNÇÕES DE BANCO - CONTROLE DE ESTUDO DIÁRIO (ALUNA)
# ==========================================
HORARIOS_ESTUDO = ["Manhã", "Tarde", "Noite"]

def db_tabela_estudo_existe():
    try:
        supabase.table("estudo_diario").select("id").limit(1).execute()
        return True
    except Exception:
        return False

def db_get_estudo_diario():
    try:
        res = supabase.table("estudo_diario").select("*").execute()
        return res.data or []
    except Exception:
        return []

def db_salvar_estudo_diario(aluna, data_str, horarios_lista):
    try:
        supabase.table("estudo_diario").upsert(
            {"aluna": aluna, "data": data_str, "horarios": horarios_lista},
            on_conflict="aluna,data"
        ).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar controle de estudo: {e}")
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
elif st.session_state.get("tipo_usuario") == "aluna":
    menu = st.sidebar.radio("Navegação:", ["🎓 Minhas Lições"])
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

    tab_consolidado, tab_plan, tab_cham, tab_licao, tab_ajustes, tab_pessoas = st.tabs([
        "📊 Visão Geral Diária", "🗓️ Planejamento", "📍 Chamada", "📝 Controle de Lições", "🛠️ Ajustar Registros", "👥 Turmas e Pessoas"
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

        # Escala do dia (rodízio salvo) — usada pra conferir se quem registrou a
        # aula é de fato quem estava escalada naquele horário/tipo pra essa aluna.
        escala_do_dia_relatorio = db_get_calendario().get(data_visao, [])

        # Controle de estudo diário das alunas (marcado por elas mesmas), pra
        # exibir no relatório com carinha de feliz/triste.
        estudo_diario_todos = db_get_estudo_diario() if db_tabela_estudo_existe() else []

        def _estudo_do_dia(aluna, data_str):
            """Retorna a lista de horários que a aluna marcou ter estudado nesse
            dia (lista vazia se não estudou ou não registrou nada)."""
            reg = next((e for e in estudo_diario_todos if e.get("aluna") == aluna and e.get("data") == data_str), None)
            return reg.get("horarios", []) if reg else None  # None = não registrou nada ainda

        def _prof_escalada_para(aluna, tipo_desejado):
            """Procura na escala do dia quem foi escalada pra dar 'tipo_desejado'
            (Prática/Teoria/Solfejo) pra 'aluna'. Retorna None se não achar.
            Compara nomes normalizados (sem acento/maiúscula) pra não falhar
            por causa de acento ou espaço digitado diferente entre as telas."""
            aluna_norm = limpar_texto(aluna)
            for reg in escala_do_dia_relatorio:
                if limpar_texto(reg.get("Aluna", "")) != aluna_norm:
                    continue
                for h in HORARIOS:
                    cont = str(reg.get(h, ""))
                    if "|" not in cont:
                        continue
                    cont_up = cont.upper()
                    if "SALA 8" in cont_up:
                        tipo_cont = "Teoria"
                    elif "SALA 9" in cont_up:
                        tipo_cont = "Solfejo"
                    elif cont_up.startswith("SALA"):
                        tipo_cont = "Prática"
                    else:
                        continue
                    if tipo_cont == tipo_desejado:
                        return cont.split("|")[-1].strip()
            return None

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

        def _valor_ou_none(v):
            """Trata None/NaN/'nan'/'---'/string vazia como 'sem valor real',
            pra nunca mostrar 'nan' cru na tela ou no texto do WhatsApp."""
            if v is None:
                return None
            try:
                if pd.isna(v):
                    return None
            except (TypeError, ValueError):
                pass
            v_str = str(v).strip()
            if v_str == "" or v_str.lower() == "nan" or v_str == "---":
                return None
            return v_str

        # Lista de alunas do dia vem da ESCALA do rodízio (fonte confiável de quem
        # tem aula hoje), não do histórico de registros — assim o relatório continua
        # mostrando todo mundo (com "faltando registro") mesmo se ninguém ainda
        # registrou nada, em vez de aparecer vazio.
        alunas_da_escala_hoje = sorted(set(
            reg.get("Aluna") for reg in escala_do_dia_relatorio if reg.get("Aluna")
        ))

        def _buscar_ultima_aula(aluna, disciplina, data_atual_str):
            """Busca o registro Analise_<disciplina> mais recente dessa aluna em
            qualquer data ANTERIOR a data_atual_str. Usado quando ela faltou ou
            justificou hoje — não teve aula nova, então repetimos o que foi visto
            da última vez, pra não sumir do relatório."""
            if df_historico.empty:
                return None
            candidatos = df_historico[
                (df_historico['Aluna'] == aluna) & (df_historico['Tipo'] == f"Analise_{disciplina}")
            ].copy()
            if candidatos.empty:
                return None
            candidatos['_dt_tmp'] = pd.to_datetime(candidatos['Data'], format='%d/%m/%Y', errors='coerce')
            data_atual_obj = pd.to_datetime(data_atual_str, format='%d/%m/%Y', errors='coerce')
            candidatos = candidatos[candidatos['_dt_tmp'] < data_atual_obj].sort_values('_dt_tmp', ascending=False)
            if candidatos.empty:
                return None
            return candidatos.iloc[0].to_dict()

        if alunas_da_escala_hoje:
            df_dia = df_historico[df_historico['Data'] == data_visao] if not df_historico.empty else pd.DataFrame()

            # Loop por Aluna
            for aluna_v in alunas_da_escala_hoje:
                with st.expander(f"👤 {aluna_v.upper()}", expanded=True):
                    dados_aluna = df_dia[df_dia['Aluna'] == aluna_v] if not df_dia.empty else pd.DataFrame()
                    texto_whatsapp += f"👤 *{aluna_v.upper()}*\n"

                    difs_do_dia = []       # todas as dificuldades reais da aluna nesse dia
                    proxima_semana = []     # o que ficou combinado pra próxima semana (lição de casa)

                    # Status de presença de hoje — decide se "sem registro" é falta de
                    # preenchimento da professora ou simplesmente porque a aluna faltou.
                    status_chamada_hoje = None
                    if not dados_aluna.empty:
                        linha_chamada = dados_aluna[dados_aluna['Tipo'] == "Chamada"]
                        if not linha_chamada.empty:
                            status_chamada_hoje = _valor_ou_none(linha_chamada.iloc[-1].get('Status'))
                    ausente_hoje = status_chamada_hoje in ("Ausente", "Justificada")

                    # Processar cada registro daquela aluna no dia
                    for _, r in dados_aluna.iterrows():
                        tipo_bruto = _valor_ou_none(r.get('Tipo'))

                        # Linha "crua" antiga (de antes da correção do gerador de
                        # rodízio) sem nenhum Tipo — não tem conteúdo pra mostrar,
                        # então só ignora. A checagem de "faltando registro" agora é
                        # feita direto contra a escala do dia, não depende mais disso.
                        if tipo_bruto is None:
                            continue

                        tipo = tipo_bruto.replace("Analise_", "").replace("Aula_", "").replace("Casa_", "").replace("_", " ")

                        if tipo_bruto == "Chamada":
                            status = _valor_ou_none(r.get('Status')) or "não registrada"
                            st.markdown(f"📍 **Presença:** {status}")
                            texto_whatsapp += f"📍 Presença: {status}\n"
                            continue

                        if tipo_bruto == "Controle_Licao" or tipo == "Controle Licao":
                            cat = _valor_ou_none(r.get('Categoria')) or "Geral"
                            det = _valor_ou_none(r.get('Licao_Detalhe')) or "não especificado"
                            obs_cl = _valor_ou_none(r.get('Observacao'))
                            st.markdown(f"📘 **{cat}:** {det}" + (f"\n\n*Nota:* {obs_cl}" if obs_cl else ""))
                            texto_whatsapp += f"📘 *{cat}*: {det}\n" + (f"   └─ {obs_cl}\n" if obs_cl else "")
                            continue

                        # --- LIÇÃO DE CASA (Casa_...): é uma tarefa combinada, não uma
                        # aula de hoje — mostrada separada pra não confundir com o
                        # "Lição de hoje" das aulas de fato. Se ainda não foi corrigida,
                        # isso fica destacado (não é "sem dificuldade", é simplesmente
                        # "ainda não corrigida") — e diz quem é responsável por corrigir.
                        if tipo_bruto.startswith("Casa_"):
                            lic_cs_casa = _valor_ou_none(r.get('Licao_Casa')) or "não especificada"
                            status_casa = _valor_ou_none(r.get('Status')) or "sem status"
                            corrigida = status_casa in STATUS_OK_LICAO
                            responsavel = "a própria professora" if tipo_bruto.endswith("_Prof") else "a secretaria"
                            with st.container(border=True):
                                st.markdown(f"🏠 **Lição de casa — {tipo}**")
                                st.write(f"**Conteúdo:** {lic_cs_casa}")
                                if corrigida:
                                    st.caption(f"Status da correção: {status_casa}")
                                else:
                                    st.warning(f"⏳ Ainda sem correção (quem corrige: {responsavel}) — status atual: {status_casa}")
                            proxima_semana.append(f"{tipo}: {lic_cs_casa}")
                            texto_whatsapp += f"🏠 Lição de casa ({tipo}): {lic_cs_casa} — status: {status_casa}\n"
                            continue

                        # --- DADOS DA PROFESSORA (Analise_...): onde moram as dificuldades,
                        # as observações (que podem trazer melhorias) e a lição de casa.
                        lic_at = _valor_ou_none(r.get('Licao_Atual')) or "não informada pela professora"
                        lic_cs = _valor_ou_none(r.get('Licao_Casa'))
                        obs_prof = _valor_ou_none(r.get('Observacao'))
                        difs_reg = _limpar_difs(r.get('Dificuldades'))

                        difs_do_dia.extend(difs_reg)
                        if lic_cs:
                            proxima_semana.append(f"{tipo}: {lic_cs}")

                        with st.container(border=True):
                            instrutora_registro = _valor_ou_none(r.get('Instrutora'))
                            prof_escalada = _prof_escalada_para(aluna_v, tipo)
                            # Nome mostrado no cabeçalho é sempre o do rodízio (fonte
                            # confiável do planejamento) — cai pro nome que registrou
                            # só se essa aluna não for encontrada na escala do dia.
                            prof_exibida = prof_escalada or instrutora_registro or "não identificada"
                            st.markdown(f"🎹 **{tipo}** — Professora: **{prof_exibida}**")
                            st.write(f"**Lição de hoje:** {lic_at}")
                            if difs_reg:
                                txt_difs = ", ".join(difs_reg)
                                st.markdown(f"<div style='background-color: #FDEDEC; padding: 8px; border-radius: 5px; border-left: 4px solid #CB4335; color: #943126;'><b>⚠️ Dificuldades:</b> {txt_difs}</div>", unsafe_allow_html=True)
                                texto_whatsapp += f"• {tipo} ({prof_exibida}): {lic_at}\n   ⚠️ *Dificuldades:* {txt_difs}\n"
                            else:
                                st.caption("✅ Sem dificuldades registradas nessa aula.")
                                texto_whatsapp += f"• {tipo} ({prof_exibida}): {lic_at}\n   ✅ Sem dificuldades\n"

                            # Observação da professora — é aqui que costumam entrar as
                            # melhorias e qualquer nota relevante pra próxima professora.
                            if obs_prof:
                                st.info(f"📝 **Observação da professora:** {obs_prof}")
                                texto_whatsapp += f"   📝 Obs: {obs_prof}\n"

                            # --- CONFERÊNCIA: quem registrou é de fato quem estava
                            # escalada no rodízio pra essa aluna, nesse tipo de aula?
                            # Comparação normalizada (sem acento/maiúscula) pra não
                            # disparar falso alarme por causa de acento diferente.
                            if prof_escalada and instrutora_registro and \
                               limpar_texto(prof_escalada) != limpar_texto(instrutora_registro):
                                st.error(f"⚠️ **Divergência com o rodízio:** a escala do dia tinha "
                                         f"**{prof_escalada}** pra essa aula, mas o registro foi feito "
                                         f"por **{instrutora_registro}**.")
                                texto_whatsapp += f"   ⚠️ Divergência: escalada {prof_escalada}, registrado por {instrutora_registro}\n"

                    # --- FALTA DE REGISTRO DA PROFESSORA (ou repetição, se faltou) ---
                    # Verifica direto contra a escala do dia (fonte confiável): pra
                    # cada uma das 3 disciplinas que essa aluna tinha agendada hoje
                    # (Prática/Teoria/Solfejo), checa se existe um Analise_<disciplina>
                    # correspondente. Se não existe E a aluna faltou/justificou, repete
                    # a última aula em vez de acusar falta de registro da professora.
                    tipos_registrados_hoje = set(_valor_ou_none(t) for t in dados_aluna['Tipo'].tolist())
                    faltando_lista = []
                    for disciplina in ["Prática", "Teoria", "Solfejo"]:
                        prof_esc_disc = _prof_escalada_para(aluna_v, disciplina)
                        if not prof_esc_disc or f"Analise_{disciplina}" in tipos_registrados_hoje:
                            continue

                        if ausente_hoje:
                            ultima_aula = _buscar_ultima_aula(aluna_v, disciplina, data_visao)
                            with st.container(border=True):
                                st.markdown(f"🔁 **{disciplina}** — Professora: **{prof_esc_disc}**")
                                st.caption(f"Aluna {status_chamada_hoje.lower()} hoje — repetindo dados da última aula:")
                                if ultima_aula:
                                    lic_ant = _valor_ou_none(ultima_aula.get('Licao_Atual')) or "não informada"
                                    difs_ant = _limpar_difs(ultima_aula.get('Dificuldades'))
                                    data_ant = ultima_aula.get('Data', '---')
                                    st.write(f"**Última lição ({data_ant}):** {lic_ant}")
                                    if difs_ant:
                                        st.markdown(f"<div style='background-color: #FDEDEC; padding: 8px; border-radius: 5px; border-left: 4px solid #CB4335; color: #943126;'><b>⚠️ Dificuldades da última aula:</b> {', '.join(difs_ant)}</div>", unsafe_allow_html=True)
                                    else:
                                        st.caption("✅ Sem dificuldades na última aula registrada.")
                                else:
                                    st.info("Nenhuma aula anterior encontrada pra repetir.")
                        else:
                            faltando_lista.append(f"{disciplina} ({prof_esc_disc})")

                    if faltando_lista:
                        txt_faltando = ", ".join(faltando_lista)
                        st.markdown(f"<div style='background-color: #FEF9E7; padding: 10px; border-radius: 6px; margin-top: 8px; border-left: 4px solid #D4AC0D;'><b>⚠️ Faltando registro da professora:</b> {txt_faltando}</div>", unsafe_allow_html=True)
                        texto_whatsapp += f"⚠️ *Faltando registro da professora:* {txt_faltando}\n"

                    # --- LIÇÕES DE CASA PENDENTES (todas em aberto, não só as de hoje) ---
                    if not df_historico.empty:
                        mask_pend_sec = (
                            (df_historico['Aluna'] == aluna_v) &
                            (df_historico['Tipo'].str.startswith("Casa_", na=False)) &
                            (~df_historico['Status'].isin(STATUS_OK_LICAO))
                        )
                        pendentes_sec_aluna = df_historico[mask_pend_sec]
                    else:
                        pendentes_sec_aluna = pd.DataFrame()

                    if not pendentes_sec_aluna.empty:
                        with st.expander(f"📋 Lições de casa pendentes ({len(pendentes_sec_aluna)})"):
                            _renderizar_pendencias_casa(pendentes_sec_aluna)
                        partes_pend_wpp = []
                        for _, linha_p in pendentes_sec_aluna.iterrows():
                            disciplina_p = _categoria_licao_casa(linha_p['Tipo'])
                            material_p = _metodo_ou_material(linha_p['Tipo'])
                            conteudo_p = _valor_ou_none(linha_p.get('Licao_Casa')) or "não especificado"
                            data_p = linha_p.get('Data', '---')
                            partes_pend_wpp.append(f"{disciplina_p} - {material_p}: {conteudo_p} (lançada em {data_p})")
                        texto_whatsapp += "📋 *Lições pendentes:*\n" + "\n".join(f"   - {p}" for p in partes_pend_wpp) + "\n"

                    # --- ESTUDO EM CASA (marcado pela própria aluna) ---
                    horarios_estudou = _estudo_do_dia(aluna_v, data_visao)
                    if horarios_estudou is None:
                        st.caption("📚 Estudo em casa: sem registro da aluna hoje.")
                    elif horarios_estudou:
                        st.success(f"📚 😊 Estudou hoje ({', '.join(horarios_estudou)})")
                        texto_whatsapp += f"📚 😊 Estudou: {', '.join(horarios_estudou)}\n"
                    else:
                        st.error("📚 😢 Não estudou hoje.")
                        texto_whatsapp += "📚 😢 Não estudou hoje\n"

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
            st.info("Nenhuma escala encontrada para esta data (rodízio não foi gerado ainda).")
            
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
                lista_turmas_ord = list(TURMAS.keys())
                col_t, col_s = st.columns(2)
                pt_por_turma, ps_por_turma = {}, {}
                with col_t:
                    st.write("**📚 Teoria (Sala 8)**")
                    for idx_t, turma_nome in enumerate(lista_turmas_ord):
                        idx_default = idx_t % len(PROFESSORAS_LISTA) if PROFESSORAS_LISTA else 0
                        pt_por_turma[turma_nome] = st.selectbox(f"Prof Teoria — {turma_nome}", PROFESSORAS_LISTA, index=idx_default, key=f"pt_{turma_nome}")
                with col_s:
                    st.write("**🔊 Solfejo (Sala 9)**")
                    for idx_t, turma_nome in enumerate(lista_turmas_ord):
                        idx_default = (idx_t + 3) % len(PROFESSORAS_LISTA) if PROFESSORAS_LISTA else 0
                        ps_por_turma[turma_nome] = st.selectbox(f"Prof Solfejo — {turma_nome}", PROFESSORAS_LISTA, index=idx_default, key=f"ps_{turma_nome}")
                st.caption("A professora acompanha a turma dela onde quer que ela caia no rodízio — mesmo se o horário mudar por causa de uma aula fixa.")
                
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

                    # --- PRIORIDADE DA AULA FIXA: escolhe qual turma faz Teoria/Solfejo/Prática
                    # em cada horário de forma que a professora fixa NUNCA esteja dando aula
                    # coletiva no exato horário em que a turma da sua aluna fixa está na prática.
                    t_list = list(TURMAS.keys())
                    melhor_arranjo = None
                    if len(t_list) == 3:
                        def _contar_conflitos_fixa(arranjo):
                            conflitos = 0
                            for i in range(3):
                                t_teo_i, t_sol_i, t_pra_i = arranjo[i]
                                prof_teo_i = pt_por_turma[t_teo_i]
                                prof_sol_i = ps_por_turma[t_sol_i]
                                # a mesma professora não pode dar Teoria e Solfejo ao mesmo tempo
                                if prof_teo_i == prof_sol_i:
                                    conflitos += 1
                                alunas_pratica_i = set(str(a).strip().lower() for a in TURMAS[t_pra_i])
                                for prof_ocupada in (prof_teo_i, prof_sol_i):
                                    for a_fixa_lower, p_fixa_nome in dict_fixas.items():
                                        if p_fixa_nome == prof_ocupada and a_fixa_lower in alunas_pratica_i:
                                            conflitos += 1
                            return conflitos

                        candidatos_arranjo = []
                        for linha0 in itertools.permutations(t_list):
                            for linha1 in itertools.permutations(t_list):
                                if any(linha1[c] == linha0[c] for c in range(3)):
                                    continue
                                for linha2 in itertools.permutations(t_list):
                                    if any(linha2[c] == linha0[c] or linha2[c] == linha1[c] for c in range(3)):
                                        continue
                                    candidatos_arranjo.append([linha0, linha1, linha2])

                        melhor_arranjo = min(candidatos_arranjo, key=_contar_conflitos_fixa)
                        conflitos_restantes = _contar_conflitos_fixa(melhor_arranjo)
                        if conflitos_restantes > 0:
                            st.warning(f"⚠️ Não foi possível eliminar {conflitos_restantes} conflito(s) de aula fixa só trocando as turmas — a professora fixa dá aula coletiva bem no horário da aluna dela em todo arranjo possível. Essas alunas vão pro rodízio normal nesse horário específico.")

                    # 5. LOOP DE HORÁRIOS (H1 a H4)
                    for i, h in enumerate(HORARIOS[1:]):
                        if melhor_arranjo:
                            t_teo, t_sol, t_pra = melhor_arranjo[i]
                        else:
                            t_teo, t_sol, t_pra = t_list[i % 3], t_list[(i + 1) % 3], t_list[(i + 2) % 3]

                        p_teoria = pt_por_turma[t_teo]
                        p_solfejo = ps_por_turma[t_sol]

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

                        # Não gravamos mais nenhuma linha "crua" (só Aluna/Instrutora/Data)
                        # no histórico aqui — a escala salva acima já é a fonte da verdade
                        # pra saber quem foi escalado, e o relatório diário (Visão Geral)
                        # compara direto contra ela pra apontar falta de registro, cobrindo
                        # Prática, Teoria e Solfejo. A linha crua causava um bug ("Todas as
                        # alunas" aparecendo como se fosse professora) e só cobria Prática.

                        # Persiste o estado do rodízio em círculo e a última alocação de cada aluna
                        db_salvar_rodizio_ciclo(estado_ciclo)
                        db_salvar_ultima_alocacao(novas_ultimas_alocacoes)

                        st.success("Rodízio em círculo gerado! Nenhuma professora repete aluna até dar aula pra todas.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                    
            # --- MURAL E EDITOR FINAL CONTINUAM ABAIXO... ---
                    
           # --- ABA 2: PLANEJAMENTO (V108 - EXPORTAÇÃO EM IMAGEM ÚNICA) ---
            else:
                df_escala = pd.DataFrame(calendario_db[data_sel_str])
                
                st.markdown(f"### 📸 Mural para Print - {data_sel_str}")

                termos_excluir = ["FALTA", "NÃO PRESENTE", "AUSENTE", "NINGUÉM", "VAZIO"]
                cores = {"SALA 1": "#dbeafe", "SALA 2": "#dcfce7", "SALA 3": "#fef9c3", "SALA 4": "#fee2e2",
                         "SALA 5": "#f3e8ff", "SALA 6": "#ccfbf1", "SALA 7": "#e0f2fe", "SALA 8": "#ffedd5",
                         "SALA 9": "#e0e7ff", "SECRETARIA": "#fef3c7"}

                colunas_html = ""
                for idx, h_col in enumerate(HORARIOS):
                    cards_html = ""
                    grupos = {}
                    for _, r in df_escala.iterrows():
                        info = str(r[h_col])
                        grupos.setdefault(info, []).append(r['Aluna'])

                    chaves_ordenadas = sorted(grupos.keys(), key=lambda x: (
                        0 if "SALA" in x.upper() and any(i in x for i in "1234567") else
                        1 if "SALA 8" in x.upper() else
                        2 if "SALA 9" in x.upper() else 3,
                        x
                    ))

                    for local_prof in chaves_ordenadas:
                        local_up = local_prof.upper()
                        if any(t in local_up for t in termos_excluir) and "SECRETARIA" not in local_up:
                            continue

                        local_exibicao = local_prof
                        if "SALA 8" in local_up: local_exibicao = f"{local_prof} (Teoria)"
                        elif "SALA 9" in local_up: local_exibicao = f"{local_prof} (Solfejo)"

                        bg = "#ffffff"
                        for sala, cor in cores.items():
                            if sala in local_up: bg = cor; break

                        alunas_gp = grupos[local_prof]
                        if h_col == HORARIOS[0]:
                            text_alunas = "Todas as alunas"
                        else:
                            presentes = [t for t, lista in TURMAS.items() if any(a in alunas_gp for a in lista)]
                            text_alunas = " + ".join(sorted(presentes)) if len(alunas_gp) > 1 else alunas_gp[0]

                        cards_html += f'''<div style="background-color:{bg}; border:2px solid #000; padding:10px; margin-bottom:10px; border-radius:10px;">
                            <b style="font-size:16px; color:#000; display:block; line-height:1.2;">{local_exibicao}</b>
                            <span style="font-size:14px; color:#1a1a1a; font-weight:800;">{text_alunas}</span>
                        </div>'''

                    colunas_html += f'''
                    <div style="flex:1; min-width:180px; background:white; border:2px solid #000; border-radius:12px; padding:10px;">
                        <div style="background:#262730; color:white; text-align:center; font-weight:bold; padding:8px; border-radius:8px; margin-bottom:10px; font-size:15px;">
                            {h_col}
                        </div>
                        {cards_html}
                    </div>'''

                nome_arquivo = f"Rodizio_{data_sel_str.replace('/', '-')}.png"

                # Fonte web (Noto Sans) carregada explicitamente: cobre acentuação e
                # caracteres especiais do português. Sem isso, o html2canvas às vezes
                # cai numa fonte padrão do sistema que "engole" acentos na hora do print.
                html_completo = f"""
                <meta charset="UTF-8">
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

                <div id="mural_wrapper" style="font-family: 'Noto Sans', Arial, sans-serif;">
                    <div id="mural_completo" style="background:white; padding:20px; border-radius:15px; font-family: 'Noto Sans', Arial, sans-serif;">
                        <div style="text-align:center; margin-bottom:18px;">
                            <h1 style="margin:0; font-size:26px; color:#111; font-family: 'Noto Sans', Arial, sans-serif;">Rodízio Geral das aulas - GEM Vila Verde</h1>
                            <h3 style="margin:6px 0 0 0; color:#555; font-weight:600; font-family: 'Noto Sans', Arial, sans-serif;">Data: {data_sel_str}</h3>
                        </div>
                        <div style="display:flex; gap:12px; align-items:flex-start;">
                            {colunas_html}
                        </div>
                    </div>

                    <button onclick="baixarImagemUnica()" style="width:100%; background: linear-gradient(90deg, #0078d4, #005a9e); color:white; border:none; padding:16px; border-radius:12px; font-weight:bold; cursor:pointer; font-size:18px; margin-top:20px; font-family: 'Noto Sans', Arial, sans-serif;">
                        📸 Baixar Rodízio Completo (1 imagem única)
                    </button>
                </div>

                <script>
                function baixarImagemUnica() {{
                    const btn = document.querySelector('#mural_wrapper button');
                    if (btn) {{ btn.disabled = true; btn.innerText = "⏳ Preparando imagem..."; }}

                    // Espera as fontes carregarem de verdade antes de tirar o print —
                    // é essa espera que resolve acentos/caracteres especiais quebrados.
                    document.fonts.ready.then(function() {{
                        return document.fonts.load("600 16px 'Noto Sans'");
                    }}).then(function() {{
                        const el = document.getElementById('mural_completo');
                        return html2canvas(el, {{
                            scale: 2,
                            backgroundColor: "#ffffff",
                            useCORS: true,
                            allowTaint: true,
                            logging: false
                        }});
                    }}).then(function(canvas) {{
                        const link = document.createElement('a');
                        link.download = "{nome_arquivo}";
                        link.href = canvas.toDataURL("image/png");
                        link.click();
                        if (btn) {{ btn.disabled = false; btn.innerText = "📸 Baixar Rodízio Completo (1 imagem única)"; }}
                    }}).catch(function(err) {{
                        console.error(err);
                        if (btn) {{ btn.disabled = false; btn.innerText = "⚠️ Erro — tente novamente"; }}
                    }});
                }}
                </script>
                """

                # Altura estimada — ajuste se cortar conteúdo
                components.html(html_completo, height=850, scrolling=True)

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
                    # Sincroniza a memória do rodízio com o que ficou salvo de verdade,
                    # pra ajuste manual não se perder e não repetir errado no próximo sábado.
                    sincronizar_ciclo_e_alocacao_da_escala(lista_ajustada, data_sel_str)
                    st.success("Escala atualizada! Rodízio (memória de professora/sala) sincronizado.")
                    st.rerun()
    
                if c_save2.button("🗑️ Apagar e Reiniciar", use_container_width=True):
                    supabase.table("calendario").delete().eq("id", data_sel_str).execute()
                    st.warning("⚠️ Escala apagada. A memória do rodízio (quem já deu aula pra quem) NÃO volta atrás — "
                               "se você gerar de novo, ela continua de onde estava. Se precisar mesmo desfazer, avise que eu ajusto manualmente.")
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
            # Só entra aqui exatamente o que a secretaria corrige: folha avulsa de
            # Teoria e apostila da Prática (ver TIPOS_CORRECAO_SECRETARIA).
            pendencias_reais = []
            if not df_historico.empty:
                df_alu = df_historico[df_historico['Aluna'] == aluna].copy()
                if not df_alu.empty:
                    df_alu = df_alu[df_alu['Tipo'].isin(TIPOS_CORRECAO_SECRETARIA)]

                    if not df_alu.empty:
                        # Converte data para ordenação
                        df_alu["dt_obj"] = pd.to_datetime(df_alu["Data"], format="%d/%m/%Y", errors="coerce")

                        # Pega a última situação de cada lição específica
                        ultimos_status = (
                            df_alu.sort_values("dt_obj")
                            .groupby(["Tipo", "Licao_Casa"])
                            .last()
                            .reset_index()
                        )

                        mask = ~ultimos_status['Status'].isin(STATUS_OK_LICAO)
                        pendencias_reais = ultimos_status[mask].to_dict('records')
        
            # --- EXIBIÇÃO DAS PENDÊNCIAS (Estilo Erro/🚨) ---
            if pendencias_reais:
                st.error(f"🚨 ATIVIDADES PENDENTES PARA {aluna.upper()}")
                for p in pendencias_reais:
                    with st.container(border=True):
                        col_info, col_acao = st.columns([2, 1])
                        with col_info:
                            tipo_bruto_p = p['Tipo'].replace('Casa_', '')
                            icone_p = "📖" if "Apostila" in tipo_bruto_p else "📄"
                            tipo_p = tipo_bruto_p.replace('Teoria', 'Folha Avulsa (Teoria)').upper()
                            st.markdown(f"{icone_p} **{tipo_p}** | {p['Licao_Casa']}")
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
        
            # --- FORMULÁRIO PARA ATIVIDADE NOVA (que a professora não lançou) ---
            # A correção do que já existe fica só na lista de pendências acima —
            # aqui é exclusivamente pra cadastrar algo que ainda não foi lançado.
            st.markdown("### ➕ Registrar Atividade Nova")
            st.caption("Use isso só para lançar uma lição que a professora não informou no sistema. Para corrigir o que já existe, use a lista de pendências acima.")
            opcoes_cat = ["Apostila", "Teoria"]
            cat_sel = st.radio("Material:", opcoes_cat, horizontal=True, key="cat_corr_sec")

            with st.form("f_nova_atividade_v10", clear_on_submit=True):
                st.markdown(f"#### ✍️ Nova atividade: {cat_sel}")
                
                det_lic = st.text_input("Lição / Página:", placeholder="Ex: Lição 05, pág 12")
                
                st.divider()
                
                status_sel = st.radio("Status Inicial:", ["Pendente", "Em Treinamento", "Realizada"], horizontal=True)
                obs_hoje = st.text_area("Observações Técnicas / Dicas:")
                
                if st.form_submit_button("❄️ CONGELAR E SALVAR", use_container_width=True, type="primary"):
                    if not det_lic:
                        st.error("⚠️ Informe a Lição/Página!")
                    else:
                        supabase.table("historico_geral").insert({
                            "Aluna": aluna, 
                            "Tipo": f"Casa_{cat_sel}", 
                            "Data": data_corr_str,
                            "Secretaria": sec_resp, 
                            "Licao_Casa": det_lic,
                            "Status": status_sel, 
                            "Observacao": obs_hoje
                        }).execute()
                        
                        st.success("✅ Atividade nova registrada com sucesso!")
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

                # --- SEÇÃO 1.5: LIMPEZA DE REGISTROS ÓRFÃOS ("Todas as alunas") ---
                with st.expander("🧹 Limpar registros órfãos do rodízio ('Todas as alunas')", expanded=False):
                    st.caption("Uma versão antiga do gerador de rodízio criava, por engano, um registro sem Tipo "
                               "com 'Instrutora' = 'Todas as alunas' pra cada aluna (o horário coletivo inicial "
                               "era interpretado como se fosse uma professora). Isso já foi corrigido na geração — "
                               "esse botão só limpa o que ficou de sobra no banco de escalas antigas.")
                    if st.button("🔍 Ver quantos registros órfãos existem", use_container_width=True):
                        try:
                            res_orfaos = supabase.table("historico_geral").select("id").is_("Tipo", "null").execute()
                            st.session_state["_qtd_orfaos"] = len(res_orfaos.data or [])
                        except Exception as e:
                            st.error(f"Erro ao consultar: {e}")

                    if "_qtd_orfaos" in st.session_state:
                        qtd = st.session_state["_qtd_orfaos"]
                        if qtd > 0:
                            st.warning(f"⚠️ {qtd} registro(s) sem Tipo encontrado(s) (inclui o bug 'Todas as alunas' e qualquer outra linha crua antiga).")
                            if st.button("🗑️ Apagar todos esses registros órfãos", type="primary", use_container_width=True):
                                try:
                                    supabase.table("historico_geral").delete().is_("Tipo", "null").execute()
                                    st.success("✅ Registros órfãos apagados!")
                                    del st.session_state["_qtd_orfaos"]
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao apagar: {e}")
                        else:
                            st.success("✅ Nenhum registro órfão encontrado.")
            
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

                st.divider()
                st.markdown("### 🔍 Verificar Consistência do Rodízio")
                st.caption("Compara o que está de fato salvo nas escalas (calendário) com o que o sistema 'acha' que aconteceu (rodizio_ciclo e ultima_alocacao). Ajustes manuais na escala que não passaram pela sincronização automática aparecem aqui.")

                if st.button("🔎 Rodar verificação", use_container_width=True):
                    cal_raw = supabase.table("calendario").select("*").execute().data or []

                    def _extrair_alocacoes(escala_lista):
                        """De uma escala (lista de linhas), extrai {aluna: {professora, sala}} só das práticas individuais."""
                        out = {}
                        for linha in escala_lista:
                            aluna = linha.get("Aluna")
                            if not aluna:
                                continue
                            for chave, valor in linha.items():
                                if chave == "Aluna":
                                    continue
                                v_str = str(valor)
                                if "|" not in v_str:
                                    continue
                                sala_parte = v_str.split("|")[0].strip().upper()
                                if sala_parte in ("SALA 8", "SALA 9") or "SECRETARIA" in sala_parte or "TODAS" in v_str.upper():
                                    continue
                                if not sala_parte.startswith("SALA"):
                                    continue
                                professora = v_str.split("|")[-1].strip()
                                if not professora:
                                    continue
                                out[aluna] = {"professora": professora, "sala": sala_parte}
                        return out

                    # 1. Última alocação REAL: percorre todas as escalas em ordem de data e
                    # vai sobrescrevendo — no final, sobra a mais recente de cada aluna.
                    itens_com_data = []
                    for item in cal_raw:
                        try:
                            d_obj = datetime.strptime(str(item.get("id", "")).strip(), "%d/%m/%Y")
                            itens_com_data.append((d_obj, item.get("id"), item.get("escala", [])))
                        except Exception:
                            continue
                    itens_com_data.sort(key=lambda x: x[0])

                    ultima_real = {}
                    for d_obj, data_str, escala in itens_com_data:
                        for aluna, dados in _extrair_alocacoes(escala).items():
                            ultima_real[aluna] = {"data": data_str, **dados}

                    # 2. Compara com o que está salvo em ultima_alocacao hoje
                    alocacao_atual = db_get_ultima_alocacao()
                    divergencias = []
                    for aluna, real in ultima_real.items():
                        registrado = alocacao_atual.get(aluna, {})
                        if registrado.get("professora") != real["professora"] or registrado.get("sala") != real["sala"]:
                            divergencias.append({
                                "Aluna": aluna,
                                "Real (última escala salva)": f"{real['professora']} — {real['sala']} ({real['data']})",
                                "Na memória do sistema": (f"{registrado.get('professora')} — {registrado.get('sala')}"
                                                           if registrado else "Sem registro nenhum")
                            })

                    st.session_state["_diag_divergencias"] = divergencias
                    st.session_state["_diag_itens_com_data"] = itens_com_data

                if "_diag_divergencias" in st.session_state:
                    divergencias = st.session_state["_diag_divergencias"]
                    if divergencias:
                        st.warning(f"⚠️ {len(divergencias)} divergência(s) encontrada(s):")
                        st.dataframe(pd.DataFrame(divergencias), use_container_width=True, hide_index=True)

                        if st.button("🔧 Corrigir automaticamente (reconstruir a partir das escalas reais)", type="primary", use_container_width=True):
                            itens_com_data = st.session_state["_diag_itens_com_data"]
                            estado_ciclo_novo = {}
                            ultima_alocacao_nova = {}
                            todas_alunas_sistema = sorted([a for turma in TURMAS.values() for a in turma])

                            for d_obj, data_str, escala in itens_com_data:
                                for linha in escala:
                                    aluna = linha.get("Aluna")
                                    if not aluna:
                                        continue
                                    for chave, valor in linha.items():
                                        if chave == "Aluna":
                                            continue
                                        v_str = str(valor)
                                        if "|" not in v_str:
                                            continue
                                        sala_parte = v_str.split("|")[0].strip().upper()
                                        if sala_parte in ("SALA 8", "SALA 9") or "SECRETARIA" in sala_parte or "TODAS" in v_str.upper():
                                            continue
                                        if not sala_parte.startswith("SALA"):
                                            continue
                                        professora = v_str.split("|")[-1].strip()
                                        if not professora:
                                            continue

                                        if professora not in estado_ciclo_novo:
                                            estado_ciclo_novo[professora] = {"alunas_dadas": [], "ciclo_num": 1}
                                        # Reconstitui o mesmo comportamento do gerador: se ela já
                                        # tinha dado aula pra todo mundo, reinicia o ciclo antes de somar essa.
                                        if set(estado_ciclo_novo[professora]["alunas_dadas"]) >= set(todas_alunas_sistema):
                                            estado_ciclo_novo[professora]["alunas_dadas"] = []
                                            estado_ciclo_novo[professora]["ciclo_num"] += 1
                                        if aluna not in estado_ciclo_novo[professora]["alunas_dadas"]:
                                            estado_ciclo_novo[professora]["alunas_dadas"].append(aluna)

                                        ultima_alocacao_nova[aluna] = {"professora": professora, "sala": sala_parte, "data": data_str}

                            db_salvar_rodizio_ciclo(estado_ciclo_novo)
                            db_salvar_ultima_alocacao(ultima_alocacao_nova)
                            st.success("✅ Reconstruído com sucesso a partir de todas as escalas salvas!")
                            del st.session_state["_diag_divergencias"]
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.success("✅ Tudo consistente! A memória do rodízio bate com a última escala salva de cada aluna.")

            # --- ABA 6: TURMAS E PESSOAS (CADASTRO) ---
            with tab_pessoas:
                sub_alunas, sub_profs = st.tabs(["🎀 Alunas e Turmas", "👩‍🏫 Professoras"])

                # --- ALUNAS E TURMAS ---
                with sub_alunas:
                    st.caption("As turmas mudam de semestre em semestre — edite a turma de cada aluna aqui quando precisar.")
                    alunas_raw = db_get_alunas_todas()
                    turmas_existentes = sorted(set([a.get("turma") for a in alunas_raw if a.get("turma")])) or ["Turma 1"]

                    st.markdown("#### ➕ Adicionar Aluna")
                    with st.form("form_add_aluna", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        nome_nova_aluna = c1.text_input("Nome completo (igual ao usado nos registros):", placeholder="Ex: Maria S - Vila Verde")
                        turma_op = c2.selectbox("Turma:", turmas_existentes + ["+ Nova turma..."])
                        nova_turma_nome = c2.text_input("Nome da nova turma:") if turma_op == "+ Nova turma..." else None
                        c3, c4 = st.columns(2)
                        login_nova_aluna = c3.text_input("Login de acesso (opcional):", placeholder="Ex: maria.s")
                        senha_nova_aluna = c4.text_input("Senha de acesso (opcional):", value="123")
                        if st.form_submit_button("Adicionar Aluna", use_container_width=True):
                            turma_final = nova_turma_nome.strip() if turma_op == "+ Nova turma..." and nova_turma_nome else turma_op
                            if not nome_nova_aluna.strip():
                                st.error("Informe o nome da aluna.")
                            else:
                                try:
                                    dados_nova_aluna = {"nome": nome_nova_aluna.strip(), "turma": turma_final, "ativo": True}
                                    if login_nova_aluna.strip():
                                        dados_nova_aluna["login"] = login_nova_aluna.strip().lower()
                                        dados_nova_aluna["senha"] = senha_nova_aluna
                                    supabase.table("alunas").insert(dados_nova_aluna).execute()
                                    st.success(f"✅ {nome_nova_aluna} adicionada em {turma_final}!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    if login_nova_aluna.strip() and "login" in str(e).lower():
                                        st.error("⚠️ A tabela 'alunas' ainda não tem as colunas 'login'/'senha'. "
                                                  "Rode este SQL no Supabase (SQL Editor) e tente de novo:\n\n"
                                                  "```sql\nalter table alunas add column if not exists login text;\n"
                                                  "alter table alunas add column if not exists senha text;\n```")
                                    else:
                                        st.error(f"Erro ao adicionar (nome já existe?): {e}")

                    st.divider()
                    st.markdown("#### ✏️ Editar Turma / Ativar-Desativar")
                    if alunas_raw:
                        for a in sorted(alunas_raw, key=lambda x: (x.get("turma") or "Sem Turma", x["nome"])):
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 2, 1])
                                c1.write(("🟢 " if a.get("ativo", True) else "⚪ ") + a["nome"])
                                lista_opcoes_turma = turmas_existentes + ["+ Nova turma..."]
                                idx_t = lista_opcoes_turma.index(a.get("turma")) if a.get("turma") in lista_opcoes_turma else 0
                                nova_turma_sel = c2.selectbox("Turma", lista_opcoes_turma, index=idx_t, key=f"turma_{a['nome']}", label_visibility="collapsed")
                                if nova_turma_sel == "+ Nova turma...":
                                    nova_turma_sel = c2.text_input("Nome da turma:", key=f"nt_{a['nome']}")
                                if c3.button("💾", key=f"sv_{a['nome']}", help="Salvar turma"):
                                    supabase.table("alunas").update({"turma": nova_turma_sel}).eq("nome", a["nome"]).execute()
                                    st.cache_data.clear(); st.rerun()
                                acao = "Desativar" if a.get("ativo", True) else "Reativar"
                                if c3.button(acao, key=f"tg_{a['nome']}"):
                                    supabase.table("alunas").update({"ativo": not a.get("ativo", True)}).eq("nome", a["nome"]).execute()
                                    st.cache_data.clear(); st.rerun()

                                with st.expander(f"🔑 Acesso de {a['nome']}"):
                                    cl1, cl2, cl3 = st.columns([2, 2, 1])
                                    login_atual = cl1.text_input("Login:", value=a.get("login") or "", key=f"log_{a['nome']}")
                                    nova_senha_al = cl2.text_input("Nova senha:", key=f"sena_{a['nome']}", placeholder="deixe em branco p/ manter")
                                    if cl3.button("💾", key=f"svlog_{a['nome']}", help="Salvar acesso"):
                                        upd = {"login": login_atual.strip().lower()}
                                        if nova_senha_al:
                                            upd["senha"] = nova_senha_al
                                        try:
                                            supabase.table("alunas").update(upd).eq("nome", a["nome"]).execute()
                                            st.success("Acesso atualizado!")
                                            st.cache_data.clear(); st.rerun()
                                        except Exception as e:
                                            st.error("⚠️ A tabela 'alunas' ainda não tem as colunas 'login'/'senha'. "
                                                      "Rode este SQL no Supabase (SQL Editor) e tente de novo:\n\n"
                                                      "```sql\nalter table alunas add column if not exists login text;\n"
                                                      "alter table alunas add column if not exists senha text;\n```")
                                            st.caption(f"Detalhe técnico: {e}")
                    else:
                        st.info("Nenhuma aluna cadastrada ainda.")

                # --- PROFESSORAS ---
                with sub_profs:
                    st.caption("Cada professora precisa de um login e senha próprios pra entrar no sistema.")
                    profs_raw = db_get_professoras_todas()

                    st.markdown("#### ➕ Adicionar Professora")
                    with st.form("form_add_prof", clear_on_submit=True):
                        c1, c2, c3 = st.columns(3)
                        nome_nova_prof = c1.text_input("Nome:", placeholder="Ex: Juliana")
                        login_nova_prof = c2.text_input("Login:", placeholder="Ex: juliana")
                        senha_nova_prof = c3.text_input("Senha:", value="456")
                        if st.form_submit_button("Adicionar Professora", use_container_width=True):
                            if not nome_nova_prof.strip() or not login_nova_prof.strip():
                                st.error("Informe nome e login.")
                            else:
                                try:
                                    supabase.table("professoras").insert({
                                        "nome": nome_nova_prof.strip(), "login": login_nova_prof.strip().lower(),
                                        "senha": senha_nova_prof, "ativo": True
                                    }).execute()
                                    st.success(f"✅ {nome_nova_prof} adicionada!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao adicionar (nome ou login já existe?): {e}")

                    st.divider()
                    st.markdown("#### ✏️ Editar / Ativar-Desativar")
                    if profs_raw:
                        for p in sorted(profs_raw, key=lambda x: x["nome"]):
                            with st.container(border=True):
                                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                                c1.write(("🟢 " if p.get("ativo", True) else "⚪ ") + p["nome"])
                                c2.caption(f"Login: {p.get('login', '---')}")
                                nova_senha = c3.text_input("Nova senha:", key=f"sen_{p['nome']}", placeholder="deixe em branco p/ manter")
                                if c4.button("💾", key=f"svp_{p['nome']}", help="Salvar nova senha"):
                                    if nova_senha:
                                        supabase.table("professoras").update({"senha": nova_senha}).eq("nome", p["nome"]).execute()
                                        st.success("Senha atualizada!")
                                        st.cache_data.clear(); st.rerun()
                                acao = "Desativar" if p.get("ativo", True) else "Reativar"
                                if c4.button(acao, key=f"tgp_{p['nome']}"):
                                    supabase.table("professoras").update({"ativo": not p.get("ativo", True)}).eq("nome", p["nome"]).execute()
                                    st.cache_data.clear(); st.rerun()
                    else:
                        st.info("Nenhuma professora cadastrada ainda.")

# ============================================================
# MÓDULO ALUNA - LIÇÕES PENDENTES + CONTROLE DE ESTUDO DIÁRIO
# ============================================================
elif menu == "🎓 Minhas Lições":
    st.header(f"🎓 Olá, {st.session_state.nome_logado}!")
    minha_aluna = st.session_state.nome_logado

    tab_licoes_aluna, tab_estudo_aluna = st.tabs(["📚 Minhas Lições de Casa", "✅ Controle de Estudo Diário"])

    with tab_licoes_aluna:
        df_hist_aluna = pd.DataFrame(db_get_historico())
        pendentes_aluna = pd.DataFrame()
        if not df_hist_aluna.empty:
            mask_al = (
                (df_hist_aluna['Aluna'] == minha_aluna) &
                (df_hist_aluna['Tipo'].str.startswith("Casa_", na=False)) &
                (~df_hist_aluna['Status'].isin(STATUS_OK_LICAO))
            )
            pendentes_aluna = df_hist_aluna[mask_al].copy()

        _renderizar_pendencias_casa(pendentes_aluna)

    with tab_estudo_aluna:
        st.subheader("✅ Registrar meu estudo do dia")
        if not db_tabela_estudo_existe():
            st.error("⚠️ A tabela 'estudo_diario' ainda não existe no Supabase. Peça pra secretaria criar essa "
                      "tabela (colunas: id, aluna, data, horarios — com uma chave única em aluna+data) antes de usar essa aba.")
        else:
            data_estudo = st.date_input("Dia:", datetime.now(), key="data_estudo_aluna")
            data_estudo_str = data_estudo.strftime("%d/%m/%Y")

            estudo_todos = db_get_estudo_diario()
            registro_existente = next((e for e in estudo_todos if e.get("aluna") == minha_aluna and e.get("data") == data_estudo_str), None)
            horarios_ja_marcados = registro_existente.get("horarios", []) if registro_existente else []

            horarios_marcados = st.multiselect(
                "Em quais horários você estudou nesse dia?",
                HORARIOS_ESTUDO, default=horarios_ja_marcados, key="horarios_estudo_aluna"
            )

            if st.button("💾 Salvar estudo do dia", use_container_width=True):
                if db_salvar_estudo_diario(minha_aluna, data_estudo_str, horarios_marcados):
                    st.success("✅ Estudo registrado!")
                    st.rerun()

            st.divider()
            st.subheader("📅 Meu histórico de estudo (últimos 30 dias)")
            hoje_dt = datetime.now().date()
            meus_estudos = [e for e in estudo_todos if e.get("aluna") == minha_aluna]
            for e in sorted(meus_estudos, key=lambda x: x.get("data", ""), reverse=True)[:30]:
                horarios_e = e.get("horarios") or []
                if horarios_e:
                    st.write(f"😊 **{e.get('data')}** — estudou: {', '.join(horarios_e)}")
                else:
                    st.write(f"😢 **{e.get('data')}** — não estudou")

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
                metodos_filtrados = df_metodos_db[df_metodos_db['categoria'] == tipo_aula]['nome'].tolist() if not df_metodos_db.empty else []
                st.markdown(f"### 📝 Registro: {tipo_aula}")

                # ============================================================
                # PRÁTICA — pode ter um ou mais métodos pra corrigir/verificar,
                # além da apostila. Cada método é conferido separadamente.
                # ============================================================
                if tipo_aula == "Prática":
                    st.caption("👀 Conferência de hoje: o que a aluna trouxe pronto (ou não) pra essa aula. A lição de casa pra próxima aula fica mais abaixo.")
                    opcoes_materiais = ["Apostila"] + metodos_filtrados
                    materiais_hoje = st.multiselect("Métodos/Apostila conferidos hoje:", opcoes_materiais, key=f"mm_{d_sel['id']}")

                    if not materiais_hoje:
                        st.info("Selecione ao menos um método ou a apostila trabalhada hoje.")
                    else:
                        with st.form(key=f"form_pratica_{d_sel['id']}_{'_'.join(materiais_hoje)}"):
                            registros_material = {}
                            for mat in materiais_hoje:
                                st.markdown(f"#### 🎼 {mat}")

                                # Resumo da última aula (qualquer data anterior) com esse
                                # material, pra quem está dando aula hoje saber onde a
                                # aluna parou — útil principalmente quando é outra
                                # professora (por causa do rodízio) que dá aula dela hoje.
                                anterior_m = pd.DataFrame()
                                if not df_hist_local.empty:
                                    anterior_m = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) &
                                                                (df_hist_local['Data'] != dt_str) &
                                                                (df_hist_local['Tipo'] == "Analise_Prática") &
                                                                (df_hist_local['Licao_Atual'].str.startswith(f"{mat}:", na=False))].copy()
                                if not anterior_m.empty:
                                    anterior_m['_dt_tmp'] = pd.to_datetime(anterior_m['Data'], format='%d/%m/%Y', errors='coerce')
                                    anterior_m = anterior_m.sort_values('_dt_tmp', ascending=False)
                                    reg_ant = anterior_m.iloc[0]
                                    lic_ant_txt = reg_ant.get('Licao_Atual', '')
                                    lic_ant = lic_ant_txt.split(':', 1)[-1].strip() if ':' in lic_ant_txt else lic_ant_txt
                                    difs_ant = [d for d in (reg_ant.get('Dificuldades') or []) if d and d != "Não apresentou dificuldades"]
                                    txt_resumo = f"📋 **Última aula ({reg_ant.get('Data')}):** {lic_ant}"
                                    if difs_ant:
                                        txt_resumo += f" — ⚠️ dificuldades: {', '.join(difs_ant)}"
                                    else:
                                        txt_resumo += " — ✅ sem dificuldades"
                                    st.caption(txt_resumo)
                                else:
                                    st.caption("📋 Nenhuma aula anterior encontrada com esse material.")

                                dados_mat = {}
                                if not df_hist_local.empty:
                                    f_m = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) &
                                                        (df_hist_local['Data'] == dt_str) &
                                                        (df_hist_local['Tipo'] == "Analise_Prática") &
                                                        (df_hist_local['Licao_Atual'].str.startswith(f"{mat}:", na=False))]
                                    if not f_m.empty: dados_mat = f_m.iloc[-1].to_dict()

                                lic_db = dados_mat.get('Licao_Atual', "").split(":")[-1].strip() if ":" in dados_mat.get('Licao_Atual', "") else ""
                                pagina = st.text_input(f"Página/lição ({mat}):", value=lic_db, key=f"pag_{mat}_{d_sel['id']}")
                                fez_licao = st.selectbox(f"A aluna fez a lição de casa desse material?", ["Sim", "Não", "Parcial"], key=f"fez_{mat}_{d_sel['id']}")

                                difs_db_m = dados_mat.get('Dificuldades', []) or []
                                cols_d = st.columns(3)
                                registros_material[mat] = {
                                    "pagina": pagina, "fez": fez_licao,
                                    "difs": [d for i, d in enumerate(DIF_PRATICA) if cols_d[i % 3].checkbox(d, value=(d in difs_db_m), key=f"dp_{mat}_{i}_{d_sel['id']}")]
                                }
                                st.divider()

                            st.subheader("🏠 Lição de Casa para a próxima aula")
                            st.caption("📬 O que marcar com 📖 vai para a fila de correção da secretaria. O que marcar com 🎼 é só acompanhamento seu (método) — mas precisa preencher, não é opcional.")
                            apostila_casa = st.text_input("📖 Apostila (página/lição — vai para a secretaria):", key=f"aph_{d_sel['id']}")

                            metodos_do_dia = [m for m in materiais_hoje if m != "Apostila"]
                            paginas_metodo_casa = {}
                            for mc in metodos_do_dia:
                                paginas_metodo_casa[mc] = st.text_input(f"🎼 Lição de casa — {mc}:", key=f"mcp_{mc}_{d_sel['id']}")

                            metodos_extra = st.multiselect(
                                "🎼 Outro(s) método(s) pra passar lição (além dos conferidos hoje):",
                                [m for m in metodos_filtrados if m not in metodos_do_dia], key=f"mch_{d_sel['id']}"
                            )
                            for mc in metodos_extra:
                                paginas_metodo_casa[mc] = st.text_input(f"🎼 Lição de casa — {mc}:", key=f"mcpx_{mc}_{d_sel['id']}")

                            obs_geral = st.text_area("Observações Pedagógicas:", key=f"obs_{d_sel['id']}")

                            if st.form_submit_button("💾 SALVAR E CONGELAR ANÁLISE", use_container_width=True):
                                faltando = [mc for mc in metodos_do_dia if not paginas_metodo_casa.get(mc, "").strip()]
                                if faltando:
                                    st.error(f"⚠️ Preencha a lição de casa do(s) método(s): {', '.join(faltando)}. Não é opcional.")
                                else:
                                    for al_f in als_selecionadas:
                                        for mat, dados in registros_material.items():
                                            difs_reais = [d for d in dados["difs"] if d != "Não apresentou dificuldades"]
                                            status_analise = "Realizada - com dificuldades" if difs_reais else "Realizada - sem pendência"
                                            db_save_historico({
                                                "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                                "Tipo": "Analise_Prática",
                                                "Licao_Atual": f"{mat}: {dados['pagina']}",
                                                "Licao_Casa": f"Fez a lição de casa: {dados['fez']}",
                                                "Dificuldades": dados["difs"], "Observacao": obs_geral,
                                                "Status": status_analise
                                            })
                                        if apostila_casa:
                                            db_save_historico({
                                                "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                                "Tipo": "Casa_Apostila", "Licao_Atual": "Definido", "Licao_Casa": apostila_casa,
                                                "Dificuldades": [], "Observacao": obs_geral, "Status": "Pendente"
                                            })
                                        for mc, pag in paginas_metodo_casa.items():
                                            if pag:
                                                db_save_historico({
                                                    "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                                    "Tipo": f"Casa_Metodo_{mc}", "Licao_Atual": "Definido", "Licao_Casa": pag,
                                                    "Dificuldades": [], "Observacao": obs_geral, "Status": "Pendente"
                                                })
                                    st.success("✅ Registro concluído com sucesso!")
                                    time.sleep(1)
                                    st.rerun()

                # ============================================================
                # TEORIA e SOLFEJO — aula de turma, dificuldade compartilhada.
                # Teoria: lição de casa em Folha Avulsa (secretaria corrige, a
                # não ser que a professora corrija ela mesma) ou Apostila
                # alternativa (não entra na fila da secretaria).
                # Solfejo: trabalha com MSA, sem correção da secretaria.
                # ============================================================
                else:
                    # Teoria/Solfejo: campo livre — a professora escreve o que usou
                    # (MSA, folha extra, apostila, método, etc.), sem lista fixa. Só a
                    # Prática usa a seleção dos métodos cadastrados (aba Configurar Métodos).
                    mat_focado = st.text_input("Material usado hoje:", key=f"mat_{d_sel['id']}", placeholder="Ex: MSA, Folha Extra, Apostila...").strip()

                    dados_hoje = {}
                    if not df_hist_local.empty and mat_focado:
                        f_ex = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) &
                                             (df_hist_local['Data'] == dt_str) &
                                             (df_hist_local['Tipo'] == f"Analise_{tipo_aula}") &
                                             (df_hist_local['Licao_Atual'].str.startswith(f"{mat_focado}:", na=False))]
                        if not f_ex.empty: dados_hoje = f_ex.iloc[-1].to_dict()

                    # Sem st.form aqui: "quem corrige a lição de casa" precisa aparecer/
                    # sumir na hora conforme a professora marca, e um st.form só reage
                    # depois do botão de envio ser clicado — então essa tela toda usa
                    # widgets normais, com um botão comum de salvar no final.

                    lic_db = dados_hoje.get('Licao_Atual', "").split(":")[-1].strip() if ":" in dados_hoje.get('Licao_Atual', "") else ""
                    lic_hoje = st.text_input("Página/Lição trabalhada:", value=lic_db, key=f"lich_{d_sel['id']}")

                    st.markdown("**Dificuldades (compartilhada pra turma):**")
                    lista_difs = DIF_TEORIA if tipo_aula == "Teoria" else DIF_SOLFEJO
                    difs_db = dados_hoje.get('Dificuldades', []) or []
                    cols_d = st.columns(3)
                    difs_sel = [
                        d for i, d in enumerate(lista_difs)
                        if cols_d[i % 3].checkbox(d, value=(d in difs_db), key=f"d_v58_{i}_{d_sel['id']}_{mat_focado}_{dt_str}")
                    ]

                    st.divider()
                    st.subheader("🏠 Lição de Casa")
                    st.caption("📬 O que marcar com 📖 abaixo vai para a fila de correção da secretaria. O que marcar com 🎼 é só acompanhamento seu (método) e não vai para a secretaria.")
                    tarefas_casa = {}
                    quem_corrige = None

                    if tipo_aula == "Teoria":
                        tipo_casa_sel = st.radio("📖 Tipo de lição de casa (vai para a secretaria):", ["Folha Avulsa", "Apostila"], horizontal=True, key=f"tc_{d_sel['id']}")
                        conteudo_casa = st.text_input(f"🏠 {tipo_casa_sel}:", key=f"cc_{d_sel['id']}")

                        # Só decide QUEM vai corrigir — a correção em si nunca acontece
                        # agora (a aluna ainda vai fazer a lição em casa). Se for "Eu
                        # mesma", essa pendência aparece pra ela corrigir na aula
                        # seguinte, no painel de "Lições pendentes pra você corrigir".
                        quem_corrige = st.radio("Quem corrige essa lição de casa (na próxima aula)?", ["Secretaria", "Eu mesma (em sala)"], horizontal=True, key=f"qc_{d_sel['id']}")

                        sufixo = "" if quem_corrige == "Secretaria" else "_Prof"
                        # Apostila é sempre apostila (mesmo tipo usado na Prática) — Folha
                        # Avulsa vira Casa_Teoria. Os dois entram na fila da secretaria,
                        # a não ser que a professora marque "Eu mesma" (aí ganha o sufixo _Prof).
                        base_tipo_casa = "Apostila" if tipo_casa_sel == "Apostila" else "Teoria"
                        if conteudo_casa: tarefas_casa[f"{base_tipo_casa}{sufixo}"] = conteudo_casa
                    else:  # Solfejo
                        conteudo_casa = st.text_input("🎼 MSA (lição de casa, sem correção da secretaria):", key=f"cc_{d_sel['id']}")
                        if conteudo_casa: tarefas_casa["MSA"] = conteudo_casa

                    # Método — sempre precisa informar a lição de casa (não é opcional),
                    # só não entra na correção da secretaria.
                    if metodos_filtrados:
                        metodo_casa_sel = st.selectbox("🎼 Método:", metodos_filtrados, key=f"met_casa_{d_sel['id']}")
                        metodo_casa_pag = st.text_input(f"🎼 Lição de casa — {metodo_casa_sel}:", key=f"met_pag_{d_sel['id']}")
                    else:
                        metodo_casa_sel, metodo_casa_pag = None, ""
                        st.info("ℹ️ Nenhum método cadastrado pra essa categoria ainda (cadastre em ⚙️ Configurar Métodos).")

                    obs_db = dados_hoje.get('Observacao', "")
                    obs_geral = st.text_area("Observações Pedagógicas:", value=obs_db, key=f"obsg_{d_sel['id']}")

                    if st.button("💾 SALVAR E CONGELAR ANÁLISE", use_container_width=True, key=f"btnsalvar_{d_sel['id']}"):
                        if not mat_focado:
                            st.error("Informe o material usado hoje antes de salvar.")
                        elif metodos_filtrados and not metodo_casa_pag.strip():
                            st.error(f"⚠️ Preencha a lição de casa do método ({metodo_casa_sel}). Não é opcional.")
                        else:
                            if metodo_casa_sel and metodo_casa_pag:
                                tarefas_casa[f"Metodo_{metodo_casa_sel}"] = metodo_casa_pag
                            difs_reais = [d for d in difs_sel if d != "Não apresentou dificuldades"]
                            status_analise = "Realizada - com dificuldades" if difs_reais else "Realizada - sem pendência"
                            for al_f in als_selecionadas:
                                db_save_historico({
                                    "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                    "Tipo": f"Analise_{tipo_aula}",
                                    "Licao_Atual": f"{mat_focado}: {lic_hoje}",
                                    "Licao_Casa": "---", "Dificuldades": difs_sel,
                                    "Observacao": obs_geral, "Status": status_analise
                                })
                                for mat_nome, conteudo in tarefas_casa.items():
                                    if conteudo:
                                        # Toda lição de casa nasce "Pendente" — ela só será
                                        # corrigida na aula seguinte, seja pela secretaria
                                        # (aba Controle de Lições) ou pela própria professora
                                        # (painel "Lições pendentes pra você corrigir").
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
    
    tab_aluna, tab_quadro = st.tabs(["👤 Prontuário Individual", "🏆 Quadro de Desempenho"])

    with tab_aluna:
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
                # Filtro por "começa com Analise_" (não "contém Teoria/Solfejo/Prática"),
                # pra não confundir com Casa_Teoria_Prof — que também contém "Teoria" no
                # nome mas é lição de casa, não aula analisada, e sempre tem Dificuldades
                # vazio, o que inflava o aproveitamento artificialmente.
                pedag_rows = df_aluna[df_aluna['Tipo'].str.startswith("Analise_", na=False)].copy()

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

                # --- ESTUDO EM CASA (registrado pela própria aluna) ---
                def _data_no_periodo(data_str):
                    try:
                        d = datetime.strptime(data_str, "%d/%m/%Y").date()
                        return data_ini <= d <= data_fim
                    except Exception:
                        return False

                estudo_todos_analitico = db_get_estudo_diario() if db_tabela_estudo_existe() else []
                estudos_aluna_periodo = [e for e in estudo_todos_analitico
                                          if e.get("aluna") == aluna_sel and _data_no_periodo(e.get("data", ""))]
                dias_com_estudo = sum(1 for e in estudos_aluna_periodo if e.get("horarios"))
                dias_sem_estudo = sum(1 for e in estudos_aluna_periodo if not e.get("horarios"))
                total_dias_estudo_reg = len(estudos_aluna_periodo)
                pct_estudo = int((dias_com_estudo / total_dias_estudo_reg) * 100) if total_dias_estudo_reg > 0 else 0

                # --- 1. RESUMO DE DESEMPENHO (DASHBOARD) ---
                st.subheader(f"📈 Resumo de Desempenho - {aluna_sel}")
                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric("Frequência", f"{int((v_pres+v_just)/len(resumo_dias)*100) if len(resumo_dias)>0 else 0}%")
                k2.metric("Aulas/Chamadas", len(resumo_dias))
                k3.metric("Faltas (N/J)", f"{v_falt} / {v_just}")
                k4.metric("Aproveitamento", f"{aprov_valor}%")
                cara_estudo = "😊" if pct_estudo >= 70 else ("😐" if pct_estudo >= 40 else "😢")
                k5.metric(f"Estudo em casa {cara_estudo}", f"{pct_estudo}%" if total_dias_estudo_reg > 0 else "sem dados")

                # --- 1.5 CALENDÁRIO DE ESTUDO (dia a dia, com carinhas) ---
                if estudos_aluna_periodo:
                    with st.expander(f"📅 Ver dia a dia do estudo em casa ({dias_com_estudo} 😊 / {dias_sem_estudo} 😢)"):
                        for e in sorted(estudos_aluna_periodo, key=lambda x: datetime.strptime(x.get("data", "01/01/2000"), "%d/%m/%Y"), reverse=True):
                            horarios_e = e.get("horarios") or []
                            if horarios_e:
                                st.write(f"😊 **{e.get('data')}** — estudou: {', '.join(horarios_e)}")
                            else:
                                st.write(f"😢 **{e.get('data')}** — não estudou")

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
                    st.markdown("### 📚 Lições Pendentes (correção da secretaria)")
                    # Só entra aqui o que a secretaria de fato corrige: apostila da prática e folhas de teoria
                    pendencias = df_aluna[(df_aluna['Tipo'].isin(TIPOS_CORRECAO_SECRETARIA)) &
                                          (~df_aluna['Status'].str.contains("Realizada", na=False))]
                    if not pendencias.empty:
                        for _, p in pendencias.iterrows():
                            rotulo = p['Tipo'].replace('Casa_', '')
                            st.warning(f"📖 **{rotulo}**: {p.get('Licao_Casa', '---')} (Status: {p.get('Status', '---')})")
                    else:
                        st.success("✅ Apostila e Teoria em dia.")

                # --- 3.5 TODAS AS LIÇÕES DE CASA (apostila, método, teoria) — NOVO ---
                st.divider()
                st.markdown("### 🏠 Todas as Lições de Casa do Período")
                casa_rows = df_aluna[df_aluna['Tipo'].str.startswith("Casa_", na=False)].sort_values('dt_obj', ascending=False)
                if not casa_rows.empty:
                    for _, c in casa_rows.iterrows():
                        rotulo = (c['Tipo'].replace("Casa_Metodo_", "Método: ")
                                  .replace("Casa_Apostila_Prof", "Apostila (corrigida pela professora)")
                                  .replace("Casa_Teoria_Prof", "Folha Avulsa (corrigida pela professora)")
                                  .replace("Casa_Teoria", "Folha Avulsa (Teoria)")
                                  .replace("Casa_Apostila", "Apostila")
                                  .replace("Casa_MSA", "MSA")
                                  .replace("Casa_", ""))
                        corrigida_pela_secretaria = c['Tipo'] in TIPOS_CORRECAO_SECRETARIA
                        icone = "🏢" if corrigida_pela_secretaria else "👩‍🏫"
                        with st.container(border=True):
                            st.write(f"{icone} **{rotulo}** ({c['Data']}) — {c.get('Licao_Casa', '---')}")
                            if corrigida_pela_secretaria:
                                st.caption(f"Status da correção: {c.get('Status', '---')}")
                else:
                    st.info("Nenhuma lição de casa registrada nesse período.")

                # --- 4. FEEDBACK DETALHADO (PROFESSORAS E SECRETARIA) ---
                st.divider()
                tab_p, tab_s = st.tabs(["👩‍🏫 Feedback Pedagógico", "🏢 Notas da Secretaria"])
            
                with tab_p:
                    aulas = df_aluna[df_aluna['Tipo'].str.startswith("Analise_", na=False)]
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

                # --- 4.5 EVOLUÇÃO DAS DIFICULDADES AO LONGO DO TEMPO ---
                st.divider()
                st.markdown("### 📉 Evolução das Dificuldades")
                st.caption("Cada barra mostra a contagem real de uma dificuldade naquele mês — barras lado a lado, não empilhadas, pra não misturar o total de uma com o de outra.")

                # Só conta a partir dos registros de aula de fato (Analise_Prática/Teoria/Solfejo).
                # Registros de Casa_/Chamada nunca têm lista de Dificuldades preenchida, mas
                # filtrar explicitamente deixa o dado de origem claro e evita qualquer contagem
                # vinda de um lugar que não devia.
                aulas_aluna = df_aluna[df_aluna['Tipo'].str.startswith("Analise_", na=False)]

                linhas_evolucao = []
                for _, row in aulas_aluna.iterrows():
                    mes_ano = row['dt_obj'].strftime("%Y-%m")
                    lista_dif = row.get('Dificuldades')
                    if isinstance(lista_dif, list):
                        for d_item in lista_dif:
                            if d_item and d_item != "Não apresentou dificuldades" and d_item != "Não participou da aula":
                                linhas_evolucao.append({"Mês": mes_ano, "Dificuldade": d_item})

                if linhas_evolucao:
                    df_evol = pd.DataFrame(linhas_evolucao)
                    meses_ordenados = sorted(df_evol['Mês'].unique())
                    contagem = df_evol.groupby(['Mês', 'Dificuldade']).size().reset_index(name='Ocorrências')

                    fig_evol = px.bar(
                        contagem, x="Mês", y="Ocorrências", color="Dificuldade",
                        barmode="group",  # barras lado a lado (verticais), não empilhadas
                        category_orders={"Mês": meses_ordenados},
                        title="Quantas vezes cada dificuldade apareceu, por mês"
                    )
                    fig_evol.update_layout(xaxis_title="Mês", yaxis_title="Nº de ocorrências", legend_title="Dificuldade")
                    fig_evol.update_yaxes(dtick=1)  # eixo em números inteiros (são contagens, não %)
                    st.plotly_chart(fig_evol, use_container_width=True)

                    # Comparação real: primeira metade do período vs segunda metade
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

                    # --- Sugestão pra próxima aula, baseada só no que está registrado ---
                    # Olha apenas o mês mais recente com registro — não é diagnóstico
                    # novo, é o próprio dado já lançado pela professora, só destacado.
                    mes_mais_recente = meses_ordenados[-1]
                    difs_mes_recente = df_evol[df_evol['Mês'] == mes_mais_recente]['Dificuldade'].value_counts()
                    if not difs_mes_recente.empty:
                        dif_top = difs_mes_recente.index[0]
                        qtd_top = int(difs_mes_recente.iloc[0])
                        st.info(f"💡 **Sugestão para a próxima aula:** a dificuldade mais registrada em {mes_mais_recente} foi "
                                f"**\"{dif_top}\"** ({qtd_top}x). Vale reforçar esse ponto especificamente na próxima aula, "
                                f"antes de avançar de conteúdo.")
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

    # --- ABA 2: QUADRO DE DESEMPENHO (TODAS AS ALUNAS, POR MATÉRIA) ---
    with tab_quadro:
        st.markdown("### 🏆 Quadro de Desempenho — Todas as Alunas")
        st.caption("🥇 Ouro: indo muito bem | 🥈 Prata: indo bem | 🥉 Bronze: precisa de atenção (ou ainda sem registros — toda aluna recebe uma medalha)")

        c_q1, c_q2 = st.columns(2)
        data_ini_q = c_q1.date_input("De:", datetime.now().date() - timedelta(days=30), key="quadro_ini")
        data_fim_q = c_q2.date_input("Até:", datetime.now().date(), key="quadro_fim")

        df_periodo_q = df_base[(df_base['dt_obj'].dt.date >= data_ini_q) & (df_base['dt_obj'].dt.date <= data_fim_q)]

        estudo_todos_quadro = db_get_estudo_diario() if db_tabela_estudo_existe() else []

        def _estudo_no_periodo_quadro(data_str):
            try:
                d = datetime.strptime(data_str, "%d/%m/%Y").date()
                return data_ini_q <= d <= data_fim_q
            except Exception:
                return False

        def calcular_medalha(score, tem_dados):
            if not tem_dados:
                return "🥉", "Bronze", 0
            if score >= 80:
                return "🥇", "Ouro", score
            elif score >= 50:
                return "🥈", "Prata", score
            else:
                return "🥉", "Bronze", score

        linhas_quadro = []
        for al in ALUNAS_LISTA:
            linha = {"Aluna": al}
            for materia in ["Prática", "Teoria", "Solfejo"]:
                regs = df_periodo_q[(df_periodo_q['Aluna'] == al) & (df_periodo_q['Tipo'] == f"Analise_{materia}")].copy()
                total = len(regs)
                if total > 0:
                    regs['tem_dificuldade'] = regs['Dificuldades'].apply(_tem_dificuldade_real)
                    sem_dificuldade = int((~regs['tem_dificuldade']).sum())
                    score = round((sem_dificuldade / total) * 100)
                else:
                    score = 0
                icone, nome_medalha, score_final = calcular_medalha(score, total > 0)
                linha[materia] = f"{icone} {nome_medalha}" + (f" ({score_final}%)" if total > 0 else " (sem registros)")

            # Coluna de estudo em casa (registrado pela própria aluna)
            estudos_al = [e for e in estudo_todos_quadro if e.get("aluna") == al and _estudo_no_periodo_quadro(e.get("data", ""))]
            if estudos_al:
                dias_ok = sum(1 for e in estudos_al if e.get("horarios"))
                pct = int((dias_ok / len(estudos_al)) * 100)
                face = "😊" if pct >= 70 else ("😐" if pct >= 40 else "😢")
                linha["Estudo em Casa"] = f"{face} {pct}% ({dias_ok}/{len(estudos_al)} dias)"
            else:
                linha["Estudo em Casa"] = "— sem registro"

            linhas_quadro.append(linha)

        df_quadro = pd.DataFrame(linhas_quadro)
        if not df_quadro.empty:
            st.dataframe(df_quadro, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma aluna cadastrada ainda.")

        st.caption(f"📅 Período analisado: {data_ini_q.strftime('%d/%m/%Y')} até {data_fim_q.strftime('%d/%m/%Y')}. A medalha é calculada pela % de aulas sem dificuldade registrada em cada matéria, dentro do período escolhido.")

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
