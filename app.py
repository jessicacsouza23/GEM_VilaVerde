import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide")

# --- CONEXÃO BANCO ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# --- DADOS MESTRE ---
ALUNAS_LISTA = sorted([
    "Mariana - Vila Araguaia", "Annie - Vila Verde", "Ana Marcela S. - Vila Verde", 
    "Caroline C. - Vila Ré", "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá Velha", 
    "Gabrielly V. - Vila Verde", "Heloísa R. - Vila Verde", "Ingrid M. - Pq do Carmo II", 
    "Júlia Cristina - União de Vila Nova", "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá Velha", 
    "Mellina S. - Jardim Lígia", "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", 
    "Rebeca R. - Vila Ré", "Rebecca A. - Vila Verde", "Rebeka S. - Jardim Lígia", 
    "Sarah S. - Vila Verde", "Vitória A. - Vila Verde", "Vitória Bella T. - Vila Verde"
])

# --- FUNÇÕES DE DADOS ---
def db_get_historico():
    res = supabase.table("historico_geral").select("*").execute()
    return res.data

def db_get_calendario():
    res = supabase.table("calendario").select("*").execute()
    return {item['id']: item['escala'] for item in res.data}

# ==========================================
# MÓDULO ANÁLISE (O NOVO CORAÇÃO DO SISTEMA)
# ==========================================
st.title("📊 Painel Pedagógico de Performance")

historico_raw = db_get_historico()
calendario_db = db_get_calendario()
df = pd.DataFrame(historico_raw)

if df.empty:
    st.info("ℹ️ Nenhum dado registrado no histórico.")
    st.stop()

# Tratamento de datas
df['dt_obj'] = pd.to_datetime(df['Data'], format="%d/%m/%Y", errors='coerce')
df = df.dropna(subset=['dt_obj']).sort_values('dt_obj', ascending=False)

# Filtros Laterais
st.sidebar.header("Filtros de Análise")
aluna_sel = st.sidebar.selectbox("Selecione a Aluna:", ALUNAS_LISTA)
periodo = st.sidebar.selectbox("Período da Análise:", ["Geral", "Mensal", "Bimestral", "Semestral", "Anual"])

# Filtragem de dados da aluna
df_aluna = df[df['Aluna'] == aluna_sel]

# --- 1. RESUMO DE FREQUÊNCIA ---
faltas = len(df_aluna[(df_aluna['Tipo'] == 'Chamada') & (df_aluna['Status'] == 'Ausente')])
presencas = len(df_aluna[(df_aluna['Tipo'] == 'Chamada') & (df_aluna['Status'] == 'Presente')])
justificativas = len(df_aluna[(df_aluna['Tipo'] == 'Chamada') & (df_aluna['Status'] == 'Justificada')])

m1, m2, m3 = st.columns(3)
m1.metric("Total de Faltas", f"{faltas} dias", delta="Atenção" if faltas > 2 else None, delta_color="inverse")
m2.metric("Presenças Confirmadas", presencas)
m3.metric("Justificativas", justificativas)

st.divider()

# --- 2. RELATÓRIO TÉCNICO DETALHADO (POR DATA) ---
st.subheader(f"📖 Relatório de Evolução: {aluna_sel}")

