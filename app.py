import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import urllib.parse

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
if "analises_fixas_salvas" not in st.session_state: st.session_state.analises_fixas_salvas = {}

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
                        pt2 = st.selectbox(f"Teoria H2 (Turma 1) - {d_str}:", PROFESSORAS_LISTA, index=0, key=f"pt2_{d_str}")
                        pt3 = st.selectbox(f"Teoria H3 (Turma 2) - {d_str}:", PROFESSORAS_LISTA, index=1, key=f"pt3_{d_str}")
                        pt4 = st.selectbox(f"Teoria H4 (Turma 3) - {d_str}:", PROFESSORAS_LISTA, index=2, key=f"pt4_{d_str}")
                    with c2:
                        st2 = st.selectbox(f"Solfejo H2 (Turma 2) - {d_str}:", PROFESSORAS_LISTA, index=3, key=f"st2_{d_str}")
                        st3 = st.selectbox(f"Solfejo H3 (Turma 3) - {d_str}:", PROFESSORAS_LISTA, index=4, key=f"st3_{d_str}")
                        st4 = st.selectbox(f"Solfejo H4 (Turma 1) - {d_str}:", PROFESSORAS_LISTA, index=5, key=f"st4_{d_str}")
                    
                    folgas = st.multiselect(f"Folgas ({d_str}):", PROFESSORAS_LISTA, key=f"f_{d_str}")

                    if st.button(f"🚀 Gerar Rodízio para {d_str}", key=f"btn_{d_str}"):
                        escala_final = []
                        # ORDEM RÍGIDA CONFORME INFORMADO
                        fluxo = {
                            HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                            HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                            HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
                        }
                        
                        for t_nome, alunas in TURMAS.items():
                            for i, aluna in enumerate(alunas):
                                agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA - Solfejo Melódico"}
                                for h_idx in [1, 2, 3]:
                                    h_label = HORARIOS_LABELS[h_idx]
                                    cfg = fluxo[h_label]
                                    
                                    if cfg["Teo"] == t_nome:
                                        agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['ITeo']})"
                                    elif cfg["Sol"] == t_nome:
                                        agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['ISol']})"
                                    else:
                                        # PRÁTICA: Pega professoras que não estão na teoria/solfejo nem folga
                                        p_ocupadas = [cfg["ITeo"], cfg["ISol"]] + folgas
                                        p_disp = [p for p in PROFESSORAS_LISTA if p not in p_ocupadas]
                                        
                                        instr_p = p_disp[i % len(p_disp)] if p_disp else "Vago"
                                        # SALA FIXA POR INSTRUTORA (1 a 7)
                                        idx_global = PROFESSORAS_LISTA.index(instr_p) if instr_p in PROFESSORAS_LISTA else 0
                                        sala_fixa = (idx_global % 7) + 1
                                        agenda[h_label] = f"🎹 SALA {sala_fixa} | Prática ({instr_p})"
                                
                                escala_final.append(agenda)
                        st.session_state.calendario_anual[d_str] = escala_final
                        st.rerun()
                else:
                    st.dataframe(pd.DataFrame(st.session_state.calendario_anual[d_str]), use_container_width=True)
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
            motivo = col3.text_input(f"Motivo", key=f"motivo_{aluna}_{data_ch_sel}", placeholder="Justificativa...", label_visibility="collapsed") if status == "Justificada" else ""
            registros_chamada.append({"Aluna": aluna, "Status": status, "Motivo": motivo})
        
        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            for reg in registros_chamada:
                st.session_state.historico_geral.append({"Data": data_ch_sel, "Aluna": reg["Aluna"], "Tipo": "Chamada", "Status": reg["Status"], "Motivo": reg["Motivo"]})
            st.success("Chamada Salva!")

    with tab_correcao:
        st.subheader("✅ Correção de Atividades")
        sec_resp = st.selectbox("Secretária Responsável:", SECRETARIAS)
        alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="alu_corr_sec")
        liçao_info = "Nenhuma lição encontrada"
        if st.session_state.historico_geral:
            df_h = pd.DataFrame(st.session_state.historico_geral)
            df_alu = df_h[(df_h["Aluna"] == alu_corr) & (df_h["Tipo"] == "Aula")]
            if not df_alu.empty:
                ult = df_alu.iloc[-1]
                liçao_info = f"Matéria: {ult['Materia']} | Lição: {ult['Home_M']} | Apostila: {ult['Home_A']}"
        st.info(f"📋 **Lição da Professora:** {liçao_info}")
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
            sala_info = atend[h_sel].split("|")[0] if "|" in atend[h_sel] else "Igreja"
            quem_info = atend['Aluna'] if "Prática" in atend[h_sel] else f"TURMA: {atend['Turma']}"
            st.warning(f"📍 **ATENDIMENTO:** {quem_info} | **LOCAL:** {sala_info}")
            
            mat = "Teoria" if "Teoria" in atend[h_sel] else ("Solfejo" if "Solfejo" in atend[h_sel] else "Prática")
            check_alunas = [atend['Aluna']] if mat == "Prática" else TURMAS[atend['Turma']]
            
            if mat != "Prática":
                st.write("Confirmar alunas presentes na sala coletiva:")
                check_alunas = [a for a in TURMAS[atend['Turma']] if st.checkbox(a, value=True, key=f"p_{a}_{h_sel}")]

            selecionadas = []
            home_m, home_a, lic_aula = "", "", ""

            if mat == "Prática":
                lic_aula = st.selectbox("Lição Atual (Prática):", [str(i) for i in range(1, 41)] + ["Outro"])
                dif_list = ["Dificuldade ritmica", "Postura (costas/ombros)", "Punho alto/baixo", "Quebrando falanges", "Dedo arredondado", "Uso do Metrônomo", "Clave de Fá", "Clave de Sol", "Não estudou", "Não apresentou dificuldades"]
            else:
                lic_aula = st.text_input(f"Lição/Página ({mat}):")
                dif_list = ["Leitura Rítmica", "Leitura Métrica", "Solfejo (Afinação)", "Movimento da mão", "Metrônomo", "Atividades Apostila", "Não apresentou dificuldades"]

            c1, c2 = st.columns(2)
            for i, d in enumerate(dif_list):
                if (c1 if i < len(dif_list)/2 else c2).checkbox(d, key=f"dif_{i}"): selecionadas.append(d)

            home_m = st.text_input("Lição de casa (Método/Volume):")
            home_a = st.text_input("Lição de casa (Apostila):")
            obs = st.text_area("Relato de Evolução:")

            if st.button("💾 SALVAR REGISTRO"):
                for aluna in check_alunas:
                    st.session_state.historico_geral.append({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Materia": mat,
                        "Licao": lic_aula, "Dificuldades": selecionadas, "Obs": obs, 
                        "Home_M": home_m, "Home_A": home_a, "Instrutora": instr_sel
                    })
                st.success("Aula registrada!")
                st.balloons()
        else: st.info("Você não tem aula escalada neste horário.")
    else: st.error("Rodízio não gerado para hoje.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica")

    if not st.session_state.historico_geral:
        st.info("Aguardando dados para análise.")
    else:
        df_geral = pd.DataFrame(st.session_state.historico_geral)
        aluna_sel = st.selectbox("Selecione a Aluna:", sorted(df_geral["Aluna"].unique()))
        periodo_tipo = st.selectbox("Período:", ["Mensal", "Semestral", "Banca Semestral"])
        
        id_analise = f"{aluna_sel}_{periodo_tipo}"

        if id_analise in st.session_state.analises_fixas_salvas:
            d = st.session_state.analises_fixas_salvas[id_analise]
            st.subheader(f"📜 Relatório {periodo_tipo} - {aluna_sel}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Aulas Realizadas", d['qtd_aulas'])
            c2.metric("Aproveitamento", f"{d['media']:.0f}%")
            c3.metric("Status Secretaria", d['status_sec'])

            st.markdown("---")
            st.error(f"### 🪑 Postura\n{d['difs_postura']}")
            st.warning(f"### 🎹 Técnica\n{d['difs_tecnica']}")
            st.info(f"### 🎵 Ritmo e Teoria\n{d['difs_ritmo']}")
            st.success(f"### 🎯 Meta Próxima Aula\n{d['dicas']}")
            
            if "Banca" in periodo_tipo:
                st.markdown(f"**⚠️ FOCO PARA BANCA:** {d['banca']}")

            if st.button("🗑️ Gerar Nova Análise (Descongelar)"):
                del st.session_state.analises_fixas_salvas[id_analise]
                st.rerun()
        else:
            if st.button("✨ GERAR ANÁLISE COMPLETA E CONGELAR"):
                df_alu = df_geral[df_geral["Aluna"] == aluna_sel]
                df_aulas = df_alu[df_alu["Tipo"] == "Aula"]
                
                # Lógica de separação por áreas
                difs_totais = [d for l in df_aulas['Dificuldades'] for d in l] if not df_aulas.empty else []
                
                postura = [d for d in difs_totais if any(w in d.lower() for w in ["postura", "punho", "banqueta", "costas"])]
                tecnica = [d for d in difs_totais if any(w in d.lower() for w in ["dedo", "falange", "articulação", "pedal", "tecla"])]
                ritmo = [d for d in difs_totais if any(w in d.lower() for w in ["metrônomo", "ritmica", "métrica", "solfejo", "teoria"])]
                
                df_sec = pd.DataFrame(st.session_state.correcoes_secretaria)
                st_sec = df_sec[df_sec["Aluna"] == aluna_sel]["Status"].iloc[-1] if not df_sec.empty else "Sem Pendências"

                st.session_state.analises_fixas_salvas[id_analise] = {
                    "qtd_aulas": len(df_aulas),
                    "media": max(0, 100 - (len(difs_totais) * 5)),
                    "status_sec": st_sec,
                    "difs_postura": ", ".join(set(postura)) if postura else "Excelente postura.",
                    "difs_tecnica": ", ".join(set(tecnica)) if tecnica else "Técnica em evolução estável.",
                    "difs_ritmo": ", ".join(set(ritmo)) if ritmo else "Ritmo e teoria em dia.",
                    "dicas": "Trabalhar independência de mãos e maior precisão no metrônomo.",
                    "banca": "Focar na respiração correta e relaxamento dos ombros durante a execução."
                }
                st.rerun()

    with st.expander("📂 Log de Registros"):
        st.write(st.session_state.historico_geral)
