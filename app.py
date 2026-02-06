import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Sistema 2026", layout="wide", page_icon="🎼")

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

# --- INICIALIZAÇÃO DE MEMÓRIA ---
if "calendario_anual" not in st.session_state: st.session_state.calendario_anual = {}
if "historico_geral" not in st.session_state: st.session_state.historico_geral = []

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
    tab_gerar, tab_chamada = st.tabs(["🗓️ Planejamento Mensal", "📍 Chamada"])

    with tab_gerar:
        st.subheader("🗓️ Gestão de Rodízios Mensais")
        c_m1, c_m2 = st.columns(2)
        mes_ref = c_m1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano_ref = c_m2.selectbox("Ano:", [2026, 2027], index=0)
        
        sabados = get_sabados_do_mes(ano_ref, mes_ref)
        for idx_sab, sab in enumerate(sabados):
            d_str = sab.strftime("%d/%m/%Y")
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
                                        agenda[h_label] = f"🎹 SALA {(f_rot % 7) + 1} | Prática ({instr_p})"
                                escala_final.append(agenda)
                        st.session_state.calendario_anual[d_str] = escala_final
                        st.rerun()
                else:
                    st.table(pd.DataFrame(st.session_state.calendario_anual[d_str]))
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        del st.session_state.calendario_anual[d_str]
                        st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe - Vila Verde")
    instr_sel = st.selectbox("👤 Identificação:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend_info = next((l for l in st.session_state.calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)

        if atend_info:
            texto_aula = atend_info[h_sel]
            mat = "Teoria" if "Teoria" in texto_aula else ("Solfejo" if "Solfejo" in texto_aula else "Prática")
            
            if mat in ["Teoria", "Solfejo"]:
                st.info(f"📚 GRUPO | Turma: {atend_info['Turma']} | {texto_aula}")
                check_alunas = [a for a in TURMAS[atend_info['Turma']] if st.checkbox(a, value=True, key=f"p_{a}")]
            else:
                st.error(f"🎹 INDIVIDUAL | Aluna: {atend_info['Aluna']} | {texto_aula}")
                check_alunas = [atend_info['Aluna']]

            st.divider()
            selecionadas = []
            
            # --- FORMULÁRIO DE ACORDO COM A MATÉRIA (ITENS SOLICITADOS) ---
            if mat == "Prática":
                st.subheader("🎹 Controle de Desempenho - Aula Prática")
                col1, col2 = st.columns(2)
                with col1:
                    lic_pr = st.selectbox("Lição/Volume (Prática):", [str(i) for i in range(1, 41)] + ["Outro"], key="lic_pr")
                
                st.markdown("**Dificuldades (Marque todas que se aplicam):**")
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
                c_a, c_b = st.columns(2)
                for i, d in enumerate(dif_pr):
                    if (c_a if i < 13 else c_b).checkbox(d, key=f"d_pr_{i}"): selecionadas.append(d)
                
                st.divider()
                st.markdown("**🏠 Lição de Casa:**")
                home_m = st.selectbox("Lição de casa - Volume prática:", [str(i) for i in range(1, 41)] + ["Outro"], key="home_pr")
                home_a = st.text_input("Lição de casa - Apostila:")

            elif mat == "Teoria":
                st.subheader("📚 Controle de Desempenho - Aula Teoria")
                lic_te = st.text_input("Lição/Volume (Teoria):")
                
                st.markdown("**Dificuldades:**")
                dif_te = [
                    "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
                    "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
                    "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
                    "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
                    "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
                ]
                c_te1, c_te2 = st.columns(2)
                for i, d in enumerate(dif_te):
                    if (c_te1 if i < 8 else c_te2).checkbox(d, key=f"d_te_{i}"): selecionadas.append(d)
                home_m = st.text_input("Lição de casa (Teoria):")
                home_a = ""

            elif mat == "Solfejo":
                st.subheader("🔊 Controle de Desempenho - Aula Solfejo")
                lic_so = st.text_input("Lição/Volume (Solfejo):")
                
                st.markdown("**Dificuldades:**")
                dif_so = [
                    "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
                    "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
                    "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
                    "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
                    "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
                ]
                c_so1, c_so2 = st.columns(2)
                for i, d in enumerate(dif_so):
                    if (c_so1 if i < 8 else c_so2).checkbox(d, key=f"d_so_{i}"): selecionadas.append(d)
                home_m = st.text_input("Lição de casa (Solfejo):")
                home_a = ""

            evolucao = st.text_area("Relato de Evolução Detalhado:")
            
            if st.button("💾 SALVAR REGISTRO", use_container_width=True):
                for aluna in check_alunas:
                    st.session_state.historico_geral.append({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                        "Dificuldades": selecionadas, "Obs": evolucao, 
                        "Home_Metodo": home_m, "Home_Apostila": home_a, "Instrutora": instr_sel
                    })
                st.success("Aula registrada!")
                st.balloons()
        else: st.warning("Sem escala para você.")
    else: st.warning("Rodízio não gerado.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência de Dados")
    df = pd.DataFrame(st.session_state.historico_geral)
    if not df.empty:
        alu_an = st.selectbox("Aluna:", sorted(df["Aluna"].unique()))
        df_f = df[df["Aluna"] == alu_an]
        st.subheader("Alertas Técnicos")
        todas_dif = [d for sub in df_f["Dificuldades"].tolist() for d in sub]
        if todas_dif: st.bar_chart(pd.Series(todas_dif).value_counts())
        st.dataframe(df_f)
    else: st.info("Sem dados.")
