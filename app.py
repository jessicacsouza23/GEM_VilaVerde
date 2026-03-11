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
SECRETARIAS_LISTA = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"]
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
                "Mariana - Vila Araguaia", "Mellina S. - Jardim Lígia", "Rebecca A. - Vila Verde", 
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
# MÓDULO SECRETARIA
# ==========================================
if menu == "🏠 Secretaria":
    # CORREÇÃO: Agora as 4 variáveis correspondem aos 4 itens da lista
    if menu == "🏠 Secretaria":
        tab_plan, tab_cham, tab_licao = st.tabs([
            "🗓️ Planejamento", 
            "📍 Chamada", 
            "📝 Controle de Lições"
        ])

            # Criamos uma expansão para não ocupar espaço visual nobre
        with st.expander("🚨 ÁREA DE PERIGO - Limpeza do Sistema"):
            st.warning("Atenção: Esta ação apagará TODOS os registros de aulas e escalas do sistema.")
            
            # Trava de segurança
            confirma_limpeza = st.checkbox("Estou ciente que esta ação não pode ser desfeita.")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🗑️ LIMPAR HISTÓRICO DE AULAS"):
                    if confirma_limpeza:
                        try:
                            # Apaga todos os registros da tabela de histórico
                            # No Supabase, um delete sem .eq() pode ser bloqueado por segurança, 
                            # então usamos um filtro que sempre seja verdadeiro (ex: Data != '')
                            supabase.table("historico_geral").delete().neq("Data", "").execute()
                            st.success("✅ Histórico de aulas limpo com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao limpar: {e}")
                    else:
                        st.error("Marque a confirmação de segurança primeiro.")
    
            with col_btn2:
                if st.button("📅 LIMPAR ESCALAS / RODÍZIO"):
                    if confirma_limpeza:
                        try:
                            # Apaga o rodízio gerado
                            supabase.table("config_calendario").delete().neq("id", -1).execute()
                            st.success("✅ Escalas e Rodízios removidos!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao limpar: {e}")
                    else:
                        st.error("Marque a confirmação de segurança primeiro.")
    
        st.divider()
        
        with tab_plan:
            c1, c2 = st.columns(2)
            mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
            ano = c2.selectbox("Ano:", [2026, 2027])
            sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano, mes) 
                       for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]
            
            if not sabados:
                st.error("Nenhum sábado encontrado.")
            else:
                data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados])
    
                # --- LÓGICA DE GERAÇÃO E EXIBIÇÃO DENTRO DO TAB ---
                if data_sel_str not in calendario_db:
                    st.warning("⚠️ Rodízio não gerado para esta data.")
                    
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
                    
                    folgas = st.multiselect("Folgas (Professoras ausentes):", PROFESSORAS_LISTA)
    
                    if st.button("🚀 GERAR RODÍZIO CARROSSEL TOTAL"):
                        dt_obj = datetime.strptime(data_sel_str, "%d/%m/%Y")
                        offset = dt_obj.isocalendar()[1] 
                        
                        mapa = {}
                        for t_nome, alunas in TURMAS.items():
                            for aluna in alunas:
                                linha = {"Aluna": aluna, "Turma": t_nome}
                                for h in HORARIOS: linha[h] = "---"
                                mapa[aluna] = linha
    
                        config_h = {
                            HORARIOS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "P_Teo": pt2, "P_Sol": ps2},
                            HORARIOS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "P_Teo": pt3, "P_Sol": ps3},
                            HORARIOS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "P_Teo": pt4, "P_Sol": ps4}
                        }
    
                        for h_idx, h_nome in enumerate(HORARIOS):
                            if h_idx == 0:
                                for a in mapa: mapa[a][h_nome] = "⛪ Igreja"
                                continue
                            
                            if h_nome in config_h:
                                conf = config_h[h_nome]
                                ocupadas = [conf["P_Teo"], conf["P_Sol"]] + folgas
                                profs_livres = [p for p in PROFESSORAS_LISTA if p not in ocupadas]
                                
                                alunas_pratica = []
                                for aluna in mapa:
                                    if mapa[aluna]["Turma"] == conf["Teo"]:
                                        mapa[aluna][h_nome] = f"📚 SALA 8 | {conf['P_Teo']}"
                                    elif mapa[aluna]["Turma"] == conf["Sol"]:
                                        mapa[aluna][h_nome] = f"🔊 SALA 9 | {conf['P_Sol']}"
                                    else:
                                        alunas_pratica.append(aluna)
                                
                                num_p = len(profs_livres)
                                if num_p > 0:
                                    for i, aluna_p in enumerate(alunas_pratica):
                                        pos = (i + offset) % num_p
                                        sala_n = ((pos + offset) % 7) + 1
                                        mapa[aluna_p][h_nome] = f"🎹 SALA {sala_n} | {profs_livres[pos]}"
    
                        supabase.table("calendario").upsert({"id": data_sel_str, "escala": list(mapa.values())}).execute()
                        st.success("✅ Rodízio completo gerado!")
                        st.cache_data.clear()
                        st.rerun()

                else:
                    st.success(f"🗓️ Rodízio Ativo: {data_sel_str}")
                    
                    # 1. Carrega os dados atuais
                    df_atual = pd.DataFrame(calendario_db[data_sel_str])
                    
                    # Ordena as colunas para garantir a visualização correta
                    colunas_finais = ["Aluna", "Turma"] + [h for h in HORARIOS if h in df_atual.columns]
                    df_atual = df_atual[colunas_finais]

                    st.markdown("💡 **Dica:** Clique duas vezes em qualquer célula para trocar a Professora ou Sala.")
                    
                    # 2. Abre o Editor de Dados (planilha interativa)
                    # O 'key' ajuda o Streamlit a manter o estado da edição
                    df_editado = st.data_editor(
                        df_atual, 
                        use_container_width=True, 
                        hide_index=True,
                        key=f"editor_{data_sel_str}" 
                    )

                    col_edit1, col_edit2 = st.columns(2)
                    
                    # 3. Botão para Salvar o que foi editado
                    with col_edit1:
                        if st.button("💾 SALVAR ALTERAÇÕES"):
                            # Transformamos o dataframe editado de volta em lista de dicionários
                            lista_editada = df_editado.to_dict(orient="records")
                            
                            # Faz o Upsert no Supabase
                            supabase.table("calendario").upsert({
                                "id": data_sel_str, 
                                "escala": lista_editada
                            }).execute()
                            
                            st.toast("Alterações salvas com sucesso!", icon="✅")
                            st.cache_data.clear()
                            st.rerun()

                    # 4. Botão para deletar
                    with col_edit2:
                        if st.button("🗑️ DELETAR RODÍZIO", use_container_width=True):
                            supabase.table("calendario").delete().eq("id", data_sel_str).execute()
                            st.cache_data.clear()
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
        
        # --- 1. INICIALIZAÇÃO DE SEGURANÇA (Evita NameError) ---
        pendencias = pd.DataFrame() 
        historico_raw = db_get_historico()
        df_historico = pd.DataFrame(historico_raw)
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            aluna_sel = st.selectbox("Selecione a Aluna:", ALUNAS_LISTA, key="sec_aluna_sel")
        with c2:
            sec_resp = st.selectbox("Responsável Secretaria:", SECRETARIAS_LISTA, key="sec_resp_sel")
        with c3:
            data_corr = st.date_input("Data da Correção:", datetime.now(), key="sec_data_sel")
            data_corr_str = data_corr.strftime("%d/%m/%Y")

        # --- 2. FILTRAGEM DE PENDÊNCIAS ---
        if not df_historico.empty:
            # Filtramos lições da aluna selecionada que não foram finalizadas pela secretaria
            pendencias = df_historico[
                (df_historico['Aluna'] == aluna_sel) & 
                (df_historico['Tipo'] == 'Controle_Licao') & 
                (df_historico['Status'] != "Realizado")
            ].copy()

        # --- 3. EXIBIÇÃO E VALIDAÇÃO ---
        if not pendencias.empty:
            st.error(f"🚨 {len(pendencias)} Lições Pendentes para {aluna_sel}")
            
            for i, (row_idx, p) in enumerate(pendencias.iterrows()):
                # Chave única para evitar conflitos de widgets
                safe_key = f"{p['Data']}_{i}".replace("/", "")
                
                with st.container(border=True):
                    col_info, col_acao = st.columns([3, 2])
                    
                    with col_info:
                        st.markdown(f"**📅 {p['Data']}** — {p['Categoria']}")
                        st.markdown(f"📖 {p['Licao_Detalhe']}")
                        if p.get('Observacao'):
                            # Se a observação for um JSON (da professora), tentamos limpar para exibir
                            try:
                                obs_json = json.loads(p['Observacao'])
                                texto_obs = f"Postura: {obs_json.get('Postura', '')} | Técnica: {obs_json.get('Técnica', '')}"
                                st.caption(f"💬 Análise Técnica: {texto_obs}")
                            except:
                                st.caption(f"💬 Nota: {p['Observacao']}")
                    
                    with col_acao:
                        novo_status = st.radio(
                            "Resultado:", 
                            ["Realizado", "Não realizado", "Devolvido para correção"],
                            key=f"status_{safe_key}", 
                            horizontal=True
                        )
                        nova_obs = st.text_input("Obs da Secretaria:", key=f"obs_sec_{safe_key}")
                        
                        if st.button("Confirmar Correção", key=f"btn_corr_{safe_key}"):
                            try:
                                # O 'id' deve ser a coluna primária da sua tabela no Supabase
                                supabase.table("historico_geral").update({
                                    "Status": novo_status,
                                    "Observacao_Sec": nova_obs, # Usando coluna diferente para não apagar a da prof
                                    "Secretaria": sec_resp
                                }).eq("id", p['id']).execute()
                                
                                st.success("✅ Atualizado!")
                                st.cache_data.clear() # Limpa o cache para recarregar a lista sem essa pendência
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar: {e}")
        else:
            st.success(f"✅ Nenhuma lição pendente para {aluna_sel}.")
        
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
# INICIALIZAÇÃO GLOBAL DE SEGURANÇA
# ==========================================
folga_ativa = False  # Garante que a variável sempre exista
nome_logado = st.session_state.get("nome_logado", "")
perfil_usuario = st.session_state.get("perfil", "")
data_hj_str = datetime.now().strftime("%d/%m/%Y")

