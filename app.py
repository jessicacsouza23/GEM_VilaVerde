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
if "correcoes_secretaria" not in st.session_state: st.session_state.correcoes_secretaria = []

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
                                        # REGRA SOLICITADA: Sala fixa por instrutora no dia, muda por semana
                                        idx_instr = PROFESSORAS_LISTA.index(instr_p) if instr_p in PROFESSORAS_LISTA else 0
                                        sala_fixa = ((idx_instr + idx_sab) % 7) + 1
                                        agenda[h_label] = f"🎹 SALA {sala_fixa} | Prática ({instr_p})"
                                escala_final.append(agenda)
                        st.session_state.calendario_anual[d_str] = escala_final
                        st.rerun()
                else:
                    st.table(pd.DataFrame(st.session_state.calendario_anual[d_str]))
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        del st.session_state.calendario_anual[d_str]
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
            motivo = ""
            if status == "Justificada":
                motivo = col3.text_input(f"Motivo justificativa", key=f"motivo_{aluna}_{data_ch_sel}", placeholder="Informe o motivo...", label_visibility="collapsed")
            registros_chamada.append({"Aluna": aluna, "Status": status, "Motivo": motivo})
        st.divider()
        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            for reg in registros_chamada:
                st.session_state.historico_geral.append({"Data": data_ch_sel, "Aluna": reg["Aluna"], "Tipo": "Chamada", "Status": reg["Status"], "Motivo": reg["Motivo"]})
            st.success(f"Chamada do dia {data_ch_sel} salva com sucesso!")

    with tab_correcao:
        st.subheader("✅ Correção de Atividades")
        sec_resp = st.selectbox("Secretária Responsável:", SECRETARIAS)
        alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
        liçao_info = "Nenhuma lição encontrada"
        if st.session_state.historico_geral:
            df_h = pd.DataFrame(st.session_state.historico_geral)
            df_alu = df_h[(df_h["Aluna"] == alu_corr) & (df_h["Tipo"] == "Aula")]
            if not df_alu.empty:
                ult = df_alu.iloc[-1]
                liçao_info = f"Matéria: {ult['Materia']} | Lição: {ult['Home_M']} | Apostila: {ult['Home_A']}"
        st.info(f"📋 **Lição registrada pela Professora:** {liçao_info}")
        status_corr = st.radio("Status:", ["Realizada", "Não Realizada", "Devolvida para Correção"], horizontal=True)
        obs_sec = st.text_area("Notas da Secretaria:")
        if st.button("💾 Salvar Registro de Correção"):
            st.session_state.correcoes_secretaria.append({"Data": datetime.now().strftime("%d/%m/%Y"), "Aluna": alu_corr, "Secretaria": sec_resp, "Atividade": liçao_info, "Status": status_corr, "Obs": obs_sec})
            st.success("Corrigido!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Identificação:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend = next((l for l in st.session_state.calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            # INFORMATIVO DE ATENDIMENTO
            sala_info = atend[h_sel].split("|")[0] if "|" in atend[h_sel] else "Igreja"
            quem_info = atend['Aluna'] if "Prática" in atend[h_sel] else atend['Turma']
            st.warning(f"📍 **ATENDIMENTO ATUAL:** {quem_info} | **LOCAL:** {sala_info}")
            st.divider()

            # FORMULÁRIO (RESTITUÍDO CONFORME O ORIGINAL)
            texto_aula = atend[h_sel]
            mat = "Teoria" if "Teoria" in texto_aula else ("Solfejo" if "Solfejo" in texto_aula else "Prática")
            check_alunas = [atend['Aluna']] if mat == "Prática" else [a for a in TURMAS[atend['Turma']] if st.checkbox(a, value=True, key=f"p_{a}")]
            
            selecionadas = []
            home_m, home_a, lic_aula = "", "", ""

            if mat == "Prática":
                st.subheader("🎹 Controle de Desempenho - Aula Prática")
                lic_aula = st.selectbox("Lição/Volume (Prática):", [str(i) for i in range(1, 41)] + ["Outro"], key="lic_pr")
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
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_pr):
                    if (c1 if i < 13 else c2).checkbox(d, key=f"dk_{i}"): selecionadas.append(d)
                st.divider()
                home_m = st.selectbox("Lição de casa - Volume prática:", [str(i) for i in range(1, 41)] + ["Outro"], key="hmp")
                home_a = st.text_input("Lição de casa - Apostila:", key="hap")

            elif mat == "Teoria":
                st.subheader("📚 Controle de Desempenho - Aula Teoria")
                lic_aula = st.text_input("Lição/Volume (Teoria):")
                dif_te = [
                    "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
                    "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
                    "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
                    "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
                    "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
                ]
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_te):
                    if (c1 if i < 8 else c2).checkbox(d, key=f"dt_{i}"): selecionadas.append(d)
                home_m = st.text_input("Lição de casa (Teoria):")

            elif mat == "Solfejo":
                st.subheader("🔊 Controle de Desempenho - Aula Solfejo")
                lic_aula = st.text_input("Lição/Volume (Solfejo):")
                dif_so = [
                    "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
                    "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
                    "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
                    "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
                    "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
                ]
                c1, c2 = st.columns(2)
                for i, d in enumerate(dif_so):
                    if (c1 if i < 8 else c2).checkbox(d, key=f"ds_{i}"): selecionadas.append(d)
                home_m = st.text_input("Lição de casa (Solfejo):")

            obs = st.text_area("Relato de Evolução:")
            if st.button("💾 SALVAR REGISTRO"):
                for aluna in check_alunas:
                    st.session_state.historico_geral.append({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                        "Licao": lic_aula, "Dificuldades": selecionadas, "Obs": obs, 
                        "Home_M": home_m, "Home_A": home_a, "Instrutora": instr_sel
                    })
                st.success("Aula salva!")
                st.balloons()
        else: st.warning("Sem escala para você.")
    else: st.warning("Rodízio pendente.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise de Evolução Pedagógica")

    if not st.session_state.historico_geral:
        st.info("Aguardando dados para análise. Realize chamadas e registros de aula primeiro.")
    else:
        # 1. Filtros de Seleção
        df_geral = pd.DataFrame(st.session_state.historico_geral)
        todas_alunas = sorted(df_geral["Aluna"].unique())
        
        c1, c2, c3 = st.columns([2, 2, 2])
        aluna_sel = c1.selectbox("Selecione a Aluna:", todas_alunas)
        periodo_tipo = c2.selectbox("Período do Relatório:", ["Diário", "Mensal", "Bimestral", "Semestral", "Anual"])
        data_ref = c3.date_input("Data de Referência (Fim do Período):")

        # Lógica de Filtro de Datas
        df_geral['dt_obj'] = pd.to_datetime(df_geral['Data'], format='%d/%m/%Y').dt.date
        d_fim = data_ref
        delta = {"Diário":0, "Mensal":30, "Bimestral":60, "Semestral":180, "Anual":365}[periodo_tipo]
        d_ini = d_fim - timedelta(days=delta)
        
        # DataFrame filtrado para a aluna e período
        df_f = df_geral[(df_geral["Aluna"] == aluna_sel) & (df_geral["dt_obj"] >= d_ini) & (df_geral["dt_obj"] <= d_fim)]

        if df_f.empty:
            st.warning(f"Nenhum registro encontrado para {aluna_sel} entre {d_ini.strftime('%d/%m/%Y')} e {d_fim.strftime('%d/%m/%Y')}.")
        else:
            # --- GRÁFICO DE DESENVOLTURA (Como a aluna se saiu) ---
            st.subheader("📈 Nível de Desenvoltura por Disciplina")
            df_aulas = df_f[df_f["Tipo"] == "Aula"].copy()
            
            if not df_aulas.empty:
                # Cálculo de Desenvoltura: Começa em 100%, perde 10% por dificuldade marcada
                def calcular_nota(lista_difs):
                    if not isinstance(lista_difs, list) or not lista_difs: return 100.0
                    if "Não apresentou dificuldades" in lista_difs: return 100.0
                    nota = 100.0 - (len(lista_difs) * 10.0)
                    return max(0.0, nota)

                df_aulas['Nota_Desenv'] = df_aulas['Dificuldades'].apply(calcular_nota)
                grafico_data = df_aulas.groupby('Materia')['Nota_Desenv'].mean()
                
                # Exibição do Gráfico de Barras
                st.bar_chart(grafico_data)
                st.caption("A pontuação baseia-se na ausência de dificuldades técnicas registradas (100% = Excelente).")
            else:
                st.info("Sem registros de aula para gerar o gráfico de desenvoltura.")

            # --- BOTÃO PARA GERAR O RELATÓRIO COMPLETO NA TELA ---
            if st.button("✨ GERAR RELATÓRIO PEDAGÓGICO E NOTIFICAR"):
                # Cálculo de Frequência
                df_ch = df_f[df_f["Tipo"] == "Chamada"]
                total_dias = len(df_ch)
                presencas = len(df_ch[df_ch["Status"] == "Presente"])
                porcentagem_freq = (presencas / total_dias * 100) if total_dias > 0 else 0

                st.divider()
                # ESTRUTURA DO RELATÓRIO (APARECE NA TELA)
                st.markdown(f"# 📜 RELATÓRIO PEDAGÓGICO - {aluna_sel.upper()}")
                st.write(f"**Período Selecionado:** {periodo_tipo} ({d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')})")
                
                # Métricas Rápidas
                m1, m2, m3 = st.columns(3)
                m1.metric("Frequência", f"{porcentagem_freq:.1f}%")
                m2.metric("Aulas Realizadas", len(df_aulas))
                m3.metric("Média de Desenvoltura", f"{df_aulas['Nota_Desenv'].mean():.0f}%" if not df_aulas.empty else "0%")

                # Conteúdo Pedagógico (Baseado nas suas seções)
                st.subheader("📗 Análise de Desempenho Técnica")
                if not df_aulas.empty:
                    for mat in ["Prática", "Teoria", "Solfejo"]:
                        aulas_mat = df_aulas[df_aulas["Materia"] == mat]
                        if not aulas_mat.empty:
                            with st.expander(f"Evolução em {mat}"):
                                for _, r in aulas_mat.iterrows():
                                    st.write(f"**Data {r['Data']}:** Lição {r['Licao']}")
                                    st.write(f"**Dificuldades:** {', '.join(r['Dificuldades'])}")
                                    st.write(f"**Obs:** {r['Obs']}")
                
                st.subheader("📋 Resumo da Secretaria")
                df_sec = pd.DataFrame(st.session_state.correcoes_secretaria)
                if not df_sec.empty:
                    df_sec_f = df_sec[df_sec["Aluna"] == aluna_sel]
                    st.table(df_sec_f[["Data", "Atividade", "Status"]])

                # AVISO FINAL
                st.success("✅ Análise gerada com sucesso e salva no banco de dados!")
                st.info("🔔 **AVISO:** A análise da aluna está pronta. Favor comunicar a instrutora da próxima semana.")

            # Histórico Geral
            with st.expander("📂 Ver histórico bruto de dados"):
                st.dataframe(df_f)
