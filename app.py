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
    """Busca todo o histórico da tabela historico_geral"""
    try:
        response = supabase.table("historico_geral").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erro ao buscar histórico: {e}")
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
            
    # --- ABA 2: PLANEJAMENTO (RODÍZIO CARROSSEL) ---
    # --- ABA 2: PLANEJAMENTO (COM CORREÇÃO DE VARIAVEL) ---
    with tab_plan:
        st.markdown("### 🗓️ Gestão de Escala")
        
        # INICIALIZAÇÃO (Evita o NameError)
        folga_ativa = [] 
        
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1, key="mes_plan")
        ano = c2.selectbox("Ano:", [2026, 2027], key="ano_plan")
        
        sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano, mes) 
                   for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]
        
        if sabados:
            data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_plan")

            calendario_db = db_get_calendario()

            if data_sel_str not in calendario_db:
                with st.container(border=True):
                    st.warning("⚡ O Rodízio ainda não foi gerado.")
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
                    
                    # Define folgas aqui
                    folga_ativa = st.multiselect("Professoras de Folga:", PROFESSORAS_LISTA, key="folgas_dia")

                    if st.button("🚀 GERAR ESCALA AUTOMÁTICA", use_container_width=True, type="primary"):
                        dt_obj = datetime.strptime(data_sel_str, "%d/%m/%Y")
                        offset = dt_obj.isocalendar()[1]
                        
                        mapa = {aluna: {"Aluna": aluna, "Turma": t_nome} for t_nome, alunas in TURMAS.items() for aluna in alunas}
                        for a in mapa: mapa[a][HORARIOS[0]] = "⛪ Igreja"
                        
                        config_h = {
                            HORARIOS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "P_Teo": pt2, "P_Sol": ps2},
                            HORARIOS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "P_Teo": pt3, "P_Sol": ps3},
                            HORARIOS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "P_Teo": pt4, "P_Sol": ps4}
                        }
                        
                        for h in [HORARIOS[1], HORARIOS[2], HORARIOS[3]]:
                            conf = config_h[h]
                            # Usa a variável folga_ativa aqui dentro com segurança
                            profs_ocupadas = [conf["P_Teo"], conf["P_Sol"]] + folga_ativa
                            profs_livres = [p for p in PROFESSORAS_LISTA if p not in profs_ocupadas]
                            
                            alunas_pratica = []
                            for t_nome, alunas in TURMAS.items():
                                if conf["Teo"] == t_nome:
                                    for a in alunas: mapa[a][h] = f"📚 SALA 8 | {conf['P_Teo']}"
                                elif conf["Sol"] == t_nome:
                                    for a in alunas: mapa[a][h] = f"🔊 SALA 9 | {conf['P_Sol']}"
                                else:
                                    alunas_pratica.extend(alunas)
                            
                            num_profs = len(profs_livres)
                            if num_profs > 0:
                                for i, aluna_p in enumerate(alunas_pratica):
                                    pos = (i + offset) % num_profs
                                    prof = profs_livres[pos]
                                    sala = ((pos + offset) % 7) + 1
                                    mapa[aluna_p][h] = f"🎹 SALA {sala} | {prof}"
                            else:
                                for a in alunas_pratica: mapa[a][h] = "⚠️ S/ Prof. Disponível"

                        supabase.table("calendario").upsert({"id": data_sel_str, "escala": list(mapa.values())}).execute()
                        st.success("Rodízio Gerado!")
                        st.cache_data.clear()
                        st.rerun()
            else:
                # Exibição do Rodízio Ativo
                st.success(f"🗓️ Escala confirmada para {data_sel_str}")
                df_raw = pd.DataFrame(calendario_db[data_sel_str])
                st.dataframe(df_raw, use_container_width=True, hide_index=True)
                if st.button("🗑️ Resetar Rodízio"):
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

    # --- ABA 4: CONTROLE DE LIÇÕES (APENAS LIÇÕES PARA CASA) ---
    with tab_licao:
        st.subheader("📝 Conferência de Lições de Casa")
        
        # Cabeçalho de Seleção
        c1, c2, c3 = st.columns([2, 1, 1])
        aluna_sel = c1.selectbox("Selecione a Aluna:", ALUNAS_LISTA, key="sec_aluna_v300")
        sec_resp = c2.selectbox("Responsável:", SECRETARIAS_LISTA, key="sec_resp_v300")
        data_corr_str = c3.date_input("Data:", datetime.now(), key="sec_data_v300").strftime("%d/%m/%Y")

        st.divider()

        # --- PARTE A: LISTAGEM DE LIÇÕES (FILTRO RÍGIDO) ---
        if not df_historico.empty:
            # FILTRO: 
            # 1. Aluna correta
            # 2. O 'Tipo' deve conter 'Casa' (ignora registros de Aula Prática)
            # 3. 'Licao_Casa' não pode ser vazio ou None
            mask_casa_only = (
                (df_historico['Aluna'] == aluna_sel) & 
                (df_historico['Tipo'].str.contains('Casa', case=False, na=False)) &
                (df_historico['Licao_Casa'].notna()) & 
                (df_historico['Licao_Casa'] != "") & 
                (df_historico['Licao_Casa'] != "None")
            )
            
            df_exibir = df_historico[mask_casa_only].copy()

            if not df_exibir.empty:
                # Ordenar por data
                df_exibir['dt_temp'] = pd.to_datetime(df_exibir['Data'], format='%d/%m/%Y', errors='coerce')
                df_exibir = df_exibir.sort_values('dt_temp', ascending=False)

                for _, row in df_exibir.iterrows():
                    # Limpeza final do texto para remover prefixos repetitivos
                    texto_final = str(row['Licao_Casa']).replace("Métodos:", "").replace("||", "").strip()

                    with st.container(border=True):
                        col_info, col_visto = st.columns([3, 2])
                        
                        with col_info:
                            # Mostra qual material a aluna deve estudar em casa
                            material = str(row['Tipo']).replace("Casa_", "").replace("_", " ")
                            st.markdown(f"**📌 ESTUDAR EM CASA: {material.upper()}**")
                            st.markdown(f"## 📖 {texto_final}")
                            st.caption(f"📅 Aula de: {row['Data']} | Prof: {row.get('Instrutora', '---')}")

                        with col_visto:
                            # Opções de Correção
                            visto = st.radio("Visto:", ["Realizada", "Não Realizada", "Devolvida"], key=f"v_{row['id']}", horizontal=True)
                            obs_s = st.text_input("Nota da Secretaria:", key=f"o_{row['id']}")
                            
                            if st.button("Confirmar", key=f"b_{row['id']}", use_container_width=True):
                                supabase.table("historico_geral").update({
                                    "Status": visto,
                                    "Observacao": obs_s,
                                    "Secretaria": sec_resp
                                }).eq("id", row['id']).execute()
                                st.success("Visto registrado!"); import time; time.sleep(0.4); st.rerun()
            else:
                st.info(f"Nenhuma lição de casa específica encontrada para {aluna_sel}.")

        st.divider()

        # --- PARTE B: INCLUIR NOVA ATIVIDADE (PARA A SECRETARIA LANÇAR) ---
        st.markdown("### ✍️ Lançar Nova Meta Extra")
        with st.form("form_sec_final", clear_on_submit=True):
            f1, f2 = st.columns(2)
            met_n = f1.radio("Material:", ["MSA(verde)", "MSA(preto)", "Apostila", "Hino", "Extra"], horizontal=True)
            status_n = f2.radio("Status Inicial:", ["Pendente", "Realizada"], horizontal=True)
            
            lic_t = st.text_input("Lição / Página:")
            obs_t = st.text_area("Instruções Adicionais:")
            
            if st.form_submit_button("💾 SALVAR META"):
                if lic_t:
                    try:
                        nova_meta = {
                            "Aluna": aluna_sel,
                            "Data": data_corr_str,
                            "Tipo": f"Casa_{met_n}",
                            "Licao_Atual": "Lançado Secretaria",
                            "Licao_Casa": lic_t,
                            "Status": status_n,
                            "Secretaria": sec_resp,
                            "Observacao": obs_t
                        }
                        supabase.table("historico_geral").insert(nova_meta).execute()
                        st.success("Meta salva!"); import time; time.sleep(0.5); st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.error("Preencha o campo da lição.")
                    
    # --- ABA 5: AJUSTES ---
    with tab_ajustes:
        st.subheader("🛠️ Ajustar Registros")
        al_aj = st.selectbox("Aluna:", ALUNAS_LISTA, key="aj_al_vfinal")
        if not df_historico.empty:
            df_f = df_historico[df_historico['Aluna'] == al_aj].sort_values('dt_obj', ascending=False)
            if not df_f.empty:
                st.dataframe(df_f[['Data', 'Tipo', 'Licao_Atual']], use_container_width=True)
                idx = st.selectbox("Escolha para apagar:", range(len(df_f)), format_func=lambda x: f"{df_f.iloc[x]['Data']} - {df_f.iloc[x]['Tipo']}")
                if st.button("❌ APAGAR"):
                    supabase.table("historico_geral").delete().eq("id", df_f.iloc[idx]['id']).execute()
                    st.rerun()
                    
