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
import unicodedata
import json
import time # <--- ESSENCIAL PARA O SLEEP FUNCIONAR
import random

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
    "kamila": {"senha": "456", "perfil": "Kamila", "nome_real": "Kamila"},
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
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamila", "Renata"]
SECRETARIAS_LISTA = ["Esther", "Jéssica", "Larissa", "Lurdes", "Natasha", "Roseli"]
ALUNAS_LISTA = sorted([
    "Annie - Vila Verde", "Ana Marcela S. - Vila Verde", 
    "Caroline C. - Vila Ré", "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá Velha", 
    "Gabrielly V. - Vila Verde", "Heloísa R. - Vila Verde", "Ingrid M. - Pq do Carmo II", 
    "Júlia Cristina - União de Vila Nova", "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá Velha", 
    "Mariana - Vila Araguaia", "Mellina S. - Jardim Lígia", "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", 
    "Rebeca R. - Vila Ré", "Rebecca A. - Vila Verde", "Rebeka S. - Jardim Lígia", 
    "Sarah S. - Vila Verde", "Vitória A. - Vila Verde", "Vitória Bella T. - Vila Verde"
])

CATEGORIAS_LICAO = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
STATUS_LICAO = ["Realizadas - sem pendência", "Realizada - devolvida para refazer", "Não realizada"]

