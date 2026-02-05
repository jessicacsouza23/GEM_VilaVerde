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

# --- INICIALIZAÇÃO DE MEMÓRIA ---
if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}
if "historico_geral" not in st.session_state:
    st.session_state.historico_geral = []
if "presenca_temp" not in st.session_state:
    st.session_state.presenca_temp = {}
if "controle_licoes" not in st.session_state:
    st.session_state.controle_licoes = []

# --- FUNÇÃO DE DOWNLOAD (FORMATO PARA PRINT) ---
def link_para_imagem(df, titulo):
    html = f"""
    <html><body style='font-family:Arial; padding:20px;'>
    <h2 style='text-align:center; color:#2E7D32;'>{titulo}</h2>
    {df.to_html(index=False, justify='center', border=1)}
    <p style='text-align:center;'>Gerado pelo Sistema GEM Vila Verde - 2026</p>
    </body></html>
    """
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{titulo}.html" style="background-color:#FF4B4B; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">📸 CLIQUE AQUI PARA GERAR IMAGEM (PRINT)</a>'

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    t1, t2, t3, t4 = st.tabs(["🗓️ Rodízio", "📍 Chamada", "✅ Correção Lições", "⚠️ Admin"])

    with t1:
        st.subheader("🗓️ Planejamento de Sábado")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # PERSISTÊNCIA: Se já existe, mostra
        if data_str in st.session_state.calendario_anual:
            st.success(f"✅ Rodízio salvo para {data_str}")
            df_view = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.table(df_view)
            st.markdown(link_para_imagem(df_view, f"Rodizio_{data_str.replace('/','-')}"), unsafe_allow_html=True)
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
            
            folgas = st.multiselect("Folgas:", PROFESSORAS_LISTA)

            if st.button("🚀 Gerar e Salvar"):
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
                            h_lab = HORARIOS_LABELS[h_idx]
                            cfg = fluxo[h_lab]
                            if cfg["Teo"] == t_nome: ag[h_lab] = f"📚 S8|Teo({cfg['ITeo']})"
                            elif cfg["Sol"] == t_nome: ag[h_lab] = f"🔊 S9|Sol({cfg['ISol']})"
                            else:
                                p_disp = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]] + folgas]
                                ag[h_lab] = f"🎹 S{(i+offset)%7+1}|Pra({p_disp[i%len(p_disp)] if p_disp else 'Vago'})"
                        escala.append(ag)
                st.session_state.calendario_anual[data_str] = {"tabela": escala}
                st.rerun()

    with t3:
        st.subheader("✅ Correção de Atividades")
        sec_resp = st.selectbox("Secretária que corrigiu:", SECRETARIAS)
        alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="c1")
        cat_corr = st.selectbox("Material:", ["MSA Verde", "MSA Preto", "Apostila", "Caderno Pauta"])
        st_corr = st.selectbox("Status:", ["✅ Ok", "⚠️ Refazer", "❌ Não fez"])
        obs_corr = st.text_area("Lições/Observações:")
        if st.button("💾 Salvar Correção"):
            st.session_state.controle_licoes.append({"Data": data_str, "Secretaria": sec_resp, "Aluna": alu_corr, "Status": st_corr, "Obs": obs_corr})
            st.success("Salvo!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    instr = st.selectbox("Quem é você?", PROFESSORAS_LISTA)
    d_str = datetime.now().strftime("%d/%m/%Y")
    
    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("Horário:", HORARIOS_LABELS, horizontal=True)
        atend = "Ninguém"
        for linha in st.session_state.calendario_anual[d_str]["tabela"]:
            if f"({instr})" in linha.get(h_sel, ""): atend = linha["Aluna"]

        st.error(f"👤 Atendendo agora: **{atend}**")
        
        # --- FORMULÁRIO COMPLETO (RESTAURADO) ---
        lic_vol = st.selectbox("Lição/Volume (1 a 40):", [str(i) for i in range(1, 41)])
        
        dif_itens = [
            "Não estudou", "Insatisfatório", "Não viu vídeos", "Ritmo", "Postura", 
            "Punho", "Banqueta", "Falanges", "Unhas compridas", "Dedos arredondados", 
            "Pedal", "Pé esquerdo", "Metrônomo", "Clave de Sol", "Clave de Fá", 
            "Apostila", "Articulação", "Respiração", "Dedilhado", "Nota de Apoio"
        ]
        
        selecionados = []
        c1, c2 = st.columns(2)
        for i, d in enumerate(dif_itens):
            if (c1 if i < 10 else c2).checkbox(d): selecionados.append(d)
        
        obs_aula = st.text_area("Observações da Aula:")
        if st.button("💾 Salvar Aula"):
            st.session_state.historico_geral.append({"Data": d_str, "Aluna": atend, "Obs": obs_aula, "Dificuldades": selecionados})
            st.success("Salvo!")
    else:
        st.warning("Rodízio não gerado hoje.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
else:
    st.header("📊 Analítico IA")
    alu_an = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    
    df_h = pd.DataFrame(st.session_state.historico_geral)
    if not df_h.empty:
        df_f = df_h[df_h["Aluna"] == alu_an][["Data", "Obs"]]
        st.table(df_f)
        # O BOTÃO QUE VOCÊ QUERIA PARA SALVAR O ANALÍTICO
        st.markdown(link_para_imagem(df_f, f"Analitico_{alu_an}"), unsafe_allow_html=True)
    else:
        st.write("Sem dados.")
