import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import base64

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
if "controle_licoes" not in st.session_state: st.session_state.controle_licoes = []

# --- FUNÇÃO PARA EXPORTAR ---
def baixar_tabela_como_html(df, titulo):
    html = f"<html><head><meta charset='utf-8'></head><body><h2 style='font-family: Arial; text-align: center;'>{titulo}</h2>"
    html += df.to_html(index=False, justify='center', border=1)
    html += "</body></html>"
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{titulo}.html" style="text-decoration: none; background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px;">📥 Baixar Relatório</a>'

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_controle = st.tabs(["🗓️ Planejar Sábado", "📍 Chamada", "✅ Controle de Lições"])

    with tab_gerar:
        st.subheader("🗓️ Planejamento de Rodízio")
        data_sel = st.date_input("Escolha a Data:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        c1, c2 = st.columns(2)
        with c1:
            pt2 = st.selectbox("Instrutora Teoria H2:", PROFESSORAS_LISTA, index=0)
            pt3 = st.selectbox("Instrutora Teoria H3:", PROFESSORAS_LISTA, index=1)
            pt4 = st.selectbox("Instrutora Teoria H4:", PROFESSORAS_LISTA, index=2)
        with c2:
            st2 = st.selectbox("Instrutora Solfejo H2:", PROFESSORAS_LISTA, index=3)
            st3 = st.selectbox("Instrutora Solfejo H3:", PROFESSORAS_LISTA, index=4)
            st4 = st.selectbox("Instrutora Solfejo H4:", PROFESSORAS_LISTA, index=5)
        
        if st.button("🚀 Gerar Rodízio", use_container_width=True):
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
                            p_disp = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]]]
                            agenda[h_label] = f"🎹 PRÁTICA ({p_disp[i % len(p_disp)]})"
                    escala_final.append(agenda)
            st.session_state.calendario_anual[data_str] = {"tabela": escala_final}
            st.rerun()

        if data_str in st.session_state.calendario_anual:
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        dt_ch = st.date_input("Data da Chamada:", value=datetime.now(), key="dt_ch_input").strftime("%d/%m/%Y")
        
        alunas_todas = sorted([a for l in TURMAS.values() for a in l])
        
        # Botão para marcar todas como presente
        if st.button("✅ Selecionar Todas como Presente"):
            for aluna in alunas_todas:
                st.session_state[f"ch_{aluna}"] = "Presente"

        chamada_data = []
        for aluna in alunas_todas:
            col_nome, col_status, col_motivo = st.columns([2, 3, 2])
            col_nome.write(f"👤 **{aluna}**")
            
            # Garante que o estado exista
            if f"ch_{aluna}" not in st.session_state:
                st.session_state[f"ch_{aluna}"] = "Presente"
                
            status = col_status.radio(f"Status_{aluna}", ["Presente", "Falta", "Justificada"], 
                                     key=f"ch_{aluna}", horizontal=True, label_visibility="collapsed")
            
            motivo = ""
            if status == "Justificada":
                motivo = col_motivo.text_input("Motivo:", key=f"mot_{aluna}", placeholder="Por que justificou?")
            
            chamada_data.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        st.divider()
        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True):
            for registro in chamada_data:
                st.session_state.historico_geral.append({
                    "Data": dt_ch, 
                    "Aluna": registro["Aluna"], 
                    "Tipo": "Chamada", 
                    "Status": registro["Status"],
                    "Motivo": registro["Motivo"]
                })
            st.success(f"Chamada do dia {dt_ch} salva com sucesso!")

    with tab_controle:
        st.subheader("✅ Controle de Lições")
        alu_s = st.selectbox("Aluna:", alunas_todas)
        r_ok = st.text_input("Lições Realizadas")
        if st.button("Gravar Secretaria"):
            st.session_state.controle_licoes.append({"Data": data_str, "Aluna": alu_s, "Status": r_ok})
            st.success("Salvo!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Registro de Aula")
    instr_sel = st.selectbox("👤 Instrutora:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend = "---"
        for linha in st.session_state.calendario_anual[d_str]["tabela"]:
            if f"({instr_sel})" in str(linha.values()): atend = linha["Aluna"]
        
        st.error(f"👤 Atendimento: **{atend}**")
        lic = st.selectbox("Lição:", [str(i) for i in range(1, 41)] + ["MSA", "Hino"])
        
        dif_itens = ["Não estudou", "Rítmica", "Postura", "Punho", "Falanges", "Unhas", "Dedos", "Metrônomo", "Clave Sol", "Clave Fá", "Articulação", "Respiração"]
        c1, c2 = st.columns(2)
        selecionadas = []
        for i, d in enumerate(dif_itens):
            if (c1 if i < 6 else c2).checkbox(d): selecionadas.append(d)
        
        obs = st.text_area("Observações:")
        if st.button("💾 SALVAR AULA"):
            st.session_state.historico_geral.append({
                "Data": d_str, "Aluna": atend, "Tipo": "Aula", "Licao": lic, 
                "Dificuldades": selecionadas, "Obs": obs, "Instrutora": instr_sel
            })
            st.balloons()
    else: st.warning("Rodízio não encontrado.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência de Dados & Períodos")
    
    st.sidebar.subheader("📅 Período")
    tipo_periodo = st.sidebar.selectbox("Período:", ["Personalizado", "Diário", "Mensal", "Bimestral", "Semestral", "Anual"])
    
    fim = datetime.now()
    if tipo_periodo == "Diário": inicio = fim
    elif tipo_periodo == "Mensal": inicio = fim - timedelta(days=30)
    elif tipo_periodo == "Bimestral": inicio = fim - timedelta(days=60)
    elif tipo_periodo == "Semestral": inicio = fim - timedelta(days=180)
    elif tipo_periodo == "Anual": inicio = fim - timedelta(days=365)
    else:
        inicio = st.sidebar.date_input("De:", value=fim - timedelta(days=30))
        fim = st.sidebar.date_input("Até:", value=fim)

    alu_an = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    df = pd.DataFrame(st.session_state.historico_geral)
    
    if not df.empty:
        df['Dt_Obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        mask = (df['Aluna'] == alu_an) & (df['Dt_Obj'] >= pd.Timestamp(inicio)) & (df['Dt_Obj'] <= pd.Timestamp(fim))
        df_filtrado = df.loc[mask]
        
        df_aulas = df_filtrado[df_filtrado["Tipo"] == "Aula"]
        df_chamada = df_filtrado[df_filtrado["Tipo"] == "Chamada"]

        st.subheader(f"🤖 Análise IA do Período")
        if not df_aulas.empty:
            todas_dif = [d for sub in df_aulas["Dificuldades"].tolist() if isinstance(sub, list) for d in sub]
            if todas_dif:
                mais_comum = pd.Series(todas_dif).value_counts().idxmax()
                st.warning(f"**Alerta:** A aluna repetiu a dificuldade em '{mais_comum}'.")
                st.info(f"**IA recomenda:** Revisar fundamento de {mais_comum} na próxima aula.")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Gráfico de Dificuldades**")
            if not df_aulas.empty and 'todas_dif' in locals() and todas_dif: st.bar_chart(pd.Series(todas_dif).value_counts())
        with c2:
            st.write("**Frequência**")
            if not df_chamada.empty: st.bar_chart(df_chamada["Status"].value_counts())

        st.divider()
        st.subheader("📅 Diário Detalhado")
        for _, row in df_aulas.sort_index(ascending=False).iterrows():
            with st.expander(f"Aula {row['Data']} - Lição: {row.get('Licao', 'S/L')}"):
                st.write(f"**Dificuldades:** {', '.join(row.get('Dificuldades', []))}")
                st.info(f"**Obs:** {row.get('Obs', '')}")
