import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM BANCO DE DADOS ---
def init_connection():
    try:
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
        st.error(f"⚠️ Erro de Configuração de Credenciais: {e}")
        return None

db = init_connection()

# --- FUNÇÕES DE PERSISTÊNCIA ---
def db_save(colecao, documento, dados):
    if db:
        try:
            db.collection(colecao).document(documento).set(dados)
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

def db_get_all(colecao):
    if db:
        try:
            return [doc.to_dict() for doc in db.collection(colecao).stream()]
        except Exception as e:
            st.warning(f"Atenção: A coleção '{colecao}' está inacessível ou vazia. Verifique se o Firestore está em 'Modo de Teste'.")
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
HORARIOS_LABELS = ["08h45 às 09h30 (1ª Aula - Igreja)", "09h35 às 10h05 (2ª Aula)", "10h10 às 10h40 (3ª Aula)", "10h45 às 11h15 (4ª Aula)"]

# --- CARREGAMENTO INICIAL PROTEGIDO ---
try:
    calendario_anual = {doc['id']: doc['escala'] for doc in db_get_all("calendario") if 'id' in doc}
    historico_geral = db_get_all("historico")
    correcoes_secretaria = db_get_all("correcoes")
    analises_fixas_salvas = {doc['id']: doc['analise'] for doc in db_get_all("analises") if 'id' in doc}
