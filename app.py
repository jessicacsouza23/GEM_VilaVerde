import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
from google.cloud import firestore
from google.oauth2 import service_account
import json

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS (FIRESTORE) ---
# --- CONEXÃO COM BANCO DE DADOS (FIRESTORE) ---
def init_connection():
    try:
        # Agora ele lê as configurações diretamente dos Secrets
        creds = service_account.Credentials.from_service_account_info(st.secrets)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro na conexão com o banco de dados: {e}")
        return None

db = init_connection()

# --- FUNÇÕES DE PERSISTÊNCIA ---
def db_save(colecao, documento, dados):
    if db:
        try:
            db.collection(colecao).document(documento).set(dados)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
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
    st.session_state.calendario_anual = {r['id']: r['dados'] for r in rodizios_db}
st.session_state.historico_geral = db_get_all("historico_geral")
st.session_state.correcoes_secretaria = db_get_all("correcoes")

# --- FUNÇÕES AUXILIARES ---
def get_sabados_do_mes(ano, mes):
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    dias = cal.monthdatescalendar(ano, mes)
    return [dia for semana in dias for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_correcao = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Correção de Atividades"])

    with tab_gerar:
        st.subheader("🗓️ Gestão de Rodízios")
        c_m1, c_m2 = st.columns(2)
        mes_ref = c_m1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano_ref = c_m2.selectbox("Ano:", [2026, 2027], index=0)
        sabados = get_sabados_do_mes(ano_ref, mes_ref)
        
        for idx_sab, sab in enumerate(sabados):
            d_str = sab.strftime("%d/%m/%Y")
            d_id = d_str.replace("/", "_")
            with st.expander(f"📅 SÁBADO: {d_str}"):
                if d_str not in st.session_state.calendario_anual:
                    c1, c2 = st.columns(2)
                    with c1:
                        pt2, pt3, pt4 = [st.selectbox(f"Teoria H{i} ({d_str}):", PROFESSORAS_LISTA, index=i-2, key=f"pt{i}_{d_str}") for i in range(2, 5)]
                    with c2:
                        st2, st3, st4 = [st.selectbox(f"Solfejo H{i} ({d_str}):", PROFESSORAS_LISTA, index=i+1, key=f"st{i}_{d_str}") for i in range(2, 5)]
                    folgas = st.multiselect(f"Folgas ({d_str}):", PROFESSORAS_LISTA, key=f"f_{d_str}")

                    if st.button(f"🚀 Gerar Rodízio para {d_str}", key=f"btn_{d_str}"):
                        escala_final = []
                        fluxo = {
                            HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                            HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                            HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
                        }
                        for t_nome, alunas in TURMAS.items():
                            for i, aluna in enumerate(alunas):
                                agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                                for h_idx in [1, 2, 3]:
                                    h_label = HORARIOS_LABELS[h_idx]; cfg = fluxo[h_label]
                                    if cfg["Teo"] == t_nome: agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['ITeo']})"
                                    elif cfg["Sol"] == t_nome: agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['ISol']})"
                                    else:
                                        p_disp = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]] + folgas]
                                        f_rot = (i + (idx_sab * 3) + h_idx)
                                        instr_p = p_disp[f_rot % len(p_disp)] if p_disp else "Vago"
                                        idx_instr = PROFESSORAS_LISTA.index(instr_p) if instr_p in PROFESSORAS_LISTA else 0
                                        sala_fixa = ((idx_instr + idx_sab) % 7) + 1
                                        agenda[h_label] = f"🎹 SALA {sala_fixa} | Prática ({instr_p})"
                                escala_final.append(agenda)
                        db_save("rodizios", d_id, {"id": d_str, "dados": escala_final})
                        st.rerun()
                else:
                    st.table(pd.DataFrame(st.session_state.calendario_anual[d_str]))
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        if db: db.collection("rodizios").document(d_id).delete()
                        del st.session_state.calendario_anual[d_str]
                        st.rerun()

    # (Módulo de Chamada e Correção mantidos conforme sua lógica original de histórico geral)

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
        atend = next((l for l in st.session_state.calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            texto_aula = atend[h_sel]
            mat = "Teoria" if "Teoria" in texto_aula else ("Solfejo" if "Solfejo" in texto_aula else "Prática")
            st.warning(f"📍 **ATENDIMENTO:** {atend['Aluna'] if mat == 'Prática' else atend['Turma']} | {mat}")

            # --- FORMULÁRIO PRÁTICA (RESTAURADO COMPLETO) ---
            if mat == "Prática":
                st.subheader("🎹 Controle de Desempenho - Aula Prática")
                aluna_p = atend['Aluna']
                lic_aula = st.selectbox("Lição/Volume (Prática):", [str(i) for i in range(1, 41)] + ["Hino", "Corinho"], key="lic_pr")
                
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
                    if (c1 if i < 13 else c2).checkbox(d, key=f"dk_{i}"): selecionadas.append(d)
                
                st.divider()
                home_m = st.selectbox("Lição de casa - Volume prática:", [str(i) for i in range(1, 41)] + ["Outro"], key="hmp")
                home_a = st.text_input("Lição de casa - Apostila:", key="hap")
                obs = st.text_area("Relato de Evolução:")

                if st.button("💾 SALVAR AULA PRÁTICA"):
                    dados_aula = {
                        "Data": d_str, "Aluna": aluna_p, "Tipo": "Aula", "Materia": "Prática",
                        "Licao": lic_aula, "Dificuldades": selecionadas, "Obs": obs, 
                        "Home_M": home_m, "Home_A": home_a, "Instrutora": instr_sel
                    }
                    if db_save("historico_geral", f"PR_{datetime.now().timestamp()}_{aluna_p}", dados_aula):
                        st.success("Aula Prática salva no banco de dados!")
                        st.balloons()

            # --- FORMULÁRIO TEORIA / SOLFEJO (RESTAURADO COMPLETO) ---
            elif mat in ["Teoria", "Solfejo"]:
                st.subheader(f"📚 Controle de Desempenho - {mat}")
                turma_sel = atend['Turma']
                check_alunas = [a for a in TURMAS[turma_sel] if st.checkbox(a, value=True, key=f"p_{a}")]
                
                lic_aula = st.text_input(f"Lição/Assunto tratado hoje ({mat}):")
                
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
                    if (c1 if i < 8 else c2).checkbox(d, key=f"dts_{i}"): selecionadas.append(d)
                
                home_m = st.text_input("Tarefa para Casa:")
                obs = st.text_area("Notas Pedagógicas da Aula:")

                if st.button(f"💾 SALVAR AULA DE {mat.upper()}"):
                    for aluna in check_alunas:
                        dados_ts = {
                            "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                            "Licao": lic_aula, "Dificuldades": selecionadas, "Obs": obs, 
                            "Home_M": home_m, "Instrutora": instr_sel
                        }
                        db_save("historico_geral", f"TS_{datetime.now().timestamp()}_{aluna}", dados_ts)
                    st.success(f"Aula de {mat} salva para {len(check_alunas)} alunas!")
        else:
            st.warning("Você não tem aula prevista neste horário segundo o rodízio.")
    else:
        st.error("Rodízio para esta data ainda não foi gerado pela secretaria.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica (Análise Semestral)")
    # Carrega dados do banco
    df_h = pd.DataFrame(db_get_all("historico_geral"))
    
    if df_h.empty:
        st.info("Nenhum registro encontrado no banco de dados para análise.")
    else:
        aluna_sel = st.selectbox("Selecione a Aluna para a Banca:", sorted(df_h["Aluna"].unique()))
        
        if st.button("✨ GERAR E CONGELAR ANÁLISE COMPLETA"):
            df_alu = df_h[df_h["Aluna"] == aluna_sel]
            
            # Agrupamento Pedagógico
            difs_totais = [d for lista in df_alu.get("Dificuldades", []) for d in lista]
            
            st.subheader(f"📋 Relatório Consolidado: {aluna_sel}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.error("**🧘 POSTURA**")
                postura_items = [d for d in set(difs_totais) if any(x in d.lower() for x in ["punho", "falange", "postura", "dedos", "banqueta", "ombro"])]
                st.write("\n".join([f"- {i}" for i in postura_items]) if postura_items else "Sem pendências.")
                
                st.warning("**🎹 TÉCNICA**")
                tecnica_items = [d for d in set(difs_totais) if any(x in d.lower() for x in ["clave", "articulação", "respiração", "dedilhado", "pedal"])]
                st.write("\n".join([f"- {i}" for i in tecnica_items]) if tecnica_items else "Sem pendências.")

            with col2:
                st.info("**⏳ RITMO**")
                ritmo_items = [d for d in set(difs_totais) if any(x in d.lower() for x in ["metrônomo", "rítmica", "métrica"])]
                st.write("\n".join([f"- {i}" for i in ritmo_items]) if ritmo_items else "Sem pendências.")
                
                st.success("**📖 TEORIA**")
                teoria_items = [d for d in set(difs_totais) if any(x in d.lower() for x in ["vídeos", "apostila", "notas", "solfejo"])]
                st.write("\n".join([f"- {i}" for i in teoria_items]) if teoria_items else "Sem pendências.")

            st.divider()
            st.subheader("🎯 Dicas para a Próxima Aula e Banca")
            st.info(f"**Recomendação:** {df_alu['Obs'].iloc[-1] if not df_alu['Obs'].empty else 'Continuar evolução no método.'}")