# --- LÓGICA DE VERIFICAÇÃO DE FOLGA ---
# Só verificamos folga se o usuário logado for uma Professora
if perfil_usuario == "Professora":
    try:
        # Puxamos o calendário do dia
        calendario_raw = db_get_calendario() 
        
        if data_hj_str in calendario_raw:
            escala_hoje = calendario_raw[data_hj_str]
            # Extraímos os nomes das professoras que estão escaladas em alguma célula do rodízio
            # Convertemos para string e limpamos espaços para evitar erros de digitação
            profs_escaladas = []
            for linha in escala_hoje:
                for celula in linha.values():
                    # Verifica se o nome da professora logada aparece em algum lugar da escala
                    if nome_logado in str(celula):
                        profs_escaladas.append(nome_logado)
            
            # Se a prof não foi encontrada na escala de hoje, ela está de folga
            if nome_logado not in profs_escaladas:
                folga_ativa = True
        else:
            # Se não houver rodízio gerado para hoje, tratamos como folga ou aviso
            folga_ativa = False 
    except Exception as e:
        st.error(f"Erro ao verificar escala: {e}")
        folga_ativa = False
        

# ============================================================
# MÓDULO PROFESSORA - V34 (CÓDIGO COMPLETO & ESTÁVEL)
# ============================================================
elif menu == "👩‍🏫 Minhas Aulas":
    st.header(f"👩‍🏫 Painel da Professora: {st.session_state.nome_logado}")
    tab_aula, tab_config = st.tabs(["📝 Registro de Aula", "⚙️ Configurar Métodos"])

    if folga_ativa:
        st.warning("📴 Sistema em modo leitura devido à sua folga.")
    
    # --- FUNÇÃO INTERNA PARA BUSCAR MÉTODOS ---
    def db_get_metodos():
        try:
            res = supabase.table("config_metodos").select("*").execute()
            return pd.DataFrame(res.data)
        except: 
            return pd.DataFrame()

    # --- ABA 1: CONFIGURAÇÃO DE MÉTODOS ---
    with tab_config:
        st.subheader("📚 Gerenciar Métodos de Prática")
        df_metodos = db_get_metodos()
        
        if not df_metodos.empty:
            st.dataframe(df_metodos[['nome']], use_container_width=True, hide_index=True)
            met_del = st.selectbox("Selecione um método para remover:", ["Selecione..."] + df_metodos['nome'].tolist(), key="del_met_v34")
            if st.button("🗑️ Remover Método", key="btn_del_v34"):
                if met_del != "Selecione...":
                    supabase.table("config_metodos").delete().eq("nome", met_del).execute()
                    st.success(f"Método {met_del} removido!")
                    st.rerun()
        
        st.divider()
        st.write("✨ **Cadastrar Novo Método**")
        n_met = st.text_input("Nome do Método (ex: Bona, Czerny, Hanon):", key="new_met_v34")
        if st.button("➕ Cadastrar", key="btn_add_v34"):
            if n_met:
                supabase.table("config_metodos").insert({"nome": n_met, "categoria": "Prática"}).execute()
                st.success("Método cadastrado!")
                st.rerun()

    # --- ABA 2: REGISTRO DE AULA ---
    with tab_aula:
        instr_sel = st.session_state.get('nome_logado', 'Selecione...')
        
        # Cabeçalho de Seleção de Data
        c1, c2 = st.columns(2)
        with c1: st.info(f"Instrutora: **{instr_sel}**")
        with c2:
            hoje = datetime.now()
            # Sugere sempre o próximo sábado ou o dia atual se for sábado
            sab_p = hoje if hoje.weekday() == 5 else hoje + timedelta(days=(5 - hoje.weekday()) % 7)
            data_prof = st.date_input("Data da Aula:", sab_p, key="data_aula_v34")
            dt_str = data_prof.strftime("%d/%m/%Y")

        if instr_sel != "Selecione...":
            cal_db = db_get_calendario()
            n_bus = limpar_texto(instr_sel).lower().strip()
            aulas = []

            # Filtragem de aulas no calendário
            if dt_str in cal_db:
                for reg in cal_db[dt_str]:
                    for h in HORARIOS:
                        cont = str(reg.get(h, ""))
                        if cont and n_bus in limpar_texto(cont).lower():
                            tipo = "Teoria" if "SALA 8" in cont.upper() else "Solfejo" if "SALA 9" in cont.upper() else "Prática"
                            lbl = f"🎹 {h} | {reg.get('Aluna')} ({cont.split('|')[0]})" if tipo=="Prática" else f"📚 {h} | {tipo} - {reg.get('Turma')}"
                            if lbl not in [x["label"] for x in aulas]:
                                aulas.append({"label": lbl, "h": h, "tipo": tipo, "al": reg.get("Aluna"), "tr": reg.get("Turma"), "loc": cont.split('|')[0]})

            if not aulas:
                st.warning("⚠️ Nenhuma aula encontrada para você nesta data.")
            else:
                # Seleção da Aula/Horário
                sel_lbl = st.radio("Selecione o Horário/Turma:", [x["label"] for x in sorted(aulas, key=lambda x: x['h'])], key="radio_aulas_v34")
                d_sel = next(x for x in aulas if x["label"] == sel_lbl)
                
                st.divider()
                st.markdown(f"### 👥 Chamada: {d_sel['loc']}")
                
                # Lista de Alunas (Checkbox de presença)
                als_ref = TURMAS.get(d_sel["tr"], [d_sel["al"]]) if d_sel["tipo"] != "Prática" else [d_sel["al"]]
                als_conf = []
                cols_ch = st.columns(4)
                for i, al in enumerate(als_ref):
                    if cols_ch[i%4].checkbox(al, value=True, key=f"ch_v34_{al}_{sel_lbl}"):
                        als_conf.append(al)

                # --- INÍCIO DA ANÁLISE PEDAGÓGICA ---
                if als_conf:
                    st.write("---")
                    st.subheader("📘 Passo 1: Escolha o Método")
                    
                    # Definição do Método (Importante para carregar os dados certos)
                    if d_sel["tipo"] == "Prática":
                        df_m = db_get_metodos()
                        m_opts = ["Selecione..."] + (df_m['nome'].tolist() if not df_m.empty else [])
                        met_v = st.selectbox("Qual livro/método você vai avaliar agora?", m_opts, key=f"sel_met_v34_{sel_lbl}")
                    else:
                        met_v = d_sel["tipo"]
                        st.info(f"Tipo de Aula: {met_v}")

                    # --- BUSCA DINÂMICA NO BANCO ---
                    pre_lic, pre_obs, pre_difs = "", "", []
                    if met_v != "Selecione...":
                        tipo_busca = f"Aula_{d_sel['tipo']}_{met_v}".replace(" ", "_")
                        # Busca apenas o histórico desse método específico
                        res_h = supabase.table("historico_geral").select("*").eq("Data", dt_str).eq("Aluna", als_conf[0]).eq("Tipo", tipo_busca).execute()
                        
                        if res_h.data:
                            dados = res_h.data[0]
                            pre_lic = dados.get("Licao_Atual", "").replace(met_v, "").strip()
                            pre_obs = dados.get("Observacao", "")
                            pre_difs = dados.get("Dificuldades", [])
                            st.success(f"✅ Histórico de {met_v} carregado para edição.")

                    # --- FORMULÁRIO DE REGISTRO ---
                    # A form_key agora muda conforme o método, permitindo resetar o form
                    form_key = f"form_v34_{als_conf[0]}_{sel_lbl}_{met_v}".replace(" ", "_")
                    with st.form(key=form_key):
                        st.subheader(f"📝 Passo 2: Analisar {met_v}")
                        
                        lic_v = st.text_input("Lição / Página Atual:", value=pre_lic, help="Digite apenas o número ou página.")
                        
                        st.markdown("**Dificuldades Detectadas nesta lição:**")
                        d_lista = DIF_TEORIA if d_sel["tipo"] == "Teoria" else DIF_SOLFEJO if d_sel["tipo"] == "Solfejo" else DIF_PRATICA
                        c_dif = st.columns(2)
                        difs_finais = []
                        for idx, dfc in enumerate(d_lista):
                            if c_dif[idx%2].checkbox(dfc, value=(dfc in pre_difs), key=f"chk_v34_{dfc}_{form_key}"):
                                difs_finais.append(dfc)

                        obs_v = st.text_area("Dicas Pedagógicas / O que melhorar:", value=pre_obs, placeholder="Dica para a próxima aula...")

                        st.divider()
                        st.subheader("🏠 Próxima Aula (Lição de Casa)")
                        cp1, cp2 = st.columns(2)
                        l_casa_1 = cp1.text_input("Tarefa principal:", key=f"l1_{form_key}")
                        l_casa_2 = cp2.text_input("Tarefa extra:", key=f"l2_{form_key}")
                        
                        btn_salvar = st.form_submit_button("💾 CONGELAR ANÁLISE DESTE MÉTODO")

                    # --- LÓGICA DE SALVAMENTO ---
                    if btn_salvar:
                        if met_v == "Selecione...":
                            st.error("⚠️ Você precisa selecionar um método antes de salvar.")
                        else:
                            with st.spinner(f"Salvando registros de {met_v}..."):
                                t_casa_final = f"{l_casa_1} | {l_casa_2}" if (l_casa_1 or l_casa_2) else "Não informada"
                                tipo_final = f"Aula_{d_sel['tipo']}_{met_v}".replace(" ", "_")
                                
                                for al_f in als_conf:
                                    # Lógica de união: Individual + Turma (Observações)
                                    res_atual = supabase.table("historico_geral").select("Observacao").eq("Data", dt_str).eq("Aluna", al_f).eq("Tipo", tipo_final).execute()
                                    
                                    obs_final = obs_v
                                    if res_atual.data:
                                        obs_ant = res_atual.data[0].get("Observacao", "")
                                        if obs_ant and obs_ant != obs_v:
                                            obs_final = f"📝 INDIVIDUAL: {obs_ant} | 👥 TURMA: {obs_v}"
                                    
                                    # Limpa o registro anterior para evitar duplicidade
                                    supabase.table("historico_geral").delete().eq("Data", dt_str).eq("Tipo", tipo_final).eq("Aluna", al_f).execute()
                                    
                                    # Grava o novo registro com o método na coluna 'Tipo'
                                    db_save_historico({
                                        "Aluna": al_f, 
                                        "Tipo": tipo_final, 
                                        "Data": dt_str,
                                        "Instrutora": instr_sel, 
                                        "Licao_Atual": f"{met_v} {lic_v}".strip(),
                                        "Dificuldades": difs_finais, 
                                        "Observacao": obs_final, 
                                        "Licao_Casa": t_casa_final
                                    })
                            
                            st.balloons()
                            st.success(f"✅ DADOS SALVOS! O método {met_v} foi congelado no prontuário.")
                            import time
                            time.sleep(2)
                            st.rerun()
                            
