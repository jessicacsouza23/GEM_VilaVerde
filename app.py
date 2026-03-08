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
        
        df_historico = pd.DataFrame(db_get_historico())
        data_hj = datetime.now()
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            aluna = st.selectbox("Selecione a Aluna:", ALUNAS_LISTA, key="sec_aluna")
        with c2:
            sec_resp = st.selectbox("Responsável Secretaria:", SECRETARIAS_LISTA, key="sec_resp")
        with c3:
            data_corr = st.date_input("Data da Correção:", data_hj, key="sec_data")
            data_corr_str = data_corr.strftime("%d/%m/%Y")

        # --- LÓGICA DE PENDÊNCIAS (Vem das Professoras) ---
        if not df_historico.empty:
            df_alu = df_historico[df_historico['Aluna'] == aluna]
            if not df_alu.empty:
                # Filtramos tudo que é Controle_Licao e que NÃO está como "Realizado"
                pendencias = df_alu[
                    (df_alu['Tipo'] == 'Controle_Licao') & 
                    (df_alu['Status'] != "Realizado")
                ].copy()

                # --- EXIBIÇÃO DAS PENDÊNCIAS (COM CHAVES ÚNICAS) ---
        if not pendencias.empty:
            st.error(f"🚨 {len(pendencias)} Lições Pendentes para {aluna}")
            
            # Usamos enumerate para garantir um contador sequencial (i)
            for i, (row_idx, p) in enumerate(pendencias.iterrows()):
                # Criamos um ID único baseado nos dados da linha + contador
                # Isso evita duplicidade mesmo que a aluna tenha 2 lições na mesma data
                safe_key = f"{p['Data']}_{p['Categoria']}_{i}".replace("/", "")
                
                with st.container(border=True):
                    col_info, col_acao = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"**📅 {p['Data']}** — {p['Categoria']}")
                        st.markdown(f"📖 {p['Licao_Detalhe']}")
                        if p.get('Observacao'):
                            st.caption(f"💬 Nota da Prof: {p['Observacao']}")
                    
                    with col_acao:
                        # Adicionamos a safe_key em cada widget
                        novo_status = st.radio(
                            "Resultado:", 
                            ["Realizado", "Não realizado", "Devolvido para correção"],
                            key=f"status_{safe_key}", 
                            horizontal=True
                        )
                        nova_obs = st.text_input("Obs da Secretaria:", key=f"obs_sec_{safe_key}")
                        
                        if st.button("Confirmar Correção", key=f"btn_corr_{safe_key}"):
                            try:
                                supabase.table("historico_geral").update({
                                    "Status": novo_status,
                                    "Observacao": nova_obs,
                                    "Secretaria": sec_resp
                                }).eq("Aluna", p['Aluna'])\
                                  .eq("Data", p['Data'])\
                                  .eq("Tipo", "Controle_Licao")\
                                  .eq("Categoria", p['Categoria']).execute()
                                
                                st.success("✅ Atualizado!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
        else:
            st.success("✅ Nenhuma lição pendente para esta aluna.")
        
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
# MÓDULO PROFESSORA - V9 (AGRUPAMENTO POR TURMA)
# ==========================================
elif menu == "👩‍🏫 Minhas Aulas":
    st.header("👩‍🏫 Controle de Desempenho")

    # 1. Funções de Busca
    def db_get_metodos():
        try:
            res = supabase.table("config_metodos").select("*").execute()
            return pd.DataFrame(res.data)
        except: return pd.DataFrame()

    df_met_db = db_get_metodos()

    # 2. Identificação e Data
    instr_sel = st.session_state.get('nome_logado', 'Selecione...')
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"Instrutora Logada: **{instr_sel}**")
    with c2:
        hoje_dt = datetime.now()
        sab_p = hoje_dt + timedelta(days=(5 - hoje_dt.weekday()) % 7)
        data_prof = st.date_input("Data da Aula:", sab_p, key="dt_v9")
        data_prof_str = data_prof.strftime("%d/%m/%Y")

    # 3. Busca na Escala com Agrupamento por Turma/Sala
    if instr_sel != "Selecione...":
        calendario_db = db_get_calendario()
        aulas_agrupadas = {}
        nome_instrutora_busca = limpar_texto(instr_sel).lower().strip()
        esta_na_escala = False

        if data_prof_str in calendario_db:
            escala_dia = calendario_db[data_prof_str]
            
            for registro in escala_dia:
                aluna_nome = registro.get("Aluna", "Sem Nome")
                turma_nome = registro.get("Turma", "Individual")
                
                # Procura o nome da professora em todas as colunas (Rodízio)
                for col_h, conteudo in registro.items():
                    if col_h in ["Aluna", "Turma", "Data", "id", "created_at"]: continue
                    
                    if conteudo and nome_instrutora_busca in limpar_texto(str(conteudo)).lower():
                        esta_na_escala = True
                        
                        # Extração do Local (Ex: SALA 8)
                        local_sala = "GERAL"
                        if "-" in str(conteudo):
                            local_sala = str(conteudo).split("-")[-1].strip().upper()
                        elif "SALA" in str(conteudo).upper():
                            local_sala = str(conteudo).upper().strip()

                        # CHAVE DE AGRUPAMENTO: Se for Sala 8 ou 9, agrupamos pelo nome da Turma
                        # Se for individual, usamos o nome da Aluna
                        eh_coletivo = any(s in local_sala for s in ["SALA 8", "SALA 9", "TEORIA", "SOLFEJO"])
                        
                        if eh_coletivo:
                            id_grupo = f"{col_h} - {local_sala} ({turma_nome})"
                        else:
                            id_grupo = f"{col_h} - {local_sala} ({aluna_nome})"

                        if id_grupo not in aulas_agrupadas:
                            aulas_agrupadas[id_grupo] = {
                                "horario": col_h, "local": local_sala, 
                                "turma": turma_nome, "alunas": [], "eh_turma": eh_coletivo
                            }
                        
                        if aluna_nome not in aulas_agrupadas[id_grupo]["alunas"]:
                            aulas_agrupadas[id_grupo]["alunas"].append(aluna_nome)

        if not esta_na_escala:
            st.warning(f"Irmã {instr_sel}, nenhuma aula encontrada para este dia.")
        else:
            st.markdown("### 🎹 1. Selecione a Aula")
            # Mostra apenas um botão por Turma/Horário
            escolha_id = st.radio("Horários disponíveis:", list(aulas_agrupadas.keys()), horizontal=True)

            dados_aula = aulas_agrupadas[escolha_id]
            alunas_da_lista = dados_aula["alunas"]
            tipo_aula = "Teoria" if "SALA 8" in dados_aula["local"] else "Solfejo" if "SALA 9" in dados_aula["local"] else "Prática"
            dif_lista = DIF_TEORIA if tipo_aula == "Teoria" else DIF_SOLFEJO if tipo_aula == "Solfejo" else DIF_PRATICA

            st.divider()
            
            # --- 2. SELEÇÃO DE ALUNAS (CHECKBOXES LADO A LADO) ---
            st.markdown(f"### 👥 Alunas da Aula: {dados_aula['local']}")
            alunas_selecionadas = []
            
            # Cria colunas para as alunas (máximo 4 por linha)
            cols_alunas = st.columns(4)
            for i, aluna in enumerate(alunas_da_lista):
                with cols_alunas[i % 4]:
                    if st.checkbox(aluna, value=True, key=f"chk_{aluna}_{escolha_id}"):
                        alunas_selecionadas.append(aluna)

            if not alunas_selecionadas:
                st.info("Selecione as alunas para abrir o formulário.")
            else:
                # --- 3. FORMULÁRIO UNIFICADO ---
                with st.form("form_pedagogico_v9"):
                    st.subheader(f"📖 Registro de Aula - {tipo_aula}")
                    
                    # Filtro de Métodos do Banco
                    metodos_opcoes = ["Selecione..."]
                    if not df_met_db.empty:
                        m_filtrados = df_met_db[df_met_db['categoria'] == tipo_aula]['nome'].tolist()
                        metodos_opcoes.extend(m_filtrados)
                    
                    c_m1, c_m2 = st.columns(2)
                    metodo_v9 = c_m1.selectbox("Livro/Método Principal:", metodos_opcoes)
                    lic_v9 = c_m2.text_input("Lições Realizadas na Aula:", placeholder="Ex: 1 a 4")
                    
                    pendencia_v9 = st.text_area("📌 Lições Pendentes / Observações da Aula:", height=80)

                    st.divider()
                    st.subheader("🎯 Dificuldades")
                    cols_dif = st.columns(2)
                    difs_v9 = []
                    for i, d in enumerate(dif_lista):
                        if cols_dif[i % 2].checkbox(d, key=f"dif_v9_{d}_{escolha_id}"):
                            difs_v9.append(d)

                    st.divider()
                    st.subheader("🏠 Tarefa de Casa (Para Secretaria)")
                    st.caption("A secretaria verá estes itens para cobrar na próxima aula:")
                    
                    cc1, cc2, cc3 = st.columns(3)
                    casa_ap = cc1.text_input("Apostila (Lição):")
                    casa_msa_p = cc2.text_input("MSA Preto:")
                    casa_msa_v = cc3.text_input("MSA Verde:")
                    casa_extra = st.text_input("Atividade Extra / Folha Avulsa:")

                    # Consolidação da lição de casa
                    l_casa = []
                    if casa_ap: l_casa.append(f"Apostila: {casa_ap}")
                    if casa_msa_p: l_casa.append(f"MSA Preto: {casa_msa_p}")
                    if casa_msa_v: l_casa.append(f"MSA Verde: {casa_msa_v}")
                    if casa_extra: l_casa.append(f"Extra: {casa_extra}")
                    texto_casa = " | ".join(l_casa)

                    if st.form_submit_button("❄️ CONGELAR E SALVAR PARA SELECIONADAS"):
                        if metodo_v9 == "Selecione...":
                            st.error("Selecione o método antes de salvar.")
                        else:
                            for aluna_f in alunas_selecionadas:
                                # Deleta registros antigos do dia/tipo
                                supabase.table("historico_geral").delete().eq("Data", data_prof_str).eq("Tipo", f"Aula_{tipo_aula}").eq("Aluna", aluna_f).execute()
                                
                                # Salva Histórico Professora
                                db_save_historico({
                                    "Aluna": aluna_f, "Tipo": f"Aula_{tipo_aula}", "Data": data_prof_str,
                                    "Instrutora": instr_sel, 
                                    "Licao_Atual": f"Método: {metodo_v9} ({lic_v9}) | Pendente: {pendencia_v9}",
                                    "Dificuldades": difs_v9, "Licao_Casa": texto_casa
                                })

                                # Salva para Secretaria (se houver lição de casa)
                                if texto_casa:
                                    supabase.table("historico_geral").delete().eq("Aluna", aluna_f).eq("Data", data_prof_str).eq("Tipo", "Controle_Licao").eq("Categoria", tipo_aula).execute()
                                    db_save_historico({
                                        "Aluna": aluna_f, "Tipo": "Controle_Licao", "Data": data_prof_str,
                                        "Secretaria": "Aguardando", "Categoria": tipo_aula, 
                                        "Licao_Detalhe": texto_casa, "Status": "Não realizado"
                                    })
                            
                            st.balloons()
                            st.success(f"Salvo para: {', '.join(alunas_selecionadas)}")
                            st.rerun()
                            
