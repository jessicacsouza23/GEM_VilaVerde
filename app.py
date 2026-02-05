import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
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

# --- FUNÇÃO DE EXPORTAÇÃO PARA IMAGEM (HTML FORMATADO) ---
def baixar_tabela_como_html(df, titulo):
    html = f"""
    <html><head><meta charset='utf-8'><style>
    body {{ font-family: Arial; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #000; padding: 10px; text-align: center; }}
    th {{ background-color: #f2f2f2; }}
    </style></head><body>
    <h2 style='text-align:center;'>{titulo}</h2>
    {df.to_html(index=False)}
    </body></html>
    """
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{titulo}.html" style="background-color:#4CAF50; color:white; padding:10px; border-radius:5px; text-decoration:none;">📸 Gerar Arquivo para Print/JPG</a>'

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_controle, tab_admin = st.tabs([
        "🗓️ Planejar Sábado", "📍 Chamada", "✅ Correção de Atividades", "⚠️ Administração"
    ])

    with tab_gerar:
        st.subheader("🗓️ Planejamento do Rodízio")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # PERSISTÊNCIA DO DIA: Se já existe, mostra o salvo
        if data_str in st.session_state.calendario_anual:
            st.success(f"✅ Rodízio para {data_str} já está definido.")
            df_atual = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.table(df_atual)
            st.markdown(baixar_tabela_como_html(df_atual, f"Rodizio_{data_str.replace('/','-')}"), unsafe_allow_html=True)
            if st.button("🔄 Refazer Rodízio"):
                del st.session_state.calendario_anual[data_str]
                st.rerun()
        else:
            c1, c2 = st.columns(2)
            with c1:
                pt2 = st.selectbox("Teoria H2 (T1):", PROFESSORAS_LISTA, index=0)
                pt3 = st.selectbox("Teoria H3 (T2):", PROFESSORAS_LISTA, index=1)
                pt4 = st.selectbox("Teoria H4 (T3):", PROFESSORAS_LISTA, index=2)
            with c2:
                st2 = st.selectbox("Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3)
                st3 = st.selectbox("Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4)
                st4 = st.selectbox("Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5)
            folgas = st.multiselect("Instrutoras de FOLGA:", PROFESSORAS_LISTA)

            if st.button("🚀 Gerar e Salvar Rodízio"):
                escala_final = []
                fluxo = {
                    HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                    HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                    HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
                }
                offset = (data_sel.day // 7) % 7
                for t_nome, alunas in TURMAS.items():
                    for i, aluna in enumerate(alunas):
                        agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                        for h_idx in [1, 2, 3]:
                            h_label = HORARIOS_LABELS[h_idx]; cfg = fluxo[h_label]
                            if cfg["Teo"] == t_nome: agenda[h_label] = f"📚 S8|Teo({cfg['ITeo']})"
                            elif cfg["Sol"] == t_nome: agenda[h_label] = f"🔊 S9|Sol({cfg['ISol']})"
                            else:
                                p_disp = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]] + folgas]
                                agenda[h_label] = f"🎹 S{(i+offset)%7+1}|Pra({p_disp[i%len(p_disp)] if p_disp else 'Vago'})"
                        escala_final.append(agenda)
                st.session_state.calendario_anual[data_str] = {"tabela": escala_final}
                st.rerun()

    with tab_controle:
        st.subheader("📋 Correção de Atividades (Secretaria)")
        c1, c2 = st.columns(2)
        with c1:
            sec_resp = st.selectbox("Secretária Responsável:", SECRETARIAS)
            alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="alu_c")
        with c2:
            cat_corr = st.selectbox("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila"])
            status_corr = st.selectbox("Status:", ["✅ Sem pendência", "⚠️ Devolvida para refazer", "❌ Não realizada"])
        
        obs_corr = st.text_area("Lições/Observações:")
        if st.button("💾 Salvar Controle Secretaria"):
            st.session_state.controle_licoes.append({
                "Data": data_str, "Secretaria": sec_resp, "Aluna": alu_corr, "Categoria": cat_corr, "Status": status_corr, "Obs": obs_corr
            })
            st.success("Salvo!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    instr_sel = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
    data_hj = datetime.now().strftime("%d/%m/%Y")

    if data_hj in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", options=HORARIOS_LABELS, horizontal=True)
        tabela = st.session_state.calendario_anual[data_hj]["tabela"]
        
        atend = "---"
        for linha in tabela:
            if f"({instr_sel})" in str(linha.values()): atend = linha["Aluna"]

        st.error(f"👤 Atendendo agora: **{atend}**")

        # --- FORMULÁRIO COMPLETO (25 ITENS) ---
        lic_vol = st.selectbox("Lição/Volume (1 a 40):", [str(i) for i in range(1, 41)])
        
        dif_itens = [
            "Não estudou nada", "Estudou insatisfatório", "Não assistiu vídeos", "Dificuldade ritmica",
            "Nomes das figuras", "Adentrando às teclas", "Postura", "Punho alto/baixo",
            "Posição na banqueta", "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
            "Pedal de expressão", "Pé esquerdo", "Metrônomo", "Estuda sem metrônomo",
            "Clave de sol", "Clave de fá", "Atividades apostila", "Articulação",
            "Respirações", "Respiração passagem", "Dedilhado", "Nota de apoio", "Sem dificuldades"
        ]
        
        selecionados = []
        c1, c2 = st.columns(2)
        for i, d in enumerate(dif_itens):
            if (c1 if i < 13 else c2).checkbox(d): selecionados.append(d)
        
        obs_aula = st.text_area("📝 Observações da Aula:")
        if st.button("💾 SALVAR AULA"):
            st.session_state.historico_geral.append({
                "Data": data_hj, "Aluna": atend, "Tipo": "Aula", "Dificuldades": selecionados, "Obs": obs_aula
            })
            st.success("Aula salva!")
    else:
        st.warning("⚠️ Rodízio não gerado hoje.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
else:
    st.header("📊 Analítico IA")
    alu_an = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    
    # Exibe Histórico de Aulas
    df_h = pd.DataFrame(st.session_state.historico_geral)
    if not df_h.empty:
        df_alu = df_h[df_h["Aluna"] == alu_an]
        if not df_alu.empty:
            st.subheader("📋 Aulas")
            st.table(df_alu[["Data", "Obs"]])
            st.markdown(baixar_tabela_como_html(df_alu[["Data", "Obs"]], f"Evolucao_{alu_an}"), unsafe_allow_html=True)

    # Exibe Histórico de Secretaria
    df_c = pd.DataFrame(st.session_state.controle_licoes)
    if not df_c.empty:
        df_sec = df_c[df_c["Aluna"] == alu_an]
        if not df_sec.empty:
            st.subheader("📋 Secretaria")
            st.table(df_sec[["Data", "Secretaria", "Status", "Obs"]])
