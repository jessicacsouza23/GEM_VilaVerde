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

# --- INICIALIZAÇÃO DE MEMÓRIA (PERSISTÊNCIA) ---
if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}
if "historico_geral" not in st.session_state:
    st.session_state.historico_geral = []
if "controle_licoes" not in st.session_state:
    st.session_state.controle_licoes = []

# --- FUNÇÃO PARA EXPORTAR ---
def baixar_tabela_como_html(df, titulo):
    html = f"<html><head><meta charset='utf-8'></head><body><h2 style='font-family: Arial; text-align: center;'>{titulo}</h2>"
    html += df.to_html(index=False, justify='center', border=1)
    html += "</body></html>"
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{titulo}.html" style="text-decoration: none; background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px;">📥 Baixar Relatório do Período</a>'

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_controle = st.tabs([
        "🗓️ Planejar Sábado", "📍 Chamada", "✅ Controle de Lições"
    ])

    with tab_gerar:
        st.subheader("🗓️ Planejamento e Consulta de Rodízio")
        data_sel = st.date_input("Escolha a Data:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        offset_semana = (data_sel.day // 7) % 7
        c1, c2 = st.columns(2)
        with c1:
            pt2 = st.selectbox("Instrutora Teoria H2 (T1):", PROFESSORAS_LISTA, index=0)
            pt3 = st.selectbox("Instrutora Teoria H3 (T2):", PROFESSORAS_LISTA, index=1)
            pt4 = st.selectbox("Instrutora Teoria H4 (T3):", PROFESSORAS_LISTA, index=2)
        with c2:
            st2 = st.selectbox("Instrutora Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3)
            st3 = st.selectbox("Instrutora Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4)
            st4 = st.selectbox("Instrutora Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5)
        folgas = st.multiselect("Instrutoras de FOLGA:", PROFESSORAS_LISTA)

        if st.button("🚀 Gerar e Salvar Rodízio", use_container_width=True):
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
                            sala_p = (i + offset_semana + h_idx) % 7 + 1
                            instr_p = p_disp[i % len(p_disp)] if p_disp else "Vago"
                            agenda[h_label] = f"🎹 SALA {sala_p} | Prática ({instr_p})"
                    escala_final.append(agenda)
            st.session_state.calendario_anual[data_str] = {"tabela": escala_final}
            st.rerun()

        if data_str in st.session_state.calendario_anual:
            df_rd = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.table(df_rd)
            st.markdown(baixar_tabela_como_html(df_rd, f"Rodizio_{data_str}"), unsafe_allow_html=True)

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        dt_ch = st.date_input("Data da Chamada:", value=datetime.now(), key="dt_ch").strftime("%d/%m/%Y")
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            c_a, c_b = st.columns([2, 4])
            c_a.write(f"👤 **{aluna}**")
            stat = c_b.radio(f"Status", ["Presente", "Falta", "Justificada"], horizontal=True, key=f"ch_{aluna}", label_visibility="collapsed")
            if st.button(f"Salvar Presença {aluna}", key=f"btn_{aluna}"):
                st.session_state.historico_geral.append({"Data": dt_ch, "Aluna": aluna, "Tipo": "Chamada", "Status": stat})
                st.toast(f"Chamada de {aluna} salva!")

    with tab_controle:
        st.subheader("📋 Controle de Lições (Secretaria)")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sec_resp = st.selectbox("Secretária responsável:", SECRETARIAS)
            alu_sec = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="alu_sec")
            cat_sec = st.multiselect("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila"])
        with col_s2:
            r_ok = st.text_input("📝 Realizadas")
            obs_sec = st.text_area("Observações Gerais")
        if st.button("💾 Salvar Controle Secretaria"):
            st.session_state.controle_licoes.append({
                "Data": data_str, "Aluna": alu_sec, "Secretaria": sec_resp, "Status": r_ok, "Obs": obs_sec
            })
            st.success("Dados da secretaria salvos!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Registro de Aula")
    instr_sel = st.selectbox("👤 Sua Identificação:", PROFESSORAS_LISTA)
    data_p = st.date_input("📅 Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", options=HORARIOS_LABELS, horizontal=True)
        atend = "---"
        for linha in st.session_state.calendario_anual[d_str]["tabela"]:
            if f"({instr_sel})" in str(linha.values()): atend = linha["Aluna"]
        
        st.error(f"👤 Atendimento: **{atend}**")
        lic_aula = st.selectbox("Lição/Volume:", [str(i) for i in range(1, 41)] + ["MSA", "Hino"])
        
        st.markdown("**Checklist de Dificuldades Técnicas:**")
        dif_itens = [
            "Não estudou", "Estudou insatisfatório", "Sem vídeos", "Rítmica", "Nomes figuras", 
            "Adentrando teclas", "Postura", "Punho", "Banqueta", "Falanges", "Unhas", 
            "Dedos", "Pedal", "Pé esquerdo", "Metrônomo", "Clave sol", "Clave fá", 
            "Apostila", "Articulação", "Respirações", "Dedilhado", "Nota de apoio", "Sem dificuldades"
        ]
        c1, c2 = st.columns(2)
        selecionadas = []
        for i, d in enumerate(dif_itens):
            if (c1 if i < 12 else c2).checkbox(d, key=f"dif_{i}"): selecionadas.append(d)
        
        obs_aula = st.text_area("📝 Evolução Detalhada:")
        if st.button("💾 SALVAR AULA", use_container_width=True):
            st.session_state.historico_geral.append({
                "Data": d_str, "Aluna": atend, "Tipo": "Aula", "Licao": lic_aula, 
                "Dificuldades": selecionadas, "Obs": obs_aula, "Instrutora": instr_sel
            })
            st.balloons()
    else: st.warning("⚠️ O rodízio precisa ser gerado na Secretaria.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência e Filtros de Período")
    
    # --- FILTRO DE TEMPO ---
    st.sidebar.subheader("📅 Período de Análise")
    tipo_periodo = st.sidebar.selectbox("Escolha o Período:", ["Personalizado", "Diário", "Mensal", "Bimestral", "Semestral", "Anual"])
    
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
    
    df_raw = pd.DataFrame(st.session_state.historico_geral)
    
    if not df_raw.empty:
        # Conversão para filtro
        df_raw['Dt_Obj'] = pd.to_datetime(df_raw['Data'], format='%d/%m/%Y')
        mask = (df_raw['Aluna'] == alu_an) & (df_raw['Dt_Obj'] >= pd.Timestamp(inicio)) & (df_raw['Dt_Obj'] <= pd.Timestamp(fim))
        df_filtrado = df_raw.loc[mask]
        
        df_aulas = df_filtrado[df_filtrado["Tipo"] == "Aula"]
        df_faltas = df_filtrado[df_filtrado["Tipo"] == "Chamada"]

        # --- PARECER IA ---
        st.subheader("🤖 Parecer Técnico da IA")
        if not df_aulas.empty:
            todas_dif = [d for sub in df_aulas["Dificuldades"].tolist() if isinstance(sub, list) for d in sub]
            if todas_dif:
                counts = pd.Series(todas_dif).value_counts()
                mais_comum = counts.idxmax()
                st.warning(f"**Análise Crítica:** No período de {inicio.strftime('%d/%m')} a {fim.strftime('%d/%m')}, a aluna apresentou recorrência em: **{mais_comum}**.")
                st.info(f"**💡 Recomendação:** Focar em métodos de técnica pura para {mais_comum} nas próximas duas semanas.")
            else: st.success("Evolução perfeita no período filtrado!")
        
        # --- GRÁFICOS ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Dificuldades no Período**")
            if not df_aulas.empty and 'todas_dif' in locals() and todas_dif: st.bar_chart(pd.Series(todas_dif).value_counts())
        with c2:
            st.write("**Frequência no Período**")
            if not df_faltas.empty: st.bar_chart(df_faltas["Status"].value_counts())

        # --- DIÁRIO DIÁRIO ---
        st.divider()
        st.subheader("📅 Diário Detalhado (Aulas filtradas)")
        if not df_aulas.empty:
            for _, row in df_aulas.sort_index(ascending=False).iterrows():
                with st.expander(f"Data: {row['Data']} | Lição: {row.get('Licao', 'S/L')}"):
                    st.write(f"**Instrutora:** {row.get('Instrutora', '---')}")
                    st.write(f"**Dificuldades:** {', '.join(row.get('Dificuldades', []))}")
                    st.info(f"**Evolução:** {row.get('Obs', '')}")
            
            st.markdown(baixar_tabela_como_html(df_aulas, f"Relatorio_{alu_an}"), unsafe_allow_html=True)
    else: st.info("Sem dados registrados para este filtro.")
