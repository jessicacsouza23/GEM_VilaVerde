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
# MÓDULO SECRETARIA - RESTAURAÇÃO DA LÓGICA ORIGINAL
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

    # --- ABA 2: PLANEJAMENTO (LÓGICA ORIGINAL RESTAURADA) ---
    with tab_plan:
        st.subheader("🗓️ Planejamento de Rodízio")
        c1, c2 = st.columns(2)
        mes_p = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1, key="mes_p_vfinal")
        ano_p = c2.selectbox("Ano:", [2026, 2027], key="ano_p_vfinal")
        
        sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano_p, mes_p) 
                   for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes_p]
        
        if sabados:
            data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_p_vfinal")
            
            # Recupera o calendário do banco
            calendario_db = db_get_calendario()
            
            # Se já existir dados para esse sábado, usamos eles. Se não, criamos a base das Turmas.
            if data_sel_str in calendario_db:
                df_planejamento = pd.DataFrame(calendario_db[data_sel_str])
            else:
                # LÓGICA ORIGINAL: Monta a lista baseada no dicionário TURMAS
                lista_base = []
                for nome_turma, alunas in TURMAS.items():
                    for aluna in alunas:
                        lista_base.append({
                            "Turma": nome_turma,
                            "Aluna": aluna,
                            "Horário": "08:00",
                            "Instrutora": "A Definir"
                        })
                df_planejamento = pd.DataFrame(lista_base)

            st.write(f"### Escala para o dia {data_sel_str}")
            
            # Editor de dados para ajustar Horários e Instrutoras
            df_editado = st.data_editor(
                df_planejamento, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Turma": st.column_config.TextColumn("Turma", disabled=True),
                    "Aluna": st.column_config.TextColumn("Aluna", disabled=True),
                    "Horário": st.column_config.TextColumn("Horário", help="Ex: 08:00 - 09:30"),
                    "Instrutora": st.column_config.SelectboxColumn("Instrutora", options=INSTRUTORAS_LISTA)
                }
            )

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                if st.button("💾 SALVAR RODÍZIO", use_container_width=True, type="primary"):
                    # Salva no Supabase usando o ID como a Data
                    dados_para_salvar = {
                        "id": data_sel_str,
                        "escala": df_editado.to_dict(orient="records")
                    }
                    supabase.table("calendario").upsert(dados_para_salvar).execute()
                    st.success(f"Escala de {data_sel_str} salva com sucesso!")
                    st.cache_data.clear()
            
            with col_p2:
                if st.button("🗑️ LIMPAR DATA", use_container_width=True):
                    supabase.table("calendario").delete().eq("id", data_sel_str).execute()
                    st.warning("Dados removidos.")
                    st.cache_data.clear()
                    st.rerun()

    # --- ABA 3: CHAMADA (SIMPLIFICADA E DIRETA) ---
    with tab_cham:
        st.subheader("📍 Chamada Geral")
        data_ch_str = st.date_input("Data:", datetime.now(), key="dt_ch_sec").strftime("%d/%m/%Y")
        p_total = st.toggle("Todas Presentes", value=True)
        
        lista_presenca = []
        alunas_ordem = sorted([a for t in TURMAS.values() for a in t])
        
        for i, nome in enumerate(alunas_ordem):
            c1, c2, c3 = st.columns([2, 3, 2])
            c1.write(f"**{nome}**")
            st_ch = c2.radio(f"Status_{i}", ["Presente", "Ausente", "Justificada"], 
                             index=0 if p_total else 1, key=f"rad_ch_{i}", horizontal=True, label_visibility="collapsed")
            motivo = c3.text_input("Motivo", key=f"txt_ch_{i}", label_visibility="collapsed") if st_ch == "Justificada" else ""
            lista_presenca.append({"Aluna": nome, "Status": st_ch, "Observacao": motivo})

        if st.button("💾 SALVAR CHAMADA", use_container_width=True, type="primary"):
            payload = [{"Data": data_ch_str, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Observacao": r["Observacao"]} for r in lista_presenca]
            supabase.table("historico_geral").delete().eq("Data", data_ch_str).eq("Tipo", "Chamada").execute()
            supabase.table("historico_geral").insert(payload).execute()
            st.success("Chamada Salva!")
            st.cache_data.clear()
            
    # --- ABA 4: CONTROLE DE LIÇÕES ---
    with tab_licao:
        st.subheader("📝 Correção e Metas")
        al_lic = st.selectbox("Aluna:", ALUNAS_LISTA, key="l_al")
        sec_r = st.selectbox("Responsável:", SECRETARIAS_LISTA, key="l_sec")
        
        if not df_historico.empty:
            pend = df_historico[(df_historico['Aluna'] == al_lic) & (df_historico['Status'] != "Realizado") & ((df_historico['Licao_Casa'].notna()) | (df_historico['Tipo'] == "Controle_Licao"))].copy()
            if not pend.empty:
                for _, p in pend.sort_values('dt_obj', ascending=False).iterrows():
                    with st.container(border=True):
                        st.write(f"**{p.get('Categoria', 'Lição')}** - {p['Data']}")
                        st.info(p.get('Licao_Casa') or p.get('Licao_Detalhe'))
                        if st.button("Confirmar Realização", key=f"btn_ok_{p['id']}"):
                            supabase.table("historico_geral").update({"Status": "Realizado", "Secretaria": sec_r}).eq("id", p['id']).execute()
                            st.rerun()

        st.divider()
        with st.form("f_meta"):
            st.write("❄️ **Congelar Meta para Próxima Aula**")
            c_a, c_m = st.columns(2)
            cat = c_a.selectbox("Área:", ["MSA", "Apostila", "Teoria", "Hino"])
            meta = c_m.text_input("Lição:")
            obs = st.text_area("Análise Pedagógica:")
            if st.form_submit_button("Salvar Meta"):
                db_save_historico({"Aluna": al_lic, "Tipo": "Controle_Licao", "Data": datetime.now().strftime("%d/%m/%Y"), "Categoria": cat, "Licao_Detalhe": meta, "Status": "Pendente", "Observacao": obs, "Secretaria": sec_r})
                st.rerun()

    # --- ABA 5: AJUSTES ---
    with tab_ajustes:
        st.subheader("🛠️ Ajustar Registros")
        al_aj = st.selectbox("Aluna:", ALUNAS_LISTA, key="a_al")
        if not df_historico.empty:
            df_f = df_historico[df_historico['Aluna'] == al_aj].sort_values('dt_obj', ascending=False)
            if not df_f.empty:
                st.dataframe(df_f[['Data', 'Tipo', 'Licao_Atual']], use_container_width=True)
                idx = st.selectbox("Apagar registro:", range(len(df_f)), format_func=lambda x: f"{df_f.iloc[x]['Data']} - {df_f.iloc[x]['Tipo']}")
                if st.button("❌ APAGAR"):
                    supabase.table("historico_geral").delete().eq("id", df_f.iloc[idx]['id']).execute()
                    st.rerun()  

# ============================================================
# MÓDULO PROFESSORA - V35 (SALVAMENTO INDIVIDUALIZADO)
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
            met_del = st.selectbox("Selecione um método para remover:", ["Selecione..."] + df_metodos['nome'].tolist(), key="del_met_v35")
            if st.button("🗑️ Remover Método", key="btn_del_v35"):
                if met_del != "Selecione...":
                    supabase.table("config_metodos").delete().eq("nome", met_del).execute()
                    st.success(f"Método {met_del} removido!")
                    st.rerun()
        
        st.divider()
        st.write("✨ **Cadastrar Novo Método**")
        n_met = st.text_input("Nome do Método (ex: Bona, Czerny, Hanon):", key="new_met_v35")
        if st.button("➕ Cadastrar", key="btn_add_v35"):
            if n_met:
                supabase.table("config_metodos").insert({"nome": n_met, "categoria": "Prática"}).execute()
                st.success("Método cadastrado!")
                st.rerun()

    # --- ABA 2: REGISTRO DE AULA ---
    with tab_aula:
        instr_sel = st.session_state.get('nome_logado', 'Selecione...')
        
        c1, c2 = st.columns(2)
        with c1: st.info(f"Instrutora: **{instr_sel}**")
        with c2:
            hoje = datetime.now()
            sab_p = hoje if hoje.weekday() == 5 else hoje + timedelta(days=(5 - hoje.weekday()) % 7)
            data_prof = st.date_input("Data da Aula:", sab_p, key="data_aula_v35")
            dt_str = data_prof.strftime("%d/%m/%Y")

        if instr_sel != "Selecione...":
            cal_db = db_get_calendario()
            n_bus = limpar_texto(instr_sel).lower().strip()
            aulas = []

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
                sel_lbl = st.radio("Selecione o Horário/Turma:", [x["label"] for x in sorted(aulas, key=lambda x: x['h'])], key="radio_aulas_v35")
                d_sel = next(x for x in aulas if x["label"] == sel_lbl)
                
                st.divider()
                st.markdown(f"### 👥 Chamada: {d_sel['loc']}")
                
                als_ref = TURMAS.get(d_sel["tr"], [d_sel["al"]]) if d_sel["tipo"] != "Prática" else [d_sel["al"]]
                als_conf = []
                cols_ch = st.columns(4)
                for i, al in enumerate(als_ref):
                    if cols_ch[i%4].checkbox(al, value=True, key=f"ch_v35_{al}_{sel_lbl}"):
                        als_conf.append(al)

                if als_conf:
                    st.write("---")
                    st.subheader("📘 Passo 1: Escolha o Método")
                    
                    if d_sel["tipo"] == "Prática":
                        df_m = db_get_metodos()
                        m_opts = ["Selecione..."] + (df_m['nome'].tolist() if not df_m.empty else [])
                        met_v = st.selectbox("Qual livro/método você vai avaliar?", m_opts, key=f"sel_met_v35_{sel_lbl}")
                    else:
                        met_v = d_sel["tipo"]
                        st.info(f"Tipo de Aula: {met_v}")

                    # --- FORMULÁRIO DE REGISTRO ---
                    form_key = f"form_v35_{als_conf[0]}_{sel_lbl}_{met_v}".replace(" ", "_")
                    with st.form(key=form_key):
                        st.subheader(f"📝 Passo 2: Analisar {met_v}")
                        lic_v = st.text_input("Lição / Página Atual (Sala):", placeholder="O que ela tocou hoje?")
                        
                        st.markdown("**Dificuldades Detectadas:**")
                        d_lista = DIF_TEORIA if d_sel["tipo"] == "Teoria" else DIF_SOLFEJO if d_sel["tipo"] == "Solfejo" else DIF_PRATICA
                        c_dif = st.columns(2)
                        difs_finais = [dfc for idx, dfc in enumerate(d_lista) if c_dif[idx%2].checkbox(dfc, key=f"chk_v35_{dfc}_{form_key}")]

                        obs_v = st.text_area("Dicas Pedagógicas:", placeholder="Dica para a aluna melhorar...")

                        st.divider()
                        st.subheader("🏠 Passo 3: Lições para Casa (Individuais)")
                        st.caption("Cada campo abaixo gera uma pendência separada para a Secretaria.")
                        
                        l_casa_principal = st.text_input(f"Tarefa Principal de {met_v}:", placeholder="Ex: Lição 10 e 11")
                        l_casa_extra = st.text_input("Tarefa Extra / Complementar:", placeholder="Ex: Escala de Dó Maior")
                        
                        btn_salvar = st.form_submit_button("💾 CONGELAR REGISTROS")

                    # --- LÓGICA DE SALVAMENTO INDIVIDUALIZADO ---
                    if btn_salvar:
                        if met_v == "Selecione...":
                            st.error("⚠️ Selecione o método!")
                        else:
                            with st.spinner("Processando registros individuais..."):
                                tipo_final = f"Aula_{d_sel['tipo']}_{met_v}".replace(" ", "_")
                                
                                for al_f in als_conf:
                                    # 1. Limpa registros anteriores da mesma aula/método para evitar duplicatas
                                    supabase.table("historico_geral").delete().eq("Data", dt_str).eq("Tipo", tipo_final).eq("Aluna", al_f).execute()
                                    
                                    # 2. Prepara a base do registro
                                    base_dados = {
                                        "Aluna": al_f, "Tipo": tipo_final, "Data": dt_str,
                                        "Instrutora": instr_sel, "Licao_Atual": f"{met_v}: {lic_v}",
                                        "Dificuldades": difs_finais, "Observacao": obs_v,
                                        "Status": "Pendente"
                                    }

                                    # 3. SALVAMENTO EM LINHAS SEPARADAS (O SEGREDO)
                                    # Se houver lição principal, salva uma linha
                                    if l_casa_principal:
                                        dados_p = base_dados.copy()
                                        dados_p["Licao_Casa"] = f"{met_v}: {l_casa_principal}"
                                        db_save_historico(dados_p)
                                    
                                    # Se houver lição extra, salva outra linha independente
                                    if l_casa_extra:
                                        dados_e = base_dados.copy()
                                        dados_e["Licao_Casa"] = f"Extra: {l_casa_extra}"
                                        db_save_historico(dados_e)
                                    
                                    # Se não houver nada escrito, salva apenas o registro da aula
                                    if not l_casa_principal and not l_casa_extra:
                                        db_save_historico(base_dados)

                            st.success("✅ Lições enviadas individualmente para a secretaria!")
                            st.balloons()
                            time.sleep(1.5)
                            st.rerun()
                            
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









































