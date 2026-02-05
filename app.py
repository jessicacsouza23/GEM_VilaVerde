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

# --- INICIALIZAÇÃO DE MEMÓRIA (PERSISTÊNCIA) ---
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
        st.subheader("🗓️ Planejamento e Consulta de Rodízio")
        data_sel = st.date_input("Escolha a Data (Para gerar ou consultar):", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # Verifica se já existe rodízio para essa data
        ja_existe = data_str in st.session_state.calendario_anual

        if ja_existe:
            st.success(f"✅ Rodízio encontrado para o dia {data_str}")
        else:
            st.warning(f"⚠️ Não há rodízio salvo para {data_str}. Configure abaixo para gerar.")

        offset_semana = (data_sel.day // 7) % 7

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

        btn_label = "🔄 Atualizar/Gerar Rodízio" if ja_existe else "🚀 Gerar Novo Rodízio"
        if st.button(btn_label, use_container_width=True):
            escala_final = []
            fluxo = {
                HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
            }
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

        if ja_existe:
            st.divider()
            st.subheader(f"📊 Escala Salva - {data_str}")
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        data_ch = st.date_input("Data da Chamada:", value=datetime.now(), key="dt_ch")
        data_ch_str = data_ch.strftime("%d/%m/%Y")
        
        if st.button("✅ Selecionar Todas como Presentes"):
            for aluna in sorted([a for l in TURMAS.values() for a in l]):
                st.session_state.presenca_temp[aluna] = "Presente"
        
        st.divider()
        chamada_lista = []
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            c_a, c_b, c_c = st.columns([2, 2, 2])
            c_a.write(f"👤 **{aluna}**")
            val_padrao = st.session_state.presenca_temp.get(aluna, "Presente")
            idx_padrao = ["Presente", "Falta", "Justificada"].index(val_padrao)
            
            status = c_b.radio(f"Status_{aluna}", ["Presente", "Falta", "Justificada"], 
                               index=idx_padrao, key=f"rad_{aluna}", horizontal=True, label_visibility="collapsed")
            
            motivo = ""
            if status == "Justificada":
                motivo = c_c.text_input("Motivo:", key=f"mot_{aluna}")
            
            chamada_lista.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True, type="primary"):
            for registro in chamada_lista:
                st.session_state.historico_geral.append({
                    "Data": data_ch_str, "Aluna": registro["Aluna"], "Tipo": "Chamada", "Status": registro["Status"], "Motivo": registro["Motivo"]
                })
            st.success("Chamada Salva!")

    with tab_controle:
        st.subheader("📋 Controle de Lições (Secretaria)")
        st.selectbox("Secretária responsável:", SECRETARIAS)
        st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="alu_sec")
        st.multiselect("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"])
        st.text_input("📝 Realizadas - sem pendência")
        st.text_input("⚠️ Realizada - devolvida para refazer")
        st.text_input("❌ Não realizada")
        st.text_area("Observações Gerais")
        st.button("💾 Salvar Controle de Lições")

    with tab_admin:
        if st.button("🔥 RESETAR SISTEMA"):
            st.session_state.clear()
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        data_p = st.date_input("📅 Data da Aula:", value=datetime.now(), key="dt_prof_main")
        d_str = data_p.strftime("%d/%m/%Y")
    
    with col_p2:
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
        if "SALA 8" in local: st.warning(f"📚 {local} | 👤 Atendimento: **{atend}**")
        elif "SALA 9" in local: st.success(f"🔊 {local} | 👤 Atendimento: **{atend}**")
        elif "Igreja" in local: st.info(f"⛪ {local} | 👤 Atendimento: **{atend}**")
        else: st.error(f"🎹 {local} | 👤 Atendimento: **{atend}**")

        last_obs = "Nenhum registro anterior encontrado."
        for h in reversed(st.session_state.historico_geral):
            if h["Aluna"] == atend and h.get("Tipo") == "Aula":
                last_obs = h["Obs"]
                break
        st.info(f"🤖 **Analítico IA para {atend}:** {last_obs}")

        st.divider()

        if mat == "Prática":
            st.subheader("🎹 Controle de Desempenho - Aula Prática")
            st.selectbox("Lição/Volume (Prática):", [str(i) for i in range(1, 41)] + ["Outro"], key="lic_pr")
            
            st.markdown("**Dificuldades:**")
            dif_pr = [
                "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos dos métodos",
                "Dificuldade ritmica", "Dificuldade em distinguir os nomes das figuras ritmicas",
                "Está adentrando às teclas", "Dificuldade com a postura", "Está deixando o punho alto ou baixo",
                "Não senta no centro da banqueta", "Está quebrando as falanges", "Unhas muito compridas",
                "Dificuldade em deixar os dedos arredondados", "Esquece o pé no pedal de expressão",
                "Movimentos desnecessários com o pé esquerdo", "Dificuldade com metrônomo", "Estuda sem metrônomo",
                "Dificuldades clave de sol", "Dificuldades clave de fá", "Não realizou atividades apostila",
                "Dificuldade articulação", "Dificuldade respirações", "Dificuldade respirações passagem",
                "Dificuldades recurso de dedilhado", "Dificuldade nota de apoio", "Não apresentou dificuldades"
            ]
            c_a, c_b = st.columns(2)
            selecionadas = []
            for i, d in enumerate(dif_pr): 
                if (c_a if i < 13 else c_b).checkbox(d, key=f"d_pr_{i}"): selecionadas.append(d)
            
            st.divider()
            st.selectbox("Lição de casa - Volume prática:", [str(i) for i in range(1, 41)] + ["Outro"], key="home_v")
            st.text_input("Lição de casa - Apostila:", key="home_ap")

        elif mat == "Teoria" or "Solfejo" in mat:
            st.subheader(f"🎼 Controle de Desempenho - {mat}")
            st.text_input("Lição/Volume:", key="lic_te_so")
            st.markdown("**Dificuldades:**")
            dif_geral = [
                "Não assistiu vídeos complementares", "Dificuldades clave de sol", "Dificuldades clave de fá",
                "Dificuldade metrônomo", "Estuda sem metrônomo", "Não realizou as atividades",
                "Dificuldade leitura ritmica", "Dificuldades leitura métrica", "Dificuldade solfejo (afinação)",
                "Dificuldades movimento da mão", "Dificuldades ordem das notas", "Não realizou atividades apostila",
                "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
            ]
            c_t1, c_t2 = st.columns(2)
            selecionadas = []
            for i, d in enumerate(dif_geral):
                if (c_t1 if i < 8 else c_t2).checkbox(d, key=f"d_te_{i}"): selecionadas.append(d)
            st.text_input("Lição de casa:", key="home_te_so")

        obs_final = st.text_area("📝 Observações da Aula:", key="obs_aula_final")
        if st.button("💾 SALVAR REGISTRO DE AULA", use_container_width=True):
            st.session_state.historico_geral.append({
                "Data": d_str, "Aluna": atend, "Tipo": "Aula", "Materia": mat, "Dificuldades": selecionadas, "Obs": obs_final
            })
            st.balloons()
            st.success(f"Aula de {atend} salva!")
    else:
        st.error("⚠️ Não há rodízio gerado para esta data. Peça para a Secretaria gerar.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência de Desempenho 2026")
    alu_an = st.selectbox("Selecione a Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    per_an = st.select_slider("Período da Análise:", ["Mensal", "Bimestral", "Semestral", "Anual"])
    
    st.divider()
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Frequência Geral", "92%", "+5%")
    col_m2.metric("Lições Concluídas", "14", "+2")
    col_m3.metric("Nível de Dificuldade", "Baixo", "-10%")

    st.subheader(f"📈 Gráfico de Frequência - {per_an}")
    chart_data = pd.DataFrame({
        "Mês": ["Jan", "Fev", "Mar", "Abr"],
        "Presenças": [4, 3, 4, 4],
        "Faltas": [0, 1, 0, 0],
        "Justificadas": [0, 0, 1, 0]
    })
    st.bar_chart(chart_data, x="Mês", y=["Presenças", "Faltas", "Justificadas"], color=["#2ecc71", "#e74c3c", "#f1c40f"])
    
    st.divider()
    st.subheader("🤖 Recomendação da IA")
    st.success(f"**Análise Inteligente:** Evolução constante. Focar na técnica de respiração.")

    st.subheader("📋 Histórico Geral (Aulas e Chamadas)")
    if st.session_state.historico_geral:
        df_hist = pd.DataFrame(st.session_state.historico_geral)
        st.dataframe(df_hist[df_hist["Aluna"] == alu_an], use_container_width=True)
    else:
        st.write("Nenhum dado registrado.")