# ============================================================
# MÓDULO PROFESSORA - V42 (ANÁLISE POR MÉTODO + SALVAMENTO INDIVIDUAL)
# ============================================================
elif menu == "👩‍🏫 Minhas Aulas":
    st.header(f"👩‍🏫 Painel da Professora: {st.session_state.nome_logado}")
    
    tab_aula, tab_config = st.tabs(["📝 Registro de Aula", "⚙️ Configurar Métodos"])

    # --- ABA 1: CONFIGURAÇÃO DE MÉTODOS ---
    with tab_config:
        st.subheader("📚 Gerenciar Métodos de Prática")
        try:
            res = supabase.table("config_metodos").select("*").execute()
            df_metodos = pd.DataFrame(res.data)
        except: df_metodos = pd.DataFrame()

        if not df_metodos.empty:
            st.dataframe(df_metodos[['nome']], use_container_width=True, hide_index=True)
            met_del = st.selectbox("Remover método:", ["Selecione..."] + df_metodos['nome'].tolist())
            if st.button("🗑️ Remover"):
                if met_del != "Selecione...":
                    supabase.table("config_metodos").delete().eq("nome", met_del).execute()
                    st.success("Removido!"); st.rerun()
        
        st.divider()
        n_met = st.text_input("Novo Método:")
        if st.button("➕ Cadastrar"):
            if n_met:
                supabase.table("config_metodos").insert({"nome": n_met, "categoria": "Prática"}).execute()
                st.success("Cadastrado!"); st.rerun()

    # --- ABA 2: REGISTRO DE AULA ---
    with tab_aula:
        instr_sel = st.session_state.get('nome_logado', 'Selecione...')
        hoje = datetime.now()
        sab_p = hoje if hoje.weekday() == 5 else hoje + timedelta(days=(5 - hoje.weekday()) % 7)
        data_prof = st.date_input("Data da Aula:", sab_p)
        dt_str = data_prof.strftime("%d/%m/%Y")

        if instr_sel != "Selecione...":
            cal_db = db_get_calendario()
            n_bus = limpar_texto(instr_sel).lower().strip()
            aulas_agrupadas = []
            vistos = set()

            if dt_str in cal_db:
                for reg in cal_db[dt_str]:
                    for h in HORARIOS:
                        cont = str(reg.get(h, ""))
                        if cont and n_bus in limpar_texto(cont).lower():
                            tipo = "Teoria" if "SALA 8" in cont.upper() else "Solfejo" if "SALA 9" in cont.upper() else "Prática"
                            id_aula = f"{h}_{tipo}_{reg.get('Turma', 'Indiv')}"
                            if id_aula not in vistos:
                                label_aula = f"{'📚' if tipo != 'Prática' else '🎹'} {h} | {tipo} - {reg.get('Turma') if tipo != 'Prática' else reg.get('Aluna')}"
                                aulas_agrupadas.append({"label": label_aula, "h": h, "tipo": tipo, "al": reg.get("Aluna"), "tr": reg.get("Turma"), "loc": cont.split('|')[0]})
                                vistos.add(id_aula)

            if not aulas_agrupadas:
                st.warning(f"Nenhuma aula para {dt_str}.")
            else:
                sel_lbl = st.radio("Selecione a Aula/Turma:", [x["label"] for x in sorted(aulas_agrupadas, key=lambda x: x['h'])])
                d_sel = next(x for x in aulas_agrupadas if x["label"] == sel_lbl)
                
                # --- CHAMADA ---
                st.divider()
                st.markdown(f"### 👥 Chamada: {d_sel['loc']}")
                als_ref = TURMAS.get(d_sel["tr"], [d_sel["al"]]) if d_sel["tipo"] != "Prática" else [d_sel["al"]]
                als_selecionadas = []
                c_ch = st.columns(4)
                for i, al in enumerate(als_ref):
                    if c_ch[i%4].checkbox(al, value=True, key=f"ch_{al}_{sel_lbl}"):
                        als_selecionadas.append(al)

                if als_selecionadas:
                    with st.form(key=f"form_v42_{sel_lbl}"):
                        
                        # --- SEÇÃO 1: ANÁLISE (HOJE) ---
                        st.subheader("🔍 1. Lição em Análise (Hoje)")
                        
                        # Seletor de Método também na Análise
                        m_opts = ["Selecione...", "MSA(verde)", "MSA(preto)", "Apostila", "Extra"] + (df_metodos['nome'].tolist() if not df_metodos.empty else [])
                        metodo_analisado = st.selectbox("Selecione o Material analisado agora:", m_opts, key="met_analise")
                        detalhe_analise = st.text_input("Página/Lição que ela tocou:", placeholder="Ex: Pág 20, Lição 5")
                        
                        st.markdown("**Dificuldades encontradas nesta lição:**")
                        lista_difs = DIF_TEORIA if d_sel["tipo"] == "Teoria" else DIF_SOLFEJO if d_sel["tipo"] == "Solfejo" else DIF_PRATICA
                        cols_d = st.columns(3)
                        difs_selecionadas = [d for idx, d in enumerate(lista_difs) if cols_d[idx%3].checkbox(d, key=f"dif_v42_{idx}")]
                        
                        st.divider()

                        # --- SEÇÃO 2: LIÇÕES PARA CASA ---
                        st.subheader("🏠 2. Lições para Casa")
                        tarefas_casa = {}
                        
                        if d_sel["tipo"] == "Teoria":
                            c1, c2 = st.columns(2)
                            tarefas_casa["MSA(verde)"] = c1.text_input("📚 MSA (Verde):")
                            tarefas_casa["MSA(preto)"] = c2.text_input("📖 MSA (Preto):")
                            tarefas_casa["Extra"] = st.text_input("📑 Extra (Teoria):")
                        
                        elif d_sel["tipo"] == "Solfejo":
                            c1, c2 = st.columns(2)
                            tarefas_casa["MSA(verde)"] = c1.text_input("🎵 MSA (Verde):")
                            tarefas_casa["Extra"] = c2.text_input("📑 Extra (Solfejo):")
                        
                        else: # Prática
                            met_casa = st.selectbox("Selecione o Método para lição de casa:", m_opts, key="met_casa")
                            c1, c2 = st.columns(2)
                            li_m = c1.text_input("🎹 Lição do Método:")
                            tarefas_casa["Apostila"] = c2.text_input("📒 Apostila:")
                            if met_casa != "Selecione..." and li_m:
                                tarefas_casa[met_casa] = li_m

                        obs_v = st.text_area("✍️ Observações Gerais:")

                        if st.form_submit_button("💾 CONGELAR E ENVIAR"):
                            for al_f in als_selecionadas:
                                # 1. SALVAR ANÁLISE ATUAL (Se preenchida)
                                if metodo_analisado != "Selecione...":
                                    db_save_historico({
                                        "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                        "Tipo": f"Analise_{metodo_analisado}".replace(" ", "_"),
                                        "Licao_Atual": f"{metodo_analisado}: {detalhe_analise}",
                                        "Licao_Casa": "N/A (Ver bloco abaixo)",
                                        "Dificuldades": difs_selecionadas,
                                        "Observacao": obs_v, "Status": "Pendente"
                                    })

                                # 2. SALVAR CADA LIÇÃO DE CASA SEPARADAMENTE
                                for material, conteudo in tarefas_casa.items():
                                    if conteudo:
                                        db_save_historico({
                                            "Aluna": al_f, "Data": dt_str, "Instrutora": instr_sel,
                                            "Tipo": f"Casa_{material}".replace(" ", "_"),
                                            "Licao_Atual": "Definido para estudo",
                                            "Licao_Casa": f"{material}: {conteudo}",
                                            "Dificuldades": [], # Lição de casa ainda não tem dificuldade
                                            "Observacao": obs_v, "Status": "Pendente"
                                        })
                            
                            st.success("✅ Tudo salvo individualmente por material!"); time.sleep(1); st.rerun()
                            