except Exception:
    calendario_anual, historico_geral, correcoes_secretaria, analises_fixas_salvas = {}, [], [], {}

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
            with st.expander(f"📅 SÁBADO: {d_str}"):
                if d_str not in calendario_anual:
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
                        db_save("calendario", d_str.replace("/", "_"), {"id": d_str, "escala": escala_final})
                        st.rerun()
                else:
                    st.table(pd.DataFrame(calendario_anual[d_str]))
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        db.collection("calendario").document(d_str.replace("/", "_")).delete()
                        st.rerun()

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        data_ch_sel = st.selectbox("Selecione a Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_chamada_unica")
        presenca_padrao = st.toggle("Marcar todas como Presente por padrão", value=True)
        st.write("---")
        registros_chamada = []
        alunas_lista = sorted([a for l in TURMAS.values() for a in l])
        for aluna in alunas_lista:
            col1, col2, col3 = st.columns([2, 3, 3])
            col1.write(f"**{aluna}**")
            status = col2.radio(f"Status {aluna}", ["Presente", "Falta", "Justificada"], index=0 if presenca_padrao else 1, key=f"status_{aluna}_{data_ch_sel}", horizontal=True, label_visibility="collapsed")
            motivo = col3.text_input(f"Motivo justificativa", key=f"motivo_{aluna}_{data_ch_sel}", placeholder="Informe o motivo...", label_visibility="collapsed") if status == "Justificada" else ""
            registros_chamada.append({"Aluna": aluna, "Status": status, "Motivo": motivo})
        
        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            for reg in registros_chamada:
                doc_id = f"CH_{data_ch_sel.replace('/','_')}_{reg['Aluna']}"
                db_save("historico", doc_id, {"Data": data_ch_sel, "Aluna": reg["Aluna"], "Tipo": "Chamada", "Status": reg["Status"], "Motivo": reg["Motivo"]})
            st.success(f"Chamada do dia {data_ch_sel} salva com sucesso!")

    with tab_correcao:
        st.subheader("✅ Correção de Atividades")
        sec_resp = st.selectbox("Secretária Responsável:", SECRETARIAS)
        alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
        liçao_info = "Nenhuma lição encontrada"
        if historico_geral:
            df_h = pd.DataFrame(historico_geral)
            df_alu = df_h[(df_h["Aluna"] == alu_corr) & (df_h["Tipo"] == "Aula")]
            if not df_alu.empty:
                ult = df_alu.iloc[-1]
                liçao_info = f"Matéria: {ult.get('Materia','')} | Lição: {ult.get('Home_M','')} | Apostila: {ult.get('Home_A','')}"
        st.info(f"📋 **Lição registrada pela Professora:** {liçao_info}")
        status_corr = st.radio("Status:", ["Realizada", "Não Realizada", "Devolvida para Correção"], horizontal=True)
        obs_sec = st.text_area("Notas da Secretaria:")
        if st.button("💾 Salvar Registro de Correção"):
            doc_id = f"CORR_{datetime.now().timestamp()}"
            db_save("correcoes", doc_id, {"Data": datetime.now().strftime("%d/%m/%Y"), "Aluna": alu_corr, "Secretaria": sec_resp, "Atividade": liçao_info, "Status": status_corr, "Obs": obs_sec})
            st.success("Corrigido!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Identificação:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend = next((l for l in calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            sala_info = atend[h_sel].split("|")[0] if "|" in atend[h_sel] else "Igreja"
            quem_info = atend['Aluna'] if "Prática" in atend[h_sel] else atend['Turma']
            st.warning(f"📍 **ATENDIMENTO ATUAL:** {quem_info} | **LOCAL:** {sala_info}")
            st.divider()

            texto_aula = atend[h_sel]
            mat = "Teoria" if "Teoria" in texto_aula else ("Solfejo" if "Solfejo" in texto_aula else "Prática")
            check_alunas = [atend['Aluna']] if mat == "Prática" else [a for a in TURMAS[atend['Turma']] if st.checkbox(a, value=True, key=f"p_{a}")]
            
            selecionadas, home_m, home_a, lic_aula = [], "", "", ""

            if mat == "Prática":
                st.subheader("🎹 Controle de Desempenho - Aula Prática")
                lic_aula = st.selectbox("Lição/Volume (Prática):", [str(i) for i in range(1, 41)] + ["Outro"], key="lic_pr")
                dif_pr = ["Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos dos métodos", "Dificuldade ritmica", "Dificuldade em distinguir os nomes das figuras ritmicas", "Está adentrando às teclas", "Dificuldade com a postura (costas, ombros e braços)", "Está deixando o punho alto ou baixo", "Não senta no centro da banqueta", "Está quebrando as falanges", "Unhas muito compridas", "Dificuldade em deixar os dedos arredondados", "Esquece de colocar o pé direito no pedal de expressão", "Faz movimentos desnecessários com o pé esquerdo na pedaleira", "Dificuldade com o uso do metrônomo", "Estuda sem o metrônomo", "Dificuldades em ler as notas na clave de sol", "Dificuldades em ler as notas na clave de fá", "Não realizou as atividades da apostila", "Dificuldade em fazer a articulação ligada e semiligada", "Dificuldade com as respirações", "Dificuldade com as respirações sobre passagem", "Dificuldades em recurso de dedilhado", "Dificuldade em fazer nota de apoio", "Não apresentou dificuldades"]
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_pr):
                    if (c1 if i < 13 else c2).checkbox(d, key=f"dk_{i}"): selecionadas.append(d)
                home_m = st.selectbox("Lição de casa - Volume prática:", [str(i) for i in range(1, 41)] + ["Outro"], key="hmp")
                home_a = st.text_input("Lição de casa - Apostila:", key="hap")

            elif mat in ["Teoria", "Solfejo"]:
                st.subheader(f"{'📚' if mat=='Teoria' else '🔊'} Controle de Desempenho - Aula {mat}")
                lic_aula = st.text_input(f"Lição/Volume ({mat}):")
                dif_te = ["Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol", "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo", "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica", "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão", "Dificuldades na ordem das notas", "Não realizou as atividades da apostila", "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"]
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_te):
                    if (c1 if i < 8 else c2).checkbox(d, key=f"dt_{i}_{mat}"): selecionadas.append(d)
                home_m = st.text_input(f"Lição de casa ({mat}):")

            obs = st.text_area("Relato de Evolução:")
            if st.button("💾 SALVAR REGISTRO"):
                for aluna in check_alunas:
                    doc_id = f"AULA_{datetime.now().timestamp()}_{aluna}"
                    db_save("historico", doc_id, {"Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat, "Licao": lic_aula, "Dificuldades": selecionadas, "Obs": obs, "Home_M": home_m, "Home_A": home_a, "Instrutora": instr_sel})
                st.success("Aula salva!")
        else: st.warning("Sem escala para você.")
    else: st.warning("Rodízio pendente.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica")
    if not historico_geral:
        st.info("Aguardando registros.")
    else:
        df_geral = pd.DataFrame(historico_geral)
        todas_alunas = sorted(df_geral["Aluna"].unique())
        aluna_sel = st.selectbox("Selecione a Aluna:", todas_alunas)
        df_f = df_geral[df_geral["Aluna"] == aluna_sel]
        
        if not df_f.empty:
            df_aulas = df_f[df_f["Tipo"] == "Aula"].copy()
            if not df_aulas.empty and 'Dificuldades' in df_aulas.columns:
                df_aulas['Nota'] = df_aulas['Dificuldades'].apply(lambda l: max(0.0, 100.0 - (len(l)*10)) if isinstance(l, list) else 100.0)
                st.bar_chart(df_aulas.groupby('Materia')['Nota'].mean())
            st.dataframe(df_f)
