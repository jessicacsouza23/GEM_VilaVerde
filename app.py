import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import urllib.parse

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- DADOS MESTRE (ORDEM FIXA PARA SALAS) ---
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

# --- PERSISTÊNCIA TEMPORÁRIA ---
if "calendario_anual" not in st.session_state: st.session_state.calendario_anual = {}
if "historico_geral" not in st.session_state: st.session_state.historico_geral = []
if "analises_fixas_salvas" not in st.session_state: st.session_state.analises_fixas_salvas = {}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Corrigido v2.0")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada = st.tabs(["🗓️ Planejamento", "📍 Chamada"])

    with tab_gerar:
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano = c2.selectbox("Ano:", [2026, 2027])
        
        sabados = [d for sem in calendar.Calendar().monthdatescalendar(ano, mes) for d in sem if d.weekday() == calendar.SATURDAY and d.month == mes]
        data_sel = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados])

        if data_sel not in st.session_state.calendario_anual:
            st.subheader("Configuração das Salas Coletivas")
            col_t, col_s = st.columns(2)
            with col_t:
                pt2 = st.selectbox("Teoria H2 (T1):", PROFESSORAS_LISTA, index=0, key="pt2")
                pt3 = st.selectbox("Teoria H3 (T2):", PROFESSORAS_LISTA, index=1, key="pt3")
                pt4 = st.selectbox("Teoria H4 (T3):", PROFESSORAS_LISTA, index=2, key="pt4")
            with col_s:
                ps2 = st.selectbox("Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3, key="ps2")
                ps3 = st.selectbox("Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4, key="ps3")
                ps4 = st.selectbox("Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5, key="ps4")
            
            folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA)

            if st.button("🚀 Gerar Rodízio Sem Conflitos"):
                escala_dia = []
                fluxo = {
                    HORARIOS_LABELS[1]: {"Teo": ("Turma 1", pt2), "Sol": ("Turma 2", ps2)},
                    HORARIOS_LABELS[2]: {"Teo": ("Turma 2", pt3), "Sol": ("Turma 3", ps3)},
                    HORARIOS_LABELS[3]: {"Teo": ("Turma 3", pt4), "Sol": ("Turma 1", ps4)}
                }

                for t_nome, alunas in TURMAS.items():
                    for i, aluna in enumerate(alunas):
                        row = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA (Geral)"}
                        
                        for h_idx in [1, 2, 3]:
                            h_label = HORARIOS_LABELS[h_idx]
                            cfg = fluxo[h_label]
                            
                            # Se a turma da aluna está na coletiva
                            if cfg["Teo"][0] == t_nome:
                                row[h_label] = f"📚 SALA 8 | Teoria ({cfg['Teo'][1]})"
                            elif cfg["Sol"][0] == t_nome:
                                row[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['Sol'][1]})"
                            else:
                                # PRÁTICA: Pegar professoras disponíveis
                                p_ocupadas = [cfg["Teo"][1], cfg["Sol"][1]] + folgas
                                p_livres = [p for p in PROFESSORAS_LISTA if p not in p_ocupadas]
                                
                                # Distribuição Circular
                                instr_p = p_livres[i % len(p_livres)]
                                # SALA É SEMPRE A MESMA PARA CADA PROFESSORA (1 a 7)
                                num_sala = (PROFESSORAS_LISTA.index(instr_p) % 7) + 1
                                row[h_label] = f"🎹 SALA {num_sala} | Prática ({instr_p})"
                        
                        escala_dia.append(row)
                
                st.session_state.calendario_anual[data_sel] = escala_dia
                st.rerun()
        else:
            st.success(f"Rodízio Gerado para {data_sel}")
            st.dataframe(pd.DataFrame(st.session_state.calendario_anual[data_sel]), use_container_width=True)
            if st.button("🗑️ Resetar"):
                del st.session_state.calendario_anual[data_sel]
                st.rerun()

elif perfil == "📊 Analítico IA":
    st.header("📊 Análise Pedagógica Completa")
    
    if not st.session_state.historico_geral:
        st.info("Nenhum dado de aula registrado para análise.")
    else:
        df_geral = pd.DataFrame(st.session_state.historico_geral)
        aluna_sel = st.selectbox("Selecione a Aluna:", sorted(df_geral["Aluna"].unique()))
        
        # Sistema de "Congelamento"
        if aluna_sel in st.session_state.analises_fixas_salvas:
            d = st.session_state.analises_fixas_salvas[aluna_sel]
            st.subheader(f"📜 Relatório Consolidado: {aluna_sel}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Desenvoltura", f"{d['media']}%")
            c2.metric("Aulas", d['aulas'])
            c3.metric("Frequência", f"{d['freq']}%")

            st.markdown("---")
            st.markdown(f"**🪑 Postura:** {d['postura']}")
            st.markdown(f"**🎹 Técnica:** {d['tecnica']}")
            st.markdown(f"**🎵 Ritmo/Teoria:** {d['ritmo']}")
            st.info(f"**💡 Dica Próxima Aula:** {d['dica']}")
            st.success(f"**🎯 Meta para Banca:** {d['banca']}")
            
            if st.button("🔄 Gerar Nova Análise"):
                del st.session_state.analises_fixas_salvas[aluna_sel]
                st.rerun()
        else:
            if st.button("✨ Gerar e Congelar Análise"):
                # Simulação de análise pedagógica (aqui entraria sua lógica de processamento)
                st.session_state.analises_fixas_salvas[aluna_sel] = {
                    "media": 85, "aulas": 4, "freq": 100,
                    "postura": "Corrigir altura do punho e falanges quebrando.",
                    "tecnica": "Dedilhados das escalas maiores precisam de atenção.",
                    "ritmo": "Dificuldade em manter o tempo no metrônomo (60bpm).",
                    "dica": "Praticar apenas mão direita separada na lição 15.",
                    "banca": "Focar na articulação ligada e expressão do pedal."
                }
                st.rerun()