# ==========================================
# MÓDULO ANÁLISE DE IA - V42 (FOCO NO PRONTUÁRIO)
# ==========================================
elif menu == "📊 Analítico IA":
    st.markdown(f"<h1 style='text-align: center; color: #2E4053;'>📊 Prontuário Pedagógico</h1>", unsafe_allow_html=True)
    
    historico_raw = db_get_historico()
    df = pd.DataFrame(historico_raw)

    if df.empty:
        st.info("ℹ️ O banco de dados está vazio.")
    else:
        # Tratamento de datas
        df['dt_obj'] = pd.to_datetime(df['Data'], format="%d/%m/%Y", errors='coerce')
        df = df.dropna(subset=['dt_obj']).sort_values('dt_obj', ascending=False)

        aluna_sel = st.selectbox("👤 Selecione a Aluna:", ALUNAS_LISTA, key="analise_v42")
        df_aluna = df[df['Aluna'] == aluna_sel]

        if not df_aluna.empty:
            # --- CABEÇALHO ---
            st.markdown(f"""
                <div style="background-color: #FDFEFE; padding: 15px; border-radius: 10px; border: 1px solid #EAEDED; border-top: 5px solid #2E4053; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #2E4053;">{aluna_sel.upper()}</h2>
                    <p style="margin: 0; color: #7F8C8D;">Ficha de Acompanhamento Técnico</p>
                </div>
            """, unsafe_allow_html=True)

            data_sel = st.selectbox("📅 Selecione a Data da Aula:", df_aluna['Data'].unique())
            # Filtra registros da data, ignorando chamadas
            dados_dia = df_aluna[(df_aluna['Data'] == data_sel) & (~df_aluna['Tipo'].isin(['Chamada', 'Presença', 'Falta']))]

            # --- SEÇÃO 1: PRÁTICA ---
            st.markdown("### 🎹 Prática")
            p_data = dados_dia[dados_dia['Tipo'].str.contains('Prática|Pratica', case=False, na=False)]
            
            if not p_data.empty:
                for _, p in p_data.iterrows():
                    metodo = p['Tipo'].split('_')[-1].replace("_", " ") if "Aula_" in p['Tipo'] else "Prática"
                    difs_p = p.get('Dificuldades', [])
                    difs_txt = ", ".join(difs_p) if isinstance(difs_p, list) else str(difs_p)
                    
                    with st.container(border=True):
                        st.markdown(f"#### 📖 Método: {metodo}")
                        c1, c2 = st.columns(2)
                        c1.markdown(f"**👩‍🏫 Instrutora:** {p.get('Instrutora') or '---'}")
                        c2.markdown(f"**📍 Lição:** {p.get('Licao_Atual', '---')}")
                        
                        if difs_txt and difs_txt not in ['[]', 'None', '', 'nan', '[]']:
                            st.markdown(f"⚠️ **Dificuldades Detectadas:** <span style='color: #C0392B; font-weight: bold;'>{difs_txt}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("✅ **Dificuldades:** Nenhuma apresentada")
                        
                        st.markdown(f"📝 **Observações:** {p.get('Observacao', '---')}")
                        st.markdown(f"""<div style="background-color: #F4F6F7; padding: 8px; border-radius: 5px; border-left: 3px solid #2980B9;">
                            <b>🏠 Lição de casa:</b> {p.get('Licao_Casa', '---')}</div>""", unsafe_allow_html=True)
            else:
                st.caption("Nenhum registro de Prática para este dia.")

            # --- SEÇÃO 2: TEORIA E SOLFEJO ---
            c_teoria, c_solfejo = st.columns(2)
            
            with c_teoria:
                st.markdown("### 📝 Teoria")
                t_data = dados_dia[dados_dia['Tipo'].str.contains('Teoria', case=False, na=False)]
                if not t_data.empty:
                    for _, t in t_data.iterrows():
                        difs_t = t.get('Dificuldades', [])
                        difs_t_txt = ", ".join(difs_t) if isinstance(difs_t, list) else str(difs_t)
                        with st.container(border=True):
                            st.markdown(f"**📖 Conteúdo:** {t.get('Licao_Atual', '---')}")
                            if difs_t_txt and difs_t_txt not in ['[]', 'None', '', 'nan']:
                                st.markdown(f"⚠️ <span style='color: #C0392B;'>{difs_t_txt}</span>", unsafe_allow_html=True)
                            st.markdown(f"**Obs:** {t.get('Observacao', '---')}")
                            st.markdown(f"🏠 **Casa:** {t.get('Licao_Casa', '---')}")

            with c_solfejo:
                st.markdown("### 🗣️ Solfejo")
                s_data = dados_dia[dados_dia['Tipo'].str.contains('Solfejo', case=False, na=False)]
                if not s_data.empty:
                    for _, s in s_data.iterrows():
                        difs_s = s.get('Dificuldades', [])
                        difs_s_txt = ", ".join(difs_s) if isinstance(difs_s, list) else str(difs_s)
                        with st.container(border=True):
                            st.markdown(f"**📖 Conteúdo:** {s.get('Licao_Atual', '---')}")
                            if difs_s_txt and difs_s_txt not in ['[]', 'None', '', 'nan']:
                                st.markdown(f"⚠️ <span style='color: #C0392B;'>{difs_s_txt}</span>", unsafe_allow_html=True)
                            st.markdown(f"**Obs:** {s.get('Observacao', '---')}")
                            st.markdown(f"🏠 **Casa:** {s.get('Licao_Casa', '---')}")

            # --- SEÇÃO 4: LIÇÕES DE CASA (SECRETARIA) ---
            st.markdown("### 📚 Status de Lições (Secretaria)")
            sec_data = dados_dia[dados_dia['Tipo'].str.contains('Controle_Licao', case=False, na=False)]
            if not sec_data.empty:
                for _, row in sec_data.iterrows():
                    status_cor = "#27AE60" if "Realizou" in row.get('Status', '') else "#F39C12"
                    st.markdown(f"""
                        <div style="padding: 10px; border: 1px solid #D5DBDB; border-radius: 5px; border-left: 10px solid {status_cor}; margin-bottom: 5px;">
                            <b>Categoria:</b> {row.get('Categoria', 'Geral')} | 
                            <b>Status:</b> {row.get('Status', '---')} <br>
                            <b>Nota:</b> {row.get('Observacao', '---')}
                        </div>
                    """, unsafe_allow_html=True)

            # --- SEÇÃO 5: METAS ---
            st.divider()
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.info("🎯 **Metas Próxima Aula**\n\n- Evoluir lição atual\n- Ajustar postura")
            with m_col2:
                st.warning("🏆 **Dicas para a Banca**\n\n- Foco na expressividade\n- Pedal de expressão")

        st.divider()

















































































