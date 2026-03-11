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
# MÓDULO SECRETARIA - VERSÃO INTEGRAL V50
# ==========================================
if menu == "🏠 Secretaria":
    tab_consolidado, tab_plan, tab_cham, tab_licao, tab_ajustes = st.tabs([
        "📊 Visão Geral Diária", 
        "🗓️ Planejamento", 
        "📍 Chamada", 
        "📝 Controle de Lições",
        "🛠️ Ajustar Registros"
    ])

    # 1. Carregamento Prévio de Dados
    historico_raw = db_get_historico()
    df_historico = pd.DataFrame(historico_raw)
    if not df_historico.empty:
        df_historico['dt_obj'] = pd.to_datetime(df_historico['Data'], format="%d/%m/%Y", errors='coerce')

    # --- ABA 1: VISÃO GERAL DIÁRIA (PENTAGRAMA PEDAGÓGICO) ---
    with tab_consolidado:
        c_data_v1, _ = st.columns([1, 2])
        data_visao = c_data_v1.date_input("📅 Data da Análise:", datetime.now(), key="sec_v_dia_final")
        dt_str_v = data_visao.strftime("%d/%m/%Y")
        
        st.markdown(f"<h2 style='text-align: center; color: #2E4053;'>🎼 Diário Pedagógico: {dt_str_v}</h2>", unsafe_allow_html=True)
        texto_para_copiar = f"📝 *RELATÓRIO PEDAGÓGICO - {dt_str_v}*\n\n"

        if df_historico.empty:
            st.info("Nenhum dado registrado.")
        else:
            df_dia = df_historico[df_historico['Data'] == dt_str_v]
            if df_dia.empty:
                st.warning(f"Sem registros para o dia {dt_str_v}.")
            else:
                for aluna_v in sorted(df_dia['Aluna'].unique()):
                    dados_aluna_v = df_dia[df_dia['Aluna'] == aluna_v]
                    st.markdown(f"""<div style="background-color: #F2F4F4; padding: 10px; border-left: 6px solid #2E4053; border-radius: 4px; margin-top: 25px;">
                                    <b style="font-size: 18px; color: #1B2631;">👤 {aluna_v.upper()}</b></div>""", unsafe_allow_html=True)
                    
                    texto_para_copiar += f"👤 *{aluna_v.upper()}*\n"
                    for _, r in dados_aluna_v.iterrows():
                        tipo = r['Tipo'].replace("Aula_", "").replace("_", " ")
                        instrutora = r.get('Instrutora', '---')
                        lic_casa = r.get('Licao_Casa', 'Não informada')
                        st.markdown(f"**🎹 {tipo}** ({instrutora})")
                        st.write(f"📖 **Hoje:** {r.get('Licao_Atual', '---')} | 🏠 **Casa:** {lic_casa}")
                        
                        difs = r.get('Dificuldades', [])
                        if difs: st.markdown(f"<span style='color: #C0392B;'>⚠️ Dificuldades: {', '.join(difs) if isinstance(difs, list) else difs}</span>", unsafe_allow_html=True)
                        if r.get('Observacao'): st.caption(f"📝 Obs: {r['Observacao']}")
                        
                        texto_para_copiar += f"  * {tipo}: {r.get('Licao_Atual', '---')} (Casa: {lic_casa})\n"
                    texto_para_copiar += "\n"
                    st.markdown("<hr style='border: 1px double #AEB6BF;'>", unsafe_allow_html=True)
                
                st.text_area("📋 Copiar para WhatsApp:", value=texto_para_copiar, height=150)

    # --- ABA 2: PLANEJAMENTO (COM DELETE DE RODÍZIO) ---
    with tab_plan:
        # [Lógica de Seleção de Sábados]
        c1, c2 = st.columns(2)
        mes_p = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1, key="plan_mes")
        ano_p = c2.selectbox("Ano:", [2026, 2027], key="plan_ano")
        sabados = [dia for semana in calendar.Calendar().monthdatescalendar(ano_p, mes_p) 
                   for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes_p]
        
        if sabados:
            data_sel_str = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados], key="plan_sab_sel")
            if data_sel_str in calendario_db:
                st.success(f"🗓️ Rodízio Ativo: {data_sel_str}")
                df_edit = st.data_editor(pd.DataFrame(calendario_db[data_sel_str]), use_container_width=True, hide_index=True)
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    if st.button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                        supabase.table("calendario").upsert({"id": data_sel_str, "escala": df_edit.to_dict(orient="records")}).execute()
                        st.toast("Salvo!"); st.rerun()
                with col_p2:
                    if st.button("🗑️ DELETAR ESTE RODÍZIO", use_container_width=True, type="secondary"):
                        supabase.table("calendario").delete().eq("id", data_sel_str).execute()
                        st.error("Rodízio Apagado!"); st.cache_data.clear(); st.rerun()

    # --- ABA 3: CHAMADA GERAL (SUA LÓGICA DE CHAVES ÚNICAS) ---
    with tab_cham:
        st.subheader("📍 Chamada Geral")
        data_ch_sel = st.selectbox("Selecione a Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_chamada_unica")
        presenca_padrao = st.toggle("Marcar todas como Presente por padrão", value=True)
        st.write("---")
        
        registros_chamada = []
        alunas_lista_ch = sorted([a for l in TURMAS.values() for a in l])
        
        for idx, aluna in enumerate(alunas_lista_ch):
            col1, col2, col3 = st.columns([2, 3, 3])
            col1.write(f"**{aluna}**")
            chave_status = f"status_{idx}_{aluna}_{data_ch_sel}"
            status = col2.radio(f"Status {aluna}", ["Presente", "Ausente", "Justificada"], index=0 if presenca_padrao else 1, key=chave_status, horizontal=True, label_visibility="collapsed")
            
            motivo = ""
            if status == "Justificada":
                chave_motivo = f"motivo_input_{idx}_{aluna}_{data_ch_sel}"
                motivo = col3.text_input("Motivo justificativa", key=chave_motivo, placeholder="Por quê?", label_visibility="collapsed")
            registros_chamada.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            novos_registros = [{"Data": data_ch_sel, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Observacao": r["Motivo"], "Licao_Atual": "Presença"} for r in registros_chamada]
            supabase.table("historico_geral").delete().eq("Data", data_ch_sel).eq("Tipo", "Chamada").execute()
            supabase.table("historico_geral").insert(novos_registros).execute()
            st.success("✅ Chamada Salva!"); st.cache_data.clear(); st.balloons()

    # --- ABA 4: CONTROLE DE LIÇÕES (CORREÇÃO E CONGELAMENTO COM FIX DE INDEXERROR) ---
        with tab_licao:
            st.subheader("Registro de Correção de Lições")
            c1, c2, c3 = st.columns([2, 1, 1])
            aluna_sel = c1.selectbox("Selecione a Aluna:", ALUNAS_LISTA, key="sec_aluna_sel_v51")
            sec_resp = c2.selectbox("Responsável Secretaria:", SECRETARIAS_LISTA, key="sec_resp_sel_v51")
            data_corr_dt = c3.date_input("Data da Correção:", datetime.now(), key="sec_data_sel_v51")
            data_corr_str = data_corr_dt.strftime("%d/%m/%Y")
        
            # 1. Filtragem de Pendências
            if not df_historico.empty:
                # Filtra lições que NÃO estão como "Realizado"
                pendencias = df_historico[
                    (df_historico['Aluna'] == aluna_sel) & 
                    (df_historico['Tipo'] == 'Controle_Licao') & 
                    (df_historico['Status'] != "Realizado")
                ].copy()
                
                if not pendencias.empty:
                    st.error(f"🚨 {len(pendencias)} Lições Pendentes para {aluna_sel}")
                    for i, (row_idx, p) in enumerate(pendencias.iterrows()):
                        with st.container(border=True):
                            ci, ca = st.columns([3, 2])
                            ci.markdown(f"**📅 {p['Data']}** — {p.get('Categoria', 'Lição')}\n\n📖 {p.get('Licao_Detalhe', '---')}")
                            nv_status = ca.radio("Resultado:", ["Realizado", "Não realizado", "Devolvido"], key=f"nv_st_{i}_{p['id']}")
                            nv_obs = ca.text_input("Obs Secretaria:", key=f"nv_obs_{i}_{p['id']}")
                            
                            if ca.button("Confirmar Correção", key=f"btn_nv_{i}_{p['id']}"):
                                supabase.table("historico_geral").update({
                                    "Status": nv_status, 
                                    "Observacao_Sec": nv_obs, 
                                    "Secretaria": sec_resp
                                }).eq("id", p['id']).execute()
                                st.success("✅ Atualizado!")
                                st.cache_data.clear()
                                st.rerun()
                else:
                    st.success(f"✅ Nenhuma lição pendente para {aluna_sel}.")
        
            st.divider()
        
            # 2. Formulário de Nova Atividade (Fix do IndexError)
            # Buscamos se já existe um registro para "hoje" para editar em vez de criar novo
            filtro_hoje = df_historico[
                (df_historico['Aluna'] == aluna_sel) & 
                (df_historico['Data'] == data_corr_str) & 
                (df_historico['Tipo'] == "Controle_Licao")
            ]
            
            # Se o filtro NÃO estiver vazio, pegamos o registro, senão enviamos um dicionário vazio
            registro_previo = filtro_hoje.iloc[-1].to_dict() if not filtro_hoje.empty else {}
        
            with st.form("f_nova_atividade_v51", clear_on_submit=False):
                st.markdown("### ✍️ Registrar Nova Atividade")
                
                # Define o índice da categoria se já existir no registro anterior
                idx_cat = 0
                cat_prev = registro_previo.get('Categoria', '')
                if cat_prev in CATEGORIAS_LICAO:
                    idx_cat = CATEGORIAS_LICAO.index(cat_prev)
        
                cat_sel = st.radio("Categoria:", CATEGORIAS_LICAO, index=idx_cat, horizontal=True)
                det_lic = st.text_input("Lição / Página:", value=registro_previo.get('Licao_Detalhe', ""), placeholder="Ex: Lição 02, pág 05")
                
                # Status
                idx_stat = 0
                stat_prev = registro_previo.get('Status', '')
                if stat_prev in STATUS_LICAO:
                    idx_stat = STATUS_LICAO.index(stat_prev)
                    
                status_sel = st.radio("Status hoje:", STATUS_LICAO, index=idx_stat, horizontal=True)
                obs_hoje = st.text_area("Observação Técnica:", value=registro_previo.get('Observacao', ""))
                
                btn_label = "🔄 ATUALIZAR REGISTRO" if registro_previo else "❄️ CONGELAR E SALVAR"
                
                if st.form_submit_button(btn_label):
                    if not det_lic:
                        st.error("⚠️ Informe a Lição/Página!")
                    else:
                        sucesso = db_save_historico({
                            "Aluna": aluna_sel, 
                            "Tipo": "Controle_Licao", 
                            "Data": data_corr_str,
                            "Secretaria": sec_resp, 
                            "Categoria": cat_sel, 
                            "Licao_Detalhe": det_lic,
                            "Status": status_sel, 
                            "Observacao": obs_hoje
                        })
                        if sucesso:
                            st.success("✅ Registro processado!")
                            st.cache_data.clear()
                            st.rerun()
                    
    # --- ABA 5: AJUSTAR REGISTROS (EXCLUSÃO INDIVIDUAL) ---
    with tab_ajustes:
        st.subheader("🛠️ Ajustar Lançamentos")
        al_aj = st.selectbox("Aluna:", ALUNAS_LISTA, key="aj_al_final")
        if not df_historico.empty:
            df_aj = df_historico[df_historico['Aluna'] == al_aj].sort_values('dt_obj', ascending=False)
            st.dataframe(df_aj[['Data', 'Tipo', 'Licao_Atual', 'Instrutora']], use_container_width=True)
            idx_d = st.selectbox("Apagar:", range(len(df_aj)), format_func=lambda x: f"{df_aj.iloc[x]['Data']} - {df_aj.iloc[x]['Tipo']}")
            if st.button("❌ APAGAR REGISTRO", type="secondary"):
                supabase.table("historico_geral").delete().eq("id", df_aj.iloc[idx_d]['id']).execute()
                st.success("Excluído!"); st.cache_data.clear(); st.rerun()
                
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









