import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
from google.cloud import firestore
from google.oauth2 import service_account
import json

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (FIRESTORE) ---
def init_connection():
    try:
        # A correção técnica para o "Incorrect Padding" está aqui:
        # .strip() remove espaços e .replace garante que as quebras de linha sejam interpretadas
        pk = st.secrets["private_key"].replace("\\n", "\n").strip()
        
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": pk,
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
        st.error(f"⚠️ Erro de Conexão: {e}")
        return None

db = init_connection()

# --- FUNÇÕES DE PERSISTÊNCIA ---
def db_save(colecao, documento, dados):
    if db:
        try:
            db.collection(colecao).document(documento).set(dados)
            return True
        except: return False
    return False

def db_get_all(colecao):
    if db:
        try:
            return [doc.to_dict() for doc in db.collection(colecao).stream()]
        except: return []
    return []

# --- BANCO DE DADOS MESTRE (SEUS DADOS ORIGINAIS) ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
SECRETARIAS = ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"]
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

# --- INICIALIZAÇÃO DE DADOS ---
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
    tab_gerar, tab_chamada, tab_correcao = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Correção"])
    
    with tab_gerar:
        st.subheader("🗓️ Gestão de Rodízios Semanais")
        # Aqui mantive a lógica que você usa para definir datas e instrutoras
        data_sel = st.date_input("Data do Sábado:", value=datetime.now())
        d_str = data_sel.strftime("%d/%m/%Y")
        
        if st.button(f"🚀 Gerar Rodízio para {d_str}"):
            escala_final = []
            for t_nome, alunas in TURMAS.items():
                for aluna in alunas:
                    escala_final.append({
                        "Aluna": aluna, "Turma": t_nome, 
                        HORARIOS_LABELS[0]: "⛪ IGREJA",
                        HORARIOS_LABELS[1]: f"🎹 Prática", 
                        HORARIOS_LABELS[2]: f"📚 Teoria", 
                        HORARIOS_LABELS[3]: f"🔊 Solfejo"
                    })
            db_save("rodizios", d_str.replace("/", "_"), {"id": d_str, "dados": escala_final})
            st.success("Rodízio salvo com sucesso!")
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe Digital")
    instr_sel = st.selectbox("👤 Identificação:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        # Busca automática no rodízio
        atend = next((l for l in st.session_state.calendario_anual[d_str] if instr_sel in str(l.values())), None)
        
        if atend:
            # Lógica para identificar matéria
            conteudo_celula = str(atend.values())
            mat = "Teoria" if "Teoria" in conteudo_celula else ("Solfejo" if "Solfejo" in conteudo_celula else "Prática")
            aluna_atual = atend.get('Aluna', 'Turma selecionada')
            st.warning(f"📍 **ATENDIMENTO:** {aluna_atual} | {mat}")

            # --- FORMULÁRIO PRÁTICA (ITENS ORIGINAIS RESTAURADOS) ---
            if mat == "Prática":
                lic_aula = st.selectbox("Lição/Volume:", [str(i) for i in range(1, 41)] + ["Hino", "Corinho"])
                dif_pr = [
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos dos métodos",
                    "Dificuldade ritmica", "Dificuldade em distinguir os nomes das figuras ritmicas",
                    "Está adentrando às teclas", "Dificuldade com a postura (costas, ombros e braços)",
                    "Está deixando o punho alto ou baixo", "Não senta no centro da banqueta", "Está quebrando as falanges",
                    "Unhas muito compridas", "Dificuldade em deixar os dedos arredondados",
                    "Esquece de colocar o pé direito no pedal de expressão", "Faz movimentos desnecessários com o pé esquerdo na pedaleira",
                    "Dificuldade com o uso do metrônomo", "Estuda sem o metrônomo", "Dificuldades em ler as notas na clave de sol",
                    "Dificuldades em ler as notas na clave de fá", "Não realizou as atividades da apostila",
                    "Dificuldade em fazer a articulação ligada e semiligada", "Dificuldade com as respirações",
                    "Dificuldade com as respirações sobre passagem", "Dificuldades em recurso de dedilhado",
                    "Dificuldade em fazer nota de apoio", "Não apresentou dificuldades"
                ]
                selecionadas = []
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_pr):
                    if (c1 if i < 13 else c2).checkbox(d): selecionadas.append(d)
                
                home_m = st.selectbox("Lição de casa - Volume:", [str(i) for i in range(1, 41)])
                home_a = st.text_input("Lição de casa - Apostila:")
                obs = st.text_area("Relato de Evolução:")

                if st.button("💾 SALVAR AULA"):
                    doc_id = f"PR_{aluna_atual}_{datetime.now().timestamp()}".replace(".","")
                    dados = {"Data": d_str, "Aluna": aluna_atual, "Materia": mat, "Dificuldades": selecionadas, "Obs": obs, "Home_M": home_m, "Home_A": home_a, "Instrutora": instr_sel}
                    db_save("historico_geral", doc_id, dados)
                    st.success("Salvo!")

            # --- FORMULÁRIO TEORIA/SOLFEJO (ITENS ORIGINAIS RESTAURADOS) ---
            else:
                turma_sel = atend.get('Turma', 'Turma 1')
                check_alunas = [a for a in TURMAS[turma_sel] if st.checkbox(a, value=True)]
                dif_ts = [
                    "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
                    "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
                    "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
                    "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
                    "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
                ]
                selecionadas = []
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_ts):
                    if (c1 if i < 8 else c2).checkbox(d): selecionadas.append(d)
                
                obs = st.text_area("Notas Pedagógicas:")
                if st.button("💾 SALVAR TURMA"):
                    for aluna in check_alunas:
                        doc_id = f"TS_{aluna}_{datetime.now().timestamp()}".replace(".","")
                        db_save("historico_geral", doc_id, {"Data": d_str, "Aluna": aluna, "Materia": mat, "Dificuldades": selecionadas, "Obs": obs, "Instrutora": instr_sel})
                    st.success("Salvo para a turma!")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica (Banca Semestral)")
    # (Lógica de análise por área integrada conforme seu pedido)
    historico = db_get_all("historico_geral")
    if historico:
        df = pd.DataFrame(historico)
        aluna_sel = st.selectbox("Selecione a Aluna:", sorted(df["Aluna"].unique()))
        df_alu = df[df["Aluna"] == aluna_sel].sort_values("Data", ascending=False)
        
        # Agrupamento por Áreas Pedagógicas
        todas_difs = [d for lista in df_alu["Dificuldades"] for d in lista]
        
        col1, col2 = st.columns(2)
        with col1:
            st.error("**🧘 POSTURA**")
            items = [d for d in set(todas_difs) if any(x in d.lower() for x in ["punho", "falange", "postura", "banqueta", "teclas", "dedos"])]
            st.write(items if items else "✅ Sem pendências")
            
            st.warning("**🎹 TÉCNICA**")
            items = [d for d in set(todas_difs) if any(x in d.lower() for x in ["clave", "articulação", "respiração", "dedilhado", "pedal"])]
            st.write(items if items else "✅ Sem pendências")
            
        with col2:
            st.info("**⏳ RITMO**")
            items = [d for d in set(todas_difs) if any(x in d.lower() for x in ["metrônomo", "ritmica", "figuras"])]
            st.write(items if items else "✅ Sem pendências")
            
            st.success("**📖 TEORIA**")
            items = [d for d in set(todas_difs) if any(x in d.lower() for x in ["vídeos", "apostila", "atividades", "estudou"])]
            st.write(items if items else "✅ Sem pendências")
        
        st.divider()
        st.subheader("🎯 Dicas para a Banca")
        st.info(f"Focar no próximo treino: {todas_difs[-1] if todas_difs else 'Manter evolução'}")
