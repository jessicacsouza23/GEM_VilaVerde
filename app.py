import streamlit as st
import pandas as pd
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

# --- FUNÇÃO PARA PRINT (ESTILO JPG) ---
def link_para_print(df, titulo):
    html = f"""
    <html><head><meta charset='utf-8'><style>
    body {{ font-family: Arial; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border: 1px solid #333; padding: 10px; text-align: center; }}
    th {{ background-color: #1b5e20; color: white; }}
    </style></head><body>
    <h2 style='text-align:center;'>{titulo}</h2>
    {df.to_html(index=False)}
    <p style='text-align:center; font-size:10px;'>GEM Vila Verde - Registro 2026</p>
    </body></html>
    """
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{titulo}.html" style="background-color:#2e7d32; color:white; padding:10px; border-radius:5px; text-decoration:none; font-weight:bold; display:inline-block; margin-top:10px;">📸 GERAR IMAGEM PARA PRINT</a>'

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    t1, t2, t3 = st.tabs(["🗓️ Rodízio", "✅ Correção de Lições", "⚠️ Administração"])

    with t1:
        st.subheader("🗓️ Planejamento de Sábado")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        if data_str in st.session_state.calendario_anual:
            st.success(f"✅ Rodízio pronto para {data_str}")
            df_view = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.table(df_view)
            st.markdown(link_para_print(df_view, f"Rodizio_{data_str.replace('/','-')}"), unsafe_allow_html=True)
            if st.button("🔄 Refazer Rodízio"):
                del st.session_state.calendario_anual[data_str]
                st.rerun()
        else:
            c1, c2 = st.columns(2)
            with c1:
                pt2, pt3, pt4 = st.selectbox("Teoria H2", PROFESSORAS_LISTA, index=0), st.selectbox("Teoria H3", PROFESSORAS_LISTA, index=1), st.selectbox("Teoria H4", PROFESSORAS_LISTA, index=2)
            with c2:
                st2, st3, st4 = st.selectbox("Solfejo H2", PROFESSORAS_LISTA, index=3), st.selectbox("Solfejo H3", PROFESSORAS_LISTA, index=4), st.selectbox("Solfejo H4", PROFESSORAS_LISTA, index=5)
            folgas = st.multiselect("Instrutoras de Folga:", PROFESSORAS_LISTA)

            if st.button("🚀 Gerar e Salvar Rodízio"):
                escala = []
                fluxo = {
                    HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                    HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                    HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
                }
                offset = (data_sel.day // 7) % 7
                for t_nome, alunas in TURMAS.items():
                    for i, aluna in enumerate(alunas):
                        ag = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                        for h_idx in [1, 2, 3]:
                            h_lab = HORARIOS_LABELS[h_idx]; cfg = fluxo[h_lab]
                            if cfg["Teo"] == t_nome: ag[h_lab] = f"📚 S8|Teo({cfg['ITeo']})"
                            elif cfg["Sol"] == t_nome: ag[h_lab] = f"🔊 S9|Sol({cfg['ISol']})"
                            else:
                                p_disp = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]] + folgas]
                                ag[h_lab] = f"🎹 S{(i+offset)%7+1}|Pra({p_disp[i%len(p_disp)] if p_disp else 'Vago'})"
                        escala.append(ag)
                st.session_state.calendario_anual[data_str] = {"tabela": escala}
                st.rerun()

    with t2:
        st.subheader("✅ Correção de Atividades")
        sec_resp = st.selectbox("Secretária Responsável:", SECRETARIAS)
        alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="c1")
        cat_corr = st.selectbox("Material:", ["MSA Verde", "MSA Preto", "Apostila", "Caderno Pauta", "Métodos Antigos"])
        st_corr = st.selectbox("Status:", ["✅ Sem Pendência", "⚠️ Refazer", "❌ Não realizou"])
        obs_corr = st.text_area("Lições Corrigidas / Obs:")
        if st.button("💾 Salvar Registro da Secretaria"):
            st.session_state.controle_licoes.append({
                "Data": datetime.now().strftime("%d/%m/%Y"), "Aluna": alu_corr, 
                "Secretaria": sec_resp, "Material": cat_corr, "Status": st_corr, "Obs": obs_corr
            })
            st.success("Salvo com sucesso!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    instr = st.selectbox("Seu Nome:", PROFESSORAS_LISTA)
    data_hj = datetime.now().strftime("%d/%m/%Y")
    
    if data_hj in st.session_state.calendario_anual:
        h_sel = st.radio("Horário:", HORARIOS_LABELS, horizontal=True)
        atend = "Ninguém"
        for linha in st.session_state.calendario_anual[data_hj]["tabela"]:
            if f"({instr})" in linha.get(h_sel, ""): atend = linha["Aluna"]

        st.error(f"👤 Atendendo: **{atend}**")
        
        # --- FORMULÁRIO COMPLETO (25 ITENS) ---
        lic_vol = st.selectbox("Lição/Volume (1 a 40):", [str(i) for i in range(1, 41)] + ["MSA", "Hino"])
        
        dif_itens = [
            "Não estudou", "Insatisfatório", "Não viu vídeos", "Ritmo", "Nomes figuras", 
            "Adentrando teclas", "Postura", "Punho", "Banqueta", "Falanges", 
            "Unhas compridas", "Dedos arredondados", "Pedal", "Pé esquerdo", "Metrônomo", 
            "Sem metrônomo", "Clave Sol", "Clave Fá", "Apostila", "Articulação", 
            "Respirações", "Passagem dedos", "Dedilhado", "Nota Apoio", "Sem dificuldades"
        ]
        
        selec_dif = []
        col1, col2 = st.columns(2)
        for i, d in enumerate(dif_itens):
            if (col1 if i < 13 else col2).checkbox(d): selec_dif.append(d)
        
        obs_aula = st.text_area("Evolução da Aluna:")
        if st.button("💾 Salvar Aula"):
            st.session_state.historico_geral.append({
                "Data": data_hj, "Aluna": atend, "Tipo": "Aula", "Status": "Realizada", "Obs": obs_aula, "Dificuldades": selec_dif
            })
            st.success("Aula registrada!")
    else:
        st.warning("Rodízio não encontrado para hoje.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
else:
    st.header("📊 Analítico IA")
    alu_an = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    
    # Seção de Aulas
    df_h = pd.DataFrame(st.session_state.historico_geral)
    if not df_h.empty:
        df_f = df_h[df_h["Aluna"] == alu_an]
        if not df_f.empty:
            st.subheader("📋 Histórico de Aulas")
            # Correção do KeyError: Selecionamos apenas colunas que GARANTIDAMENTE existem
            cols_show = [c for c in ["Data", "Tipo", "Status", "Obs"] if c in df_f.columns]
            st.table(df_f[cols_show])
            st.markdown(link_para_print(df_f[cols_show], f"Aula_{alu_an}"), unsafe_allow_html=True)
    
    # Seção de Secretaria
    df_c = pd.DataFrame(st.session_state.controle_licoes)
    if not df_c.empty:
        df_fc = df_c[df_c["Aluna"] == alu_an]
        if not df_fc.empty:
            st.subheader("📋 Histórico da Secretaria")
            cols_sec = [c for c in ["Data", "Secretaria", "Material", "Status", "Obs"] if c in df_fc.columns]
            st.table(df_fc[cols_sec])
            st.markdown(link_para_print(df_fc[cols_sec], f"Secretaria_{alu_an}"), unsafe_allow_html=True)
