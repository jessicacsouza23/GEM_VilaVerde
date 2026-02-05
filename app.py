import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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
if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}
if "historico_geral" not in st.session_state:
    st.session_state.historico_geral = []
if "presenca_temp" not in st.session_state:
    st.session_state.presenca_temp = {}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_controle, tab_admin = st.tabs([
        "🗓️ Planejar Sábado", "📍 Chamada", "✅ Controle de Lições", "⚠️ Administração"
    ])

    with tab_gerar:
        st.subheader("🗓️ Planejamento do Rodízio")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("📚 Sala 8 - Teoria")
            pt2 = st.selectbox("Instrutora Teoria H2 (T1):", PROFESSORAS_LISTA, index=0, key=f"pt2_{data_str}")
            pt3 = st.selectbox("Instrutora Teoria H3 (T2):", PROFESSORAS_LISTA, index=1, key=f"pt3_{data_str}")
            pt4 = st.selectbox("Instrutora Teoria H4 (T3):", PROFESSORAS_LISTA, index=2, key=f"pt4_{data_str}")
        with c2:
            st.info("🔊 Sala 9 - Solfejo/MSA")
            st2 = st.selectbox("Instrutora Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3, key=f"st2_{data_str}")
            st3 = st.selectbox("Instrutora Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4, key=f"st3_{data_str}")
            st4 = st.selectbox("Instrutora Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5, key=f"st4_{data_str}")
        
        folgas = st.multiselect("Instrutoras de FOLGA:", PROFESSORAS_LISTA, key=f"fol_{data_str}")

        if st.button("🚀 Gerar e Mostrar Grade", use_container_width=True):
            escala_final = []
            fluxo = {
                HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
            }
            offset_semana = (data_sel.day // 7) % 7
            for t_nome, alunas in TURMAS.items():
                for i, aluna in enumerate(alunas):
                    agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA | Solfejo Coletivo"}
                    for h_idx in [1, 2, 3]:
                        h_label = HORARIOS_LABELS[h_idx]
                        config = fluxo[h_label]
                        if config["Teo"] == t_nome: agenda[h_label] = f"📚 SALA 8 | Teoria ({config['ITeo']})"
                        elif config["Sol"] == t_nome: agenda[h_label] = f"🔊 SALA 9 | Solfejo ({config['ISol']})"
                        else:
                            p_disp = [p for p in PROFESSORAS_LISTA if p not in [config["ITeo"], config["ISol"]] + folgas]
                            sala_p = (i + offset_semana + h_idx) % 7 + 1
                            instr_p = p_disp[i % len(p_disp)] if p_disp else "Vago"
                            agenda[h_label] = f"🎹 SALA {sala_p} | Prática ({instr_p})"
                    escala_final.append(agenda)
            st.session_state.calendario_anual[data_str] = {"tabela": escala_final}

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.subheader(f"📊 Visualização do Rodízio - {data_str}")
            df_view = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.table(df_view)
            st.info("💡 Capture a imagem (Print) da tabela acima para o WhatsApp.")

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        data_ch_str = data_sel.strftime("%d/%m/%Y")
        if st.button("✅ Todas Presentes"):
            for aluna in sorted([a for l in TURMAS.values() for a in l]):
                st.session_state.presenca_temp[aluna] = "Presente"
        
        chamada_temp = []
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            c_a, c_b, c_c = st.columns([2, 2, 2])
            c_a.write(f"👤 **{aluna}**")
            val_padrao = st.session_state.presenca_temp.get(aluna, "Presente")
            status = c_b.radio(f"St_{aluna}", ["Presente", "Falta", "Justificada"], index=["Presente", "Falta", "Justificada"].index(val_padrao), key=f"rad_{aluna}", horizontal=True, label_visibility="collapsed")
            motivo = c_c.text_input("Motivo:", key=f"mot_{aluna}") if status == "Justificada" else ""
            chamada_temp.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        if st.button("💾 SALVAR CHAMADA COMPLETA", type="primary", use_container_width=True):
            for r in chamada_temp:
                st.session_state.historico_geral.append({"Data": data_ch_str, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Obs": r["Motivo"]})
            st.success("Chamada Salva!")

    with tab_controle:
        st.subheader("📋 Controle de Lições (Secretaria)")
        st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="alu_sec")
        st.multiselect("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila"])
        st.text_input("📝 Realizadas - sem pendência")
        st.text_area("Observações Gerais")
        st.button("💾 Salvar Controle")

    with tab_admin:
        if st.button("🔥 RESETAR SISTEMA"):
            st.session_state.clear()
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    data_p = st.date_input("📅 Data da Aula:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")
    instr_sel = st.selectbox("👤 Selecione seu Nome:", PROFESSORAS_LISTA)

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Selecione o Horário:", options=HORARIOS_LABELS, horizontal=True)
        info = st.session_state.calendario_anual[d_str]
        atend, local, mat = "---", "---", "---"

        for linha in info["tabela"]:
            if f"({instr_sel})" in linha.get(h_sel, ""):
                atend, local = linha["Aluna"], linha[h_sel].split(" | ")[0]
                mat = "Teoria" if "SALA 8" in local else "Solfejo" if "SALA 9" in local else "Prática"

        st.divider()
        st.error(f"📍 {local} | Atendendo: **{atend}**")

        # --- IA ANALÍTICO ---
        last_obs = "Nenhum registro anterior."
        for h in reversed(st.session_state.historico_geral):
            if h["Aluna"] == atend and h.get("Tipo") == "Aula":
                last_obs = h["Obs"]
                break
        st.info(f"🤖 **Analítico IA para {atend}:** {last_obs}")

        # --- FORMULÁRIO DE DESEMPENHO (O QUE HAVIA SIDO ESQUECIDO) ---
        if mat == "Prática":
            st.subheader("🎹 Registro de Prática")
            st.selectbox("Lição/Volume (1 a 40):", [str(i) for i in range(1, 41)] + ["Outro"], key="lic_pr")
            
            st.markdown("**Dificuldades (25 itens):**")
            dif_pr = [
                "Não estudou nada", "Estudou insatisfatório", "Não assistiu vídeos",
                "Dificuldade ritmica", "Nomes das figuras", "Adentrando às teclas",
                "Postura", "Punho alto/baixo", "Posição na banqueta", "Quebrando falanges",
                "Unhas compridas", "Dedos arredondados", "Pedal de expressão",
                "Pé esquerdo", "Metrônomo", "Estuda sem metrônomo", "Clave de sol",
                "Clave de fá", "Atividades apostila", "Articulação", "Respirações",
                "Respiração passagem", "Dedilhado", "Nota de apoio", "Sem dificuldades"
            ]
            c_a, c_b = st.columns(2)
            selec_dif = []
            for i, d in enumerate(dif_pr): 
                if (c_a if i < 13 else c_b).checkbox(d, key=f"d_pr_{i}"): selec_dif.append(d)
        
        else:
            st.subheader(f"🎼 Registro de {mat}")
            st.text_input("Lição/Volume:", key="lic_te_so")
            dif_geral = ["Não assistiu vídeos", "Clave de Sol", "Clave de Fá", "Metrônomo", "Leitura Rítmica", "Solfejo", "Movimento da mão", "Sem dificuldades"]
            selec_dif = [d for d in dif_geral if st.checkbox(d, key=f"d_g_{d}")]

        obs_final = st.text_area("📝 Observações da Aula:", key="obs_aula_final")
        if st.button("💾 SALVAR REGISTRO DE AULA", use_container_width=True):
            st.session_state.historico_geral.append({
                "Data": d_str, "Aluna": atend, "Tipo": "Aula", "Materia": mat, "Dificuldades": selec_dif, "Obs": obs_final
            })
            st.success(f"Aula de {atend} salva!")
    else:
        st.warning("⚠️ Rodízio não gerado para hoje.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência de Desempenho")
    alu_an = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Frequência", "95%")
    col_m2.metric("Lições", "14/40")

    st.subheader("📈 Frequência")
    st.bar_chart(pd.DataFrame({"Mês": ["Jan", "Fev"], "Presenças": [4, 3]}))
    
    st.divider()
    st.subheader(f"🖼️ Relatório Visual para Print - {alu_an}")
    df_h = pd.DataFrame(st.session_state.historico_geral)
    if not df_h.empty:
        df_aluna = df_h[df_h["Aluna"] == alu_an][["Data", "Tipo", "Status", "Obs"]]
        st.table(df_aluna)
        st.info("📸 Tire um print desta tabela para enviar aos pais.")
    else:
        st.write("Sem dados.")