datas_disponiveis = df_aluna['Data'].unique()
if len(datas_disponiveis) > 0:
    data_escolhida = st.selectbox("Consultar histórico do dia:", datas_disponiveis)
    
    # Filtra tudo dessa aluna nessa data
    dados_dia = df_aluna[df_aluna['Data'] == data_escolhida]
    
    # Organização das seções conforme sua solicitação
    col_a, col_b = st.columns(2)
    
    with col_a:
        # --- SEÇÃO PRÁTICA ---
        pratica = dados_dia[dados_dia['Tipo'] == 'Aula_Pratica']
        with st.container(border=True):
            st.markdown("### 🎹 Prática")
            if not pratica.empty:
                p = pratica.iloc[0]
                st.write(f"**Instrutora:** {p.get('Professor', '---')}")
                st.write(f"**Estudo:** {p.get('Licao_Atual', '---')}")
                st.warning(f"**Dificuldades:** {', '.join(p.get('Dificuldades', []))}")
                st.info(f"**Lição de Casa:** {p.get('Metas', '---')}")
                st.write(f"**Observações:** {p.get('Observacao', '---')}")
            else:
                st.caption("Nenhum registro de aula prática neste dia.")

        # --- SEÇÃO SOLFEJO ---
        solfejo = dados_dia[dados_dia['Tipo'] == 'Aula_Solfejo']
        with st.container(border=True):
            st.markdown("### 🗣️ Solfejo")
            if not solfejo.empty:
                s = solfejo.iloc[0]
                st.write(f"**Instrutora:** {s.get('Professor', '---')}")
                st.write(f"**Estudo:** {s.get('Licao_Atual', '---')}")
                st.warning(f"**Dificuldades:** {', '.join(s.get('Dificuldades', []))}")
                st.info(f"**Lição de Casa:** {s.get('Metas', '---')}")
            else:
                st.caption("Nenhum registro de solfejo neste dia.")

    with col_b:
        # --- SEÇÃO TEORIA ---
        teoria = dados_dia[dados_dia['Tipo'] == 'Aula_Teoria']
        with st.container(border=True):
            st.markdown("### 📝 Teoria")
            if not teoria.empty:
                t = teoria.iloc[0]
                st.write(f"**Instrutora:** {t.get('Professor', '---')}")
                st.write(f"**Estudo:** {t.get('Licao_Atual', '---')}")
                st.warning(f"**Dificuldades:** {', '.join(t.get('Dificuldades', []))}")
                st.info(f"**Lição de Casa:** {t.get('Metas', '---')}")
            else:
                st.caption("Nenhum registro de teoria neste dia.")

        # --- SEÇÃO SECRETARIA (LIÇÕES DE CASA) ---
        secretaria = dados_dia[dados_dia['Tipo'] == 'Controle_Licao']
        with st.container(border=True):
            st.markdown("### 📋 Status da Secretaria")
            if not secretaria.empty:
                for _, sec in secretaria.iterrows():
                    st.write(f"**{sec['Categoria']}:** {sec['Status']}")
                    st.caption(f"Obs: {sec['Observacao']}")
            else:
                st.caption("Sem validação da secretaria nesta data.")

st.divider()

# --- 3. GRÁFICOS DE DESEMPENHO E EVOLUÇÃO ---
st.subheader("📈 Análise de Desempenho (Gráficos)")

c1, c2 = st.columns(2)

with c1:
    st.markdown("#### Distribuição de Dificuldades")
    # Explode a lista de dificuldades para contar individualmente
    all_difs = df_aluna['Dificuldades'].explode().value_counts().reset_index()
    if not all_difs.empty:
        fig_dif = px.pie(all_difs, values='count', names='Dificuldades', hole=.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_dif, use_container_width=True)
    else:
        st.write("Dados insuficientes para gerar gráfico de dificuldades.")

with c2:
    st.markdown("#### Evolução de Conteúdo (Lições Concluídas)")
    # Gráfico de barras por mês mostrando volume de lições dadas como "Sem pendência"
    lic_ok = df_aluna[df_aluna['Status'] == 'Realizadas - sem pendência'].copy()
    if not lic_ok.empty:
        lic_ok['Mes'] = lic_ok['dt_obj'].dt.strftime('%m/%Y')
        evolucao = lic_ok.groupby('Mes').size().reset_index(name='Qtd')
        fig_evol = px.bar(evolucao, x='Mes', y='Qtd', text_auto=True, color_discrete_sequence=['#4CAF50'])
        st.plotly_chart(fig_evol, use_container_width=True)
    else:
        st.write("Nenhuma lição concluída registrada ainda.")

# --- 4. RODÍZIO E ESCALA ---
st.divider()
st.subheader("📅 Informações de Escala")

# Verifica quem deu aula na última data registrada
ultima_data = df_aluna['Data'].iloc[0] if not df_aluna.empty else None
if ultima_data:
    st.write(f"**Última aula registrada em:** {ultima_data}")
    
# Verifica escala futura (Próximo Sábado)
hoje = datetime.now()
proximo_sabado = (hoje + timedelta(days=(5 - hoje.weekday()) % 7)).strftime("%d/%m/%Y")

with st.expander(f"Verificar Escala para {proximo_sabado}"):
    if proximo_sabado in calendario_db:
        escala_dia = pd.DataFrame(calendario_db[proximo_sabado])
        minha_escala = escala_dia[escala_dia['Aluna'] == aluna_sel]
        if not minha_escala.empty:
            st.dataframe(minha_escala, hide_index=True)
        else:
            st.info("Aluna não escalada para este sábado.")
    else:
        st.warning("⚠️ Rodízio para o próximo sábado ainda não foi gerado pela secretaria.")
