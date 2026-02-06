import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (FIRESTORE) ---
def init_connection():
    try:
        # Puxa os campos individuais salvos nos Secrets
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"],
        }
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=creds, project=st.secrets["project_id"])
    except Exception as e:
        st.error(f"⚠️ Erro de Conexão: Verifique os Secrets. Detalhe: {e}")
        return None

db = init_connection()

# --- FUNÇÕES DE PERSISTÊNCIA ---
def db_save(colecao, documento, dados):
    if db:
        try:
            db.collection(colecao).document(documento).set(dados)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar no banco: {e}")
    return False

def db_get_all(colecao):
    if db:
        try:
            return [doc.to_dict() for doc in db.collection(colecao).stream()]
        except:
            return []
    return []

# --- BANCO DE DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

# --- CARREGAMENTO DE DADOS ---
if "calendario_anual" not in st.session_state:
    rodizios_db = db_get_all("rodizios")
    st.session_state.calendario_anual = {r['id']: r['dados'] for r in rodizios_db if 'id' in r}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada = st.tabs(["🗓️ Planejamento", "📍 Chamada"])
    
    with tab_gerar:
        st.subheader("🗓️ Geração de Rodízio")
        data_sel = st.date_input("Selecione o Sábado:", value=datetime.now())
        d_str = data_sel.strftime("%d/%m/%Y")
        
        if st.button(f"🚀 Gerar Escala para {d_str}"):
            # Exemplo de lógica de rodízio (ajustável conforme sua regra)
            escala_exemplo = []
            for t_nome, alunas in TURMAS.items():
                for aluna in alunas:
                    escala_exemplo.append({
                        "Aluna": aluna, "Turma": t_nome,
                        HORARIOS_LABELS[0]: "⛪ Igreja",
                        HORARIOS_LABELS[1]: f"🎹 Prática ({PROFESSORAS_LISTA[0]})",
                        HORARIOS_LABELS[2]: f"📚 Teoria ({PROFESSORAS_LISTA[1]})",
                        HORARIOS_LABELS[3]: f"🔊 Solfejo ({PROFESSORAS_LISTA[2]})"
                    })
            db_save("rodizios", d_str.replace("/", "_"), {"id": d_str, "dados": escala_exemplo})
            st.success(f"Rodízio de {d_str} salvo!")
            st.rerun()

    with tab_chamada:
        st.subheader("📍 Presença Geral")
        historico = db_get_all("historico_geral")
        if historico:
            df_h = pd.DataFrame(historico)
            st.dataframe(df_h[["Data", "Aluna", "Materia", "Instrutora"]])
        else:
            st.info("Nenhuma aula registrada ainda.")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe Digital")
    instr_sel = st.selectbox("👤 Identificação:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data da Aula:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend = next((l for l in st.session_state.calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            texto_aula = atend[h_sel]
            mat = "Teoria" if "Teoria" in texto_aula else ("Solfejo" if "Solfejo" in texto_aula else "Prática")
            st.warning(f"📍 **ATENDIMENTO:** {atend['Aluna'] if mat == 'Prática' else atend['Turma']} | {mat}")

            # --- CAMPOS COMUNS ---
            if mat == "Prática":
                aluna_p = atend['Aluna']
                lic_aula = st.selectbox("Lição/Volume:", [str(i) for i in range(1, 41)] + ["Hino", "Corinho"])
                dif_lista = [
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos",
                    "Dificuldade ritmica", "Dificuldade em distinguir figuras", "Adentrando às teclas",
                    "Postura (costas, ombros, braços)", "Punho alto ou baixo", "Fora do centro da banqueta",
                    "Quebrando as falanges", "Unhas compridas", "Dedos arredondados", "Pedal de expressão",
                    "Movimentos pedaleira", "Uso do metrônomo", "Estuda s/ metrônomo", "Clave de Sol",
                    "Clave de Fá", "Atividades apostila", "Articulação ligada/semiligada", "Respirações",
                    "Respirações s/ passagem", "Recurso dedilhado", "Nota de apoio", "Sem dificuldades"
                ]
            else:
                aluna_p = st.selectbox("Aluna da Turma:", TURMAS[atend['Turma']])
                lic_aula = st.text_input("Assunto/Lição:")
                dif_lista = [
                    "Vídeos complementares", "Clave de Sol", "Clave de Fá", "Metrônomo",
                    "Atividades", "Leitura Rítmica", "Leitura Métrica", "Solfejo (afinação)",
                    "Movimento da mão", "Ordem das notas", "Apostila", "Não estudou", "Sem dificuldades"
                ]

            selecionadas = []
            c1, c2 = st.columns(2)
            for i, d in enumerate(dif_lista):
                if (c1 if i < len(dif_lista)/2 else c2).checkbox(d): selecionadas.append(d)
            
            obs = st.text_area("Relato de Evolução (Pedagógico):")
            
            if st.button("💾 SALVAR REGISTRO"):
                doc_id = f"{aluna_p}_{datetime.now().timestamp()}".replace(".","")
                db_save("historico_geral", doc_id, {
                    "Data": d_str, "Aluna": aluna_p, "Materia": mat, "Licao": lic_aula,
                    "Dificuldades": selecionadas, "Obs": obs, "Instrutora": instr_sel
                })
                st.success("Aula registrada com sucesso!")
        else:
            st.error("Escala não encontrada para você neste horário.")
    else:
        st.info("Rodízio não gerado para hoje.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica (Banca Semestral)")
    dados = db_get_all("historico_geral")
    
    if not dados:
        st.info("Aguardando registros para análise.")
    else:
        df = pd.DataFrame(dados)
        aluna_sel = st.selectbox("Selecione a Aluna para Análise Completa:", sorted(df["Aluna"].unique()))
        
        df_alu = df[df["Aluna"] == aluna_sel].sort_values("Data")
        
        # --- SEPARAÇÃO POR ÁREAS ---
        todas_difs = [d for lista in df_alu["Dificuldades"] for d in lista]
        
        areas = {
            "🧘 POSTURA": ["postura", "punho", "falange", "unha", "banqueta", "tecla", "dedo"],
            "🎹 TÉCNICA": ["articulação", "respiração", "dedilhado", "apoio", "pedal", "clave"],
            "⏳ RITMO": ["metrônomo", "rítmica", "métrica", "figuras"],
            "📖 TEORIA/ESTUDO": ["vídeo", "apostila", "atividade", "estudou", "notas"]
        }

        st.subheader(f"📋 Relatório Pedagógico: {aluna_sel}")
        cols = st.columns(4)
        for i, (area, palavras) in enumerate(areas.items()):
            with cols[i]:
                st.markdown(f"**{area}**")
                encontradas = [d for d in set(todas_difs) if any(p in d.lower() for p in palavras)]
                if encontradas:
                    for e in encontradas: st.write(f"❌ {e}")
                else:
                    st.write("✅ Excelente")

        st.divider()
        
        # --- DICAS PARA A BANCA ---
        st.subheader("🎯 Planejamento para a Banca Semestral")
        c_banca1, c_banca2 = st.columns(2)
        
        with c_banca1:
            st.info("**Foco de Treino Semanal:**")
            if "metrônomo" in str(todas_difs).lower():
                st.write("- Priorizar estabilidade rítmica com metrônomo em andamento lento.")
            if "falange" in str(todas_difs).lower() or "punho" in str(todas_difs).lower():
                st.write("- Exercícios de técnica de base (Hanon) para correção de postura de mão.")
            st.write("- Revisar transições de respiração e dedilhado nas lições atuais.")

        with c_banca2:
            st.success("**Metas Próxima Aula:**")
            st.write(f"1. Superar dificuldade em: {todas_difs[-1] if todas_difs else 'Evolução constante'}")
            st.write(f"2. Meta de Lição: {df_alu['Licao'].iloc[-1]}")

        # --- RESUMO DA SECRETARIA ---
        with st.expander("📂 Resumo Administrativo (Secretaria)"):
            st.write(f"**Total de Aulas:** {len(df_alu)}")
            st.write(f"**Última Instrutora:** {df_alu['Instrutora'].iloc[-1]}")
            st.write(f"**Histórico de Observações:**")
            for o in df_alu["Obs"]: st.write(f"- {o}")