# ==========================================
# MÓDULO ANÁLISE DE IA - V39 (CORREÇÕES E AJUSTES)
# ==========================================
elif menu == "📊 Analítico IA":
    st.markdown(f"<h1 style='text-align: center; color: #2E4053;'>📊 Prontuário Pedagógico</h1>", unsafe_allow_html=True)
    
    historico_raw = db_get_historico()
    df = pd.DataFrame(historico_raw)

    if df.empty:
        st.info("ℹ️ O banco de dados está vazio.")
    else:
        # 1. Tratamento rigoroso de datas e tipos
        df['dt_obj'] = pd.to_datetime(df['Data'], format="%d/%m/%Y", errors='coerce')
        df = df.dropna(subset=['dt_obj']).sort_values('dt_obj', ascending=False)

        aluna_sel = st.selectbox("👤 Selecione a Aluna:", ALUNAS_LISTA, key="analise_v39")
        df_aluna = df[df['Aluna'] == aluna_sel]

        if not df_aluna.empty:
            # --- NOVO CABEÇALHO LIMPO ---
            st.markdown(f"""
                <div style="background-color: #FDFEFE; padding: 15px; border-radius: 10px; border: 1px solid #EAEDED; border-top: 5px solid #2E4053; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #2E4053;">{aluna_sel.upper()}</h2>
                    <p style="margin: 0; color: #7F8C8D;">Relatório Pedagógico Detalhado</p>
                </div>
            """, unsafe_allow_html=True)

            # Seleção de Data
            data_sel = st.selectbox("📅 Selecione a Data da Aula:", df_aluna['Data'].unique())
            # Filtramos apenas o que é "Aula" para não vir lixo do banco
            dados_dia = df_aluna[(df_aluna['Data'] == data_sel) & (df_aluna['Tipo'].str.contains('Aula_', na=False))]

            # --- SEÇÃO 1: PRÁTICA ---
            st.markdown("### 🎹 Prática")
            p_data = dados_dia[dados_dia['Tipo'].str.contains('Prática|Pratica', case=False, na=False)]
            
            if not p_data.empty:
                for _, p in p_data.iterrows():
                    # Extrai o nome do método de forma limpa
                    metodo = p['Tipo'].split('_')[-1].replace("_", " ")
                    difs_p = p.get('Dificuldades', [])
                    difs_txt = ", ".join(difs_p) if isinstance(difs_p, list) else str(difs_p)
                    
                    with st.container(border=True):
                        st.markdown(f"#### 📖 Método: {metodo}")
                        col_info1, col_info2 = st.columns(2)
                        col_info1.markdown(f"**👩‍🏫 Instrutora:** {p.get('Instrutora') or '---'}")
                        col_info2.markdown(f"**📍 Lição:** {p.get('Licao_Atual', '---')}")
                        
                        if difs_txt and difs_txt not in ['[]', 'None', '']:
                            st.markdown(f"⚠️ **Dificuldades:** <span style='color: #C0392B;'>{difs_txt}</span>", unsafe_allow_html=True)
                        
                        st.markdown(f"📝 **Observações:** {p.get('Observacao', '---')}")
                        
                        st.markdown(f"""
                            <div style="background-color: #F4F6F7; padding: 10px; border-radius: 5px; border-left: 3px solid #2980B9;">
                                <b>🏠 Lição de casa:</b> {p.get('Licao_Casa', '---')}
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.caption("Nenhum registro de Prática para este dia.")

            # --- SEÇÃO 2: TEORIA E SOLFEJO ---
            c_teoria, c_solfejo = st.columns(2)
            with c_teoria:
                st.markdown("### 📝 Teoria")
                t_data = dados_dia[dados_dia['Tipo'].str.contains('Teoria', na=False)]
                for _, t in t_data.iterrows():
                    with st.container(border=True):
                        st.write(f"**Lição:** {t.get('Licao_Atual', '---')}")
                        st.caption(f"Obs: {t.get('Observacao', '---')}")

            with c_solfejo:
                st.markdown("### 🗣️ Solfejo")
                s_data = dados_dia[dados_dia['Tipo'].str.contains('Solfejo', na=False)]
                for _, s in s_data.iterrows():
                    with st.container(border=True):
                        st.write(f"**Lição:** {s.get('Licao_Atual', '---')}")
                        st.caption(f"Obs: {s.get('Observacao', '---')}")

            # --- GRÁFICO FUNCIONAL (FILTRADO) ---
            st.divider()
            st.subheader("📈 Evolução Técnica")
            # Aqui filtramos para contar apenas "Métodos de Aula", ignorando Chamada e Controle
            df_grafico = df_aluna[df_aluna['Tipo'].str.contains('Aula_', na=False)].copy()
            
            if not df_grafico.empty:
                # Agrupamos por data e contamos quantos registros de "Aula" existem
                evol_res = df_grafico.groupby('dt_obj').size().reset_index(name='Volume de Estudo')
                
                fig = px.line(evol_res, x='dt_obj', y='Volume de Estudo', 
                              title="Constância Pedagógica (Quantidade de Métodos por Aula)",
                              markers=True, template="plotly_white")
                fig.update_traces(line_color='#2E4053', marker_size=10)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para gerar o gráfico de evolução.")

        st.divider()        