TURMAS = {
    "Turma 1": ["Annie - Vila Verde", "Caroline C. - Vila Ré", "Ingrid M. - Pq do Carmo II",
                "Mariana - Vila Araguaia", "Mellina S. - Jardim Lígia", "Rebecca A. - vVila Verde", 
                "Rebeca R. - Vila Ré", "Rebeka S. - Jardim Lígia"],
    "Turma 2": ["Vitória A. - Vila Verde", "Elisa F. - Vila Verde", "Sarah S. - Vila Verde", "Gabrielly V. - Vila Verde", 
                "Emilly O. - Vila Curuçá Velha", "Julya O. - Vila Curuçá Velha"],
    "Turma 3": ["Heloísa R. - Vila Verde", "Ana Marcela S. - Vila Verde", "Vitória Bella T. - Vila Verde", 
                "Júlia S. - Vila Verde", "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", "Júlia Cristina - União de Vila Nova"]
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
            
    # --- ABA 2: PLANEJAMENTO (GERADOR AUTOMÁTICO V77) ---
with tab_plan:
    st.markdown("### 🗓️ Gestão de Escala")
    
    if 'fixas_escala' not in st.session_state:
        st.session_state.fixas_escala = []

    c1, c2 = st.columns(2)
    mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1, key="mes_plan")
    ano = c2.selectbox("Ano:", [2026, 2027], key="ano_plan")
    
    sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano, mes) 
               for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]
    
    if sabados:
        data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_plan")
        calendario_db = db_get_calendario()
        
        # 1. BUSCA E PREPARAÇÃO DO HISTÓRICO (ESSENCIAL PARA EVITAR KEYERROR)
        historico_raw = db_get_historico()
        df_historico_total = pd.DataFrame(historico_raw)
        
        if not df_historico_total.empty:
            # Garantir que a coluna 'Data' vire 'dt_obj' antes de qualquer sorteio
            df_historico_total['dt_obj'] = pd.to_datetime(df_historico_total['Data'], format="%d/%m/%Y", errors='coerce')
            df_historico_total = df_historico_total.dropna(subset=['dt_obj'])

        if data_sel_str not in calendario_db:
            with st.container(border=True):
                st.warning("⚡ O Rodízio ainda não foi gerado.")
                
                # Seleção de Teoria/Solfejo
                col_t, col_s = st.columns(2)
                with col_t:
                    st.markdown("**📚 Teoria (Sala 8)**")
                    pt2 = st.selectbox("H2", PROFESSORAS_LISTA, index=0, key="t2")
                    pt3 = st.selectbox("H3", PROFESSORAS_LISTA, index=1, key="t3")
                    pt4 = st.selectbox("H4", PROFESSORAS_LISTA, index=2, key="t4")
                with col_s:
                    st.markdown("**🔊 Solfejo (Sala 9)**")
                    ps2 = st.selectbox("H2", PROFESSORAS_LISTA, index=3, key="s2")
                    ps3 = st.selectbox("H3", PROFESSORAS_LISTA, index=4, key="s3")
                    ps4 = st.selectbox("H4", PROFESSORAS_LISTA, index=5, key="s4")
                
                st.divider()
                st.markdown("📌 **Definir Duplas Fixas**")
                cf1, cf2, cf3 = st.columns([2, 2, 1])
                f_alu = cf1.selectbox("Aluna:", ALUNAS_LISTA, key="f_alu_plan")
                f_pro = cf2.selectbox("Professora:", PROFESSORAS_LISTA, key="f_pro_plan")
                if cf3.button("➕ Fixar"):
                    st.session_state.fixas_escala.append({"Aluna": f_alu, "Prof": f_pro})
                
                if st.session_state.fixas_escala:
                    st.caption(f"Fixas: {', '.join([f['Aluna'] for f in st.session_state.fixas_escala])}")
                    if st.button("🗑️ Limpar Fixas"): st.session_state.fixas_escala = []; st.rerun()

                folga_ativa = st.multiselect("Professoras de Folga:", PROFESSORAS_LISTA, key="folgas_dia")

                if st.button("🚀 GERAR ESCALA AUTOMÁTICA", use_container_width=True, type="primary"):
                    mapa = {aluna: {"Aluna": aluna, "Turma": t_nome} for t_nome, alunas in TURMAS.items() for aluna in alunas}
                    for a in mapa: mapa[a][HORARIOS[0]] = "⛪ Igreja"
                    
                    config_h = {
                        HORARIOS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "P_Teo": pt2, "P_Sol": ps2},
                        HORARIOS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "P_Teo": pt3, "P_Sol": ps3},
                        HORARIOS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "P_Teo": pt4, "P_Sol": ps4}
                    }
                    
                    for h in [HORARIOS[1], HORARIOS[2], HORARIOS[3]]:
                        conf = config_h[h]
                        profs_ocupadas_h = [conf["P_Teo"], conf["P_Sol"]] + folga_ativa
                        
                        alunas_pratica_h = []
                        for t_nome, alunas in TURMAS.items():
                            if conf["Teo"] == t_nome:
                                for a in alunas: mapa[a][h] = f"📚 SALA 8 | {conf['P_Teo']}"
                            elif conf["Sol"] == t_nome:
                                for a in alunas: mapa[a][h] = f"🔊 SALA 9 | {conf['P_Sol']}"
                            else:
                                alunas_pratica_h.extend(alunas)
                        
                        random.shuffle(alunas_pratica_h)
                        profs_disponiveis = [p for p in PROFESSORAS_LISTA if p not in profs_ocupadas_h]
                        
                        for aluna in alunas_pratica_h:
                            fixa = next((f for f in st.session_state.fixas_escala if f['Aluna'] == aluna), None)
                            
                            if fixa and fixa['Prof'] in profs_disponiveis:
                                prof_final = fixa['Prof']
                                nota = "📌"
                            else:
                                # LÓGICA DE ANTI-REPETIÇÃO SEGURA
                                ultima_prof = "---"
                                if not df_historico_total.empty:
                                    h_alu = df_historico_total[df_historico_total['Aluna'] == aluna]
                                    if not h_alu.empty:
                                        # dt_obj agora existe garantidamente
                                        ultima_prof = h_alu.sort_values('dt_obj', ascending=False).iloc[0].get('Instrutora', '---')
                                
                                candidatas = [p for p in profs_disponiveis if p != ultima_prof]
                                
                                if profs_disponiveis:
                                    prof_final = random.choice(candidatas if candidatas else profs_disponiveis)
                                    nota = "🎹"
                                else:
                                    prof_final = "⚠️ INDISPONÍVEL"
                                    nota = "❌"

                            # ATRIBUIÇÃO DE SALA SEGURA
                            if prof_final in PROFESSORAS_LISTA:
                                s_idx = (PROFESSORAS_LISTA.index(prof_final) % 7) + 1
                                mapa[aluna][h] = f"{nota} SALA {s_idx} | {prof_final}"
                                if prof_final in profs_disponiveis: profs_disponiveis.remove(prof_final)
                            else:
                                mapa[aluna][h] = f"{prof_final}"

                    supabase.table("calendario").upsert({"id": data_sel_str, "escala": list(mapa.values())}).execute()
                    st.session_state.fixas_escala = []
                    st.success("Rodízio Gerado!"); st.cache_data.clear(); st.rerun()

        else:
            # Exibição da Tabela já gerada
            st.success(f"🗓️ Escala confirmada para {data_sel_str}")
            df_exibir = pd.DataFrame(calendario_db[data_sel_str])
            df_exibir = df_exibir[["Aluna", "Turma"] + HORARIOS]
            df_edt = st.data_editor(df_exibir, use_container_width=True, hide_index=True, key="edt_v77")

            c_s1, c_s2 = st.columns(2)
            if c_s1.button("💾 SALVAR ALTERAÇÕES", use_container_width=True, type="primary"):
                supabase.table("calendario").upsert({"id": data_sel_str, "escala": df_edt.to_dict('records')}).execute()
                st.success("Salvo!"); st.cache_data.clear(); st.rerun()
            
            if c_s2.button("🗑️ Resetar Rodízio", use_container_width=True):
                supabase.table("calendario").delete().eq("id", data_sel_str).execute()
                st.cache_data.clear(); st.rerun()
                
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
# MÓDULO PROFESSORA - V52 (CAMPOS DE PRÁTICA EXPOSTOS)
# ============================================================
elif menu == "👩‍🏫 Minhas Aulas":
    st.header(f"👩‍🏫 Painel da Professora: {st.session_state.nome_logado}")
    
    tab_aula, tab_config = st.tabs(["📝 Registro de Aula", "⚙️ Configurar Métodos"])

    with tab_config:
        try:
            res_m = supabase.table("config_metodos").select("*").execute()
            df_metodos = pd.DataFrame(res_m.data) if res_m.data else pd.DataFrame()
        except: df_metodos = pd.DataFrame()

    with tab_aula:
        instr_sel = st.session_state.get('nome_logado', 'Selecione...')
        dt_input = st.date_input("Data da Aula:", datetime.now(), key="dt_v52")
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

        # --- TELA DE FOLGA BONITINHA ---
        if not aulas_listagem:
            st.balloons() # Animação de bexigas subindo
            
            st.markdown(f"""
                <div class="folga-container">
                    <div class="folga-icon">🎈</div>
                    <h1 class="folga-titulo">Dia de Descanso!</h1>
                    <p class="folga-sub">Olá, <b>{instr_sel}</b>! Não encontramos aulas agendadas para você hoje.</p>
                    <div class="badge-folga">
                        📅 {dt_str}
                    </div>
                    <p style="margin-top: 30px; color: #7F8C8D; font-style: italic;">
                        "O descanso é o tempero que torna o trabalho mais saboroso."
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
        if not aulas_listagem:
            st.warning("Nenhuma aula encontrada para hoje.")
        else:
            aulas_ordenadas = sorted(aulas_listagem, key=lambda x: x['h'])
            sel_lbl = st.radio("Selecione a Aula:", [x["label"] for x in aulas_ordenadas], key="rd_v52")
            d_sel = next(x for x in aulas_listagem if x["label"] == sel_lbl)
            
            st.divider()
            
            # --- CHAMADA E PENDÊNCIAS ---
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
                # Busca dados salvos hoje para persistência/limpeza
                dados_hoje = {}
                if not df_hist_local.empty:
                    f_ex = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) & 
                                         (df_hist_local['Data'] == dt_str) & 
                                         (df_hist_local['Tipo'] == f"Analise_{d_sel['tipo']}")]
                    if not f_ex.empty: dados_hoje = f_ex.iloc[-1].to_dict()

                # FORMULÁRIO (Key dinâmica garante o reset total ao trocar de aula)
                with st.form(key=f"form_v52_{d_sel['id']}"):
                    st.subheader(f"📝 Registro: {d_sel['tipo']}")
                    
                    # 1. Material usado em sala
                    if d_sel["tipo"] == "Prática":
                        m_list = ["Selecione...", "Apostila", "Hino"] + (df_metodos['nome'].tolist() if not df_metodos.empty else [])
                    elif d_sel["tipo"] == "Teoria":
                        m_list = ["Selecione...", "MSA (Preto)", "Folha Extra"]
                    else:
                        m_list = ["Selecione...", "MSA (Verde)", "Folha Extra"]

                    mat_db = dados_hoje.get('Licao_Atual', "").split(":")[0] if dados_hoje else "Selecione..."
                    idx_mat = m_list.index(mat_db) if mat_db in m_list else 0
                    mat_focado = st.selectbox("Material usado hoje:", m_list, index=idx_mat)
                    
                    lic_db = dados_hoje.get('Licao_Atual', "").split(":")[-1].strip() if ":" in dados_hoje.get('Licao_Atual', "") else ""
                    lic_hoje = st.text_input("Página/Lição trabalhada:", value=lic_db)

                    # 2. Dificuldades
                    st.markdown("**Dificuldades:**")
                    lista_difs = DIF_TEORIA if d_sel["tipo"] == "Teoria" else DIF_SOLFEJO if d_sel["tipo"] == "Solfejo" else DIF_PRATICA
                    difs_db = dados_hoje.get('Dificuldades', [])
                    cols_d = st.columns(3)
                    difs_sel = [d for i, d in enumerate(lista_difs) if cols_d[i%3].checkbox(d, value=(d in difs_db), key=f"d_v52_{i}_{d_sel['id']}")]

                    st.divider()
                    st.subheader("🏠 Lição de Casa")
                    
                    def get_c_v52(m):
                        if not df_hist_local.empty:
                            c = df_hist_local[(df_hist_local['Aluna'] == als_selecionadas[0]) & 
                                              (df_hist_local['Data'] == dt_str) & 
                                              (df_hist_local['Tipo'] == f"Casa_{m}")]
                            return c.iloc[-1]['Licao_Casa'] if not c.empty else ""
                        return ""

                    tarefas_casa = {}
                    col_c1, col_c2 = st.columns(2)

                    # EXIBIÇÃO IGUAL PARA TODOS (Dois campos fixos)
                    if d_sel["tipo"] == "Prática":
                        # Na Prática, mostramos Apostila e o Método principal (ou Hino)
                        m1, m2 = "Apostila", "Método/Hino"
                        tarefas_casa["Apostila"] = col_c1.text_input(f"🏠 {m1}:", value=get_c_v52("Apostila"))
                        tarefas_casa["Metodo"] = col_c2.text_input(f"🏠 {m2}:", value=get_c_v52("Metodo"))
                    else:
                        m1, m2 = m_list[1], m_list[2] # MSA e Folha
                        tarefas_casa[m1] = col_c1.text_input(f"🏠 {m1}:", value=get_c_v52(m1))
                        tarefas_casa[m2] = col_c2.text_input(f"🏠 {m2}:", value=get_c_v52(m2))

                    # 4. Observações
                    obs_db = dados_hoje.get('Observacao', "")
                    obs_geral = st.text_area("Observações Pedagógicas:", value=obs_db)

                    if st.form_submit_button("💾 SALVAR E CONGELAR ANÁLISE", use_container_width=True):
                        if mat_focado == "Selecione...":
                            st.error("Selecione o material da aula antes de salvar.")
                        else:
                            for al_f in als_selecionadas:
                                # Salva Registro de Aula
                                db_save_historico({
                                    "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                    "Tipo": f"Analise_{d_sel['tipo']}",
                                    "Licao_Atual": f"{mat_focado}: {lic_hoje}",
                                    "Licao_Casa": "---", "Dificuldades": difs_sel,
                                    "Observacao": obs_geral, "Status": "Realizada"
                                })
                                # Salva Lições de Casa Separadamente (Pendentes)
                                for mat_nome, conteudo in tarefas_casa.items():
                                    if conteudo:
                                        db_save_historico({
                                            "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                            "Tipo": f"Casa_{mat_nome}",
                                            "Licao_Atual": "Definido", "Licao_Casa": conteudo,
                                            "Dificuldades": [], "Observacao": obs_geral, "Status": "Pendente"
                                        })
                            st.success("Registro concluído com sucesso!")
                            time.sleep(1); st.rerun()

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