# ==========================================
# MÓDULO ANÁLISE DE IA (LAYOUT CONSOLIDADO)
# ==========================================
elif menu == "📊 Analítico IA":
    st.title("📊 Painel Pedagógico de Performance")
    
    historico_raw = db_get_historico()
    df = pd.DataFrame(historico_raw)

    if df.empty:
        st.info("ℹ️ O banco de dados está vazio.")
    else:
        # Tratamento de datas e organização
        df['dt_obj'] = pd.to_datetime(df['Data'], format="%d/%m/%Y", errors='coerce')
        df = df.dropna(subset=['dt_obj']).sort_values('dt_obj', ascending=False)

        # Seleção da Aluna
        aluna_sel = st.selectbox("👤 Selecione a Aluna:", ALUNAS_LISTA, key="analise_aluna_auto")
        df_aluna = df[df['Aluna'] == aluna_sel]

        # --- RESUMO DE FALTAS ---
        df_chamada = df_aluna[df_aluna['Tipo'] == 'Chamada']
        faltas = len(df_chamada[df_chamada['Status'] == 'Ausente'])
        st.markdown(f"### 🚩 Faltas Acumuladas: `{faltas}`")
        st.divider()

        if not df_aluna.empty:
            datas_disponiveis = df_aluna['Data'].unique()
            data_sel = st.selectbox("📅 Selecione a Data da Aula:", datas_disponiveis)
            
            # Filtro dos dados do dia
            dados_dia = df_aluna[df_aluna['Data'] == data_sel]

            # --- CABEÇALHO DO RELATÓRIO ---
            st.markdown(f"<h1 style='text-align: center; color: #1E1E1E;'>{aluna_sel.upper()}</h1>", unsafe_allow_html=True)
            st.divider()

            # --- SEÇÃO 1: PRÁTICA ---
            st.markdown("### 🎹 Prática")
            p_data = dados_dia[dados_dia['Tipo'].str.contains('Prática|Pratica', case=False, na=False)]
            if not p_data.empty:
                p = p_data.iloc[0]
                difs_p = p.get('Dificuldades', [])
                # Formata lista de dificuldades se for lista
                difs_txt = ", ".join(difs_p) if isinstance(difs_p, list) else difs_p
                
                st.markdown(f"""
                **Data:** {data_sel}  
                **Instrutora:** {p.get('Instrutora') or '---'}  
                **Estudo / Lição:** {p.get('Licao_Atual', '---')}  
                **Dificuldades:** {difs_txt if difs_txt else 'Não apresentou dificuldades'}  
                **Observações:** {p.get('Observacao', '---')}  
                **Lição de casa – Volume prática:** {p.get('Licao_Casa', '---')}
                """)
            else:
                st.caption("Sem registros de Prática para este dia.")

            # --- SEÇÃO 2: TEORIA ---
            st.markdown("### 📝 Teoria")
            t_data = dados_dia[dados_dia['Tipo'].str.contains('Teoria', case=False, na=False)]
            if not t_data.empty:
                t = t_data.iloc[0]
                st.markdown(f"""
                **Data:** {data_sel}  
                **Instrutora:** {t.get('Instrutora') or '---'}  
                **Lição/Volume:** {t.get('Licao_Atual', '---')}  
                **Dificuldades:** {t.get('Dificuldades', 'Não apresentou dificuldades')}  
                **Observações:** {t.get('Observacao', '---')}  
                **Lição de casa:** {t.get('Licao_Casa', '---')}
                """)
            else:
                st.caption("Sem registros de Teoria para este dia.")

            # --- SEÇÃO 3: SOLFEJO ---
            st.markdown("### 🗣️ Solfejo")
            s_data = dados_dia[dados_dia['Tipo'].str.contains('Solfejo', case=False, na=False)]
            if not s_data.empty:
                s = s_data.iloc[0]
                st.markdown(f"""
                **Data:** {data_sel}  
                **Instrutora:** {s.get('Instrutora') or '---'}  
                **Lição/Volume:** {s.get('Licao_Atual', '---')}  
                **Dificuldades:** {s.get('Dificuldades', 'Não apresentou dificuldades')}  
                **Observações:** {s.get('Observacao', '---')}  
                **Lição de casa:** {s.get('Licao_Casa', '---')}
                """)
            else:
                st.caption("Sem registros de Solfejo para este dia.")

            # --- SEÇÃO 4: LIÇÕES DE CASA (SECRETARIA / CONTROLE) ---
            st.markdown("### 📚 Lições de Casa")
            sec_data = dados_dia[dados_dia['Tipo'].str.contains('Controle_Licao', case=False, na=False)]
            if not sec_data.empty:
                for _, row in sec_data.iterrows():
                    st.info(f"""
                    **Categoria:** {row.get('Categoria', 'Geral')}  
                    **{row.get('Status', 'Status')}:** {row.get('Observacao', 'Sem pendências')}
                    """)
            else:
                st.caption("Sem registros de lição de casa validados pela secretaria.")

            # --- SEÇÃO 5: ANÁLISE PEDAGÓGICA POR ÁREAS (AUTOMÁTICA) ---
            st.divider()
            st.subheader("🎯 Planejamento e Metas")
            
            # Lógica para Dicas da Banca (Exemplo baseado no instrumento)
            col_metas, col_banca = st.columns(2)
            with col_metas:
                st.markdown("**Metas para a Próxima Aula:**")
                st.success("1. Evoluir lição atual com metrônomo\n2. Corrigir postura de dedos arredondados")
            
            with col_banca:
                st.markdown("**Dicas para a Banca Semestral:**")
                st.warning("Atenção especial à articulação técnica e ao uso do pedal de expressão.")

            # --- RODÍZIO (AULAS AGENDADAS) ---
            st.divider()
            st.markdown("### 📅 Próximas Aulas Agendadas")
            
            # 1. Pegamos a data de hoje para filtrar apenas o que é futuro
            hoje_dt = datetime.now().date()
            
            # 2. Criamos uma lista para consolidar as próximas aulas
            proximas_aulas = []
            
            # 3. Varremos o dicionário do calendário
            # Ordenamos as datas para aparecerem na sequência correta
            for data_str in sorted(calendario_db.keys()):
                try:
                    # Converte a chave (string) em data para comparar
                    data_escala_dt = datetime.strptime(data_str, "%d/%m/%Y").date()
                    
                    if data_escala_dt >= hoje_dt:
                        escala_dia = pd.DataFrame(calendario_db[data_str])
                        # Filtra a aluna específica neste dia
                        minha_linha = escala_dia[escala_dia['Aluna'] == aluna_sel].copy()
                        
                        if not minha_linha.empty:
                            # Adicionamos uma coluna de data para o relatório
                            minha_linha.insert(0, "Data da Aula", data_str)
                            proximas_aulas.append(minha_linha)
                except:
                    continue

            if proximas_aulas:
                # Une todas as linhas encontradas em um único DataFrame
                df_proximas = pd.concat(proximas_aulas)
                
                # Definimos as colunas alvo (ajustadas para bater com seus nomes exatos)
                colunas_alvo = ['Data da Aula', 'Turma', '08h45 (Igreja)', '09h35(H2)', '10h10(H3)', '10h45(H4)']
                
                # Filtra apenas as colunas que existem no banco (evita erro de digitação/espaços)
                colunas_validas = [c for c in colunas_alvo if c in df_proximas.columns]
                
                st.write(f"Confira abaixo o cronograma de aulas para **{aluna_sel}**:")
                st.dataframe(df_proximas[colunas_validas], hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum rodízio futuro encontrado para esta aluna no sistema.")
                
        st.divider()
        if st.checkbox("Ver Gráficos de Evolução"):
            # Exemplo de gráfico de presença
            st.markdown("#### Evolução de Presença")
            fig_faltas = px.bar(x=['Presenças', 'Faltas'], y=[len(df_chamada[df_chamada['Status'] == 'Presente']), faltas], 
                                color_discrete_sequence=['#2ecc71', '#e74c3c'])
            st.plotly_chart(fig_faltas, use_container_width=True)
















