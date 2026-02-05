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
if "presenca_temp" not in st.session_state:
    st.session_state.presenca_temp = {}
if "controle_licoes" not in st.session_state:
    st.session_state.controle_licoes = []

# --- FUNÇÃO PARA EXPORTAR ---
def baixar_tabela_como_html(df, titulo):
    html = f"<html><head><meta charset='utf-8'></head><body><h2 style='font-family: Arial; text-align: center;'>{titulo}</h2>"
    html += df.to_html(index=False, justify='center', border=1)
    html += "</body></html>"
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{titulo}.html" style="text-decoration: none; background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px;">📥 Salvar como Arquivo para Imagem</a>'

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
        st.subheader("🗓️ Planejamento e Consulta de Rodízio")
        data_sel = st.date_input("Escolha o Sábado:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # PERSISTÊNCIA: Mostra se já existir
        if data_str in st.session_state.calendario_anual:
            st.success(f"✅ Rodízio encontrado para {data_str}")
            df_atual = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.table(df_atual)
            st.markdown(baixar_tabela_como_html(df_atual, f"Rodizio_{data_str.replace('/','-')}"), unsafe_allow_html=True)
            if st.button("🔄 Gerar Novo Rodízio (Substituir)"):
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
                            h_label = HORARIOS_LABELS[h_idx]
                            config = fluxo[h_label]
                            if config["Teo"] == t_nome: ag[h_label] = f"📚 S8|Teo({config['ITeo']})"
                            elif config["Sol"] == t_nome: ag[h_label] = f"🔊 S9|Sol({config['ISol']})"
                            else:
                                p_disp = [p for p in PROFESSORAS_LISTA if p not in [config["ITeo"], config["ISol"]] + folgas]
                                instr_p = p_disp[i % len(p_disp)] if p_disp else "Vago"
                                ag[h_label] = f"🎹 S{(i+offset)%7+1}|Pra({instr_p})"
                        escala.append(ag)
                st.session_state.calendario_anual[data_str] = {"tabela": escala}
                st.rerun()

    with tab_chamada:
        st.subheader("📍 Chamada")
        if st.button("✅ Marcar Todas Presentes"):
            for aluna in sorted([a for l in TURMAS.values() for a in l]):
                st.session_state.presenca_temp[aluna] = "Presente"
        
        chamada_temp = []
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            c_a, c_b, c_c = st.columns([2, 2, 2])
            c_a.write(f"👤 **{aluna}**")
            val = st.session_state.presenca_temp.get(aluna, "Presente")
            st_ch = c_b.radio(f"S_{aluna}", ["Presente", "Falta", "Justificada"], index=["Presente", "Falta", "Justificada"].index(val), key=f"ch_{aluna}", horizontal=True, label_visibility="collapsed")
            mot = c_c.text_input("Motivo:", key=f"mot_{aluna}") if st_ch == "Justificada" else ""
            chamada_temp.append({"Data": data_str, "Aluna": aluna, "Status": st_ch, "Obs": mot})

        if st.button("💾 Salvar Chamada Completa", type="primary"):
            st.session_state.historico_geral.extend(chamada_temp)
            st.success("Chamada Salva!")

    with tab_controle:
        st.subheader("📋 Correção de Atividades (Secretaria)")
        c1, c2 = st.columns(2)
        with c1:
            sec_resp = st.selectbox("Secretária responsável:", SECRETARIAS)
            alu_corr = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="alu_c")
        with c2:
            cat_corr = st.selectbox("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"])
            status_corr = st.selectbox("Status:", ["✅ Realizadas - sem pendência", "⚠️ Realizada - devolvida para refazer", "❌ Não realizada"])
        
        detalhes_corr = st.text_area("Observações detalhadas:")
        if st.button("💾 Salvar Correção de Atividade"):
            st.session_state.controle_licoes.append({
                "Data": data_str, "Secretaria": sec_resp, "Aluna": alu_corr, "Categoria": cat_corr, "Status": status_corr, "Obs": detalhes_corr
            })
            st.success("Correção Registrada!")

    with tab_admin:
        if st.button("🔥 RESETAR TODOS OS DADOS"):
            st.session_state.clear()
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")
    instr_sel = st.selectbox("👤 Seu Nome:", PROFESSORAS_LISTA)

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", options=HORARIOS_LABELS, horizontal=True)
        tabela = st.session_state.calendario_anual[d_str]["tabela"]
        
        atend, local, mat = "---", "---", "---"
        for linha in tabela:
            if f"({instr_sel})" in linha.get(h_sel, ""):
                atend, local = linha["Aluna"], linha[h_sel]
                mat = "Teoria" if "SALA 8" in local else "Solfejo" if "SALA 9" in local else "Prática"

        st.divider()
        st.error(f"📍 Local: {local} | 👤 Aluna: {atend}")

        # --- IA ANALÍTICO ---
        last_obs = "Nenhum registro anterior."
        for h in reversed(st.session_state.historico_geral):
            if h["Aluna"] == atend and h.get("Tipo") == "Aula":
                last_obs = h["Obs"]
                break
        st.info(f"🤖 **Analítico IA para {atend}:** {last_obs}")

        # --- FORMULÁRIOS COMPLETOS ---
        if mat == "Prática":
            st.subheader("🎹 Controle de Desempenho - Aula Prática")
            st.selectbox("Lição/Volume (1 a 40):", [str(i) for i in range(1, 41)] + ["Outro"])
            
            st.markdown("**Dificuldades (Checklist completo):**")
            dif_pr = [
                "Não estudou nada", "Estudou insatisfatório", "Não assistiu vídeos",
                "Dificuldade ritmica", "Figuras ritmicas", "Adentrando às teclas",
                "Postura", "Punho alto/baixo", "Centro da banqueta", "Quebrando falanges",
                "Unhas compridas", "Dedos arredondados", "Pedal de expressão",
                "Pé esquerdo", "Metrônomo", "Estuda sem metrônomo", "Clave de Sol",
                "Clave de Fá", "Atividades apostila", "Articulação", "Respirações",
                "Respiração passagem", "Dedilhado", "Nota de apoio", "Sem dificuldades"
            ]
            c_a, c_b = st.columns(2)
            selec_dif = []
            for i, d in enumerate(dif_pr):
                if (c_a if i < 13 else c_b).checkbox(d, key=f"d_{i}"): selec_dif.append(d)
        
        else:
            st.subheader(f"🎼 Controle de {mat}")
            st.text_input("Lição/Volume:")
            dif_geral = ["Não assistiu vídeos", "Clave de Sol", "Clave de Fá", "Metrônomo", "Ritmo", "Solfejo", "Sem dificuldades"]
            selec_dif = [d for d in dif_geral if st.checkbox(d, key=f"dg_{d}")]

        obs_aula = st.text_area("📝 Observações da Aula:")
        if st.button("💾 SALVAR REGISTRO DE AULA"):
            st.session_state.historico_geral.append({"Data": d_str, "Aluna": atend, "Tipo": "Aula", "Materia": mat, "Dificuldades": selec_dif, "Obs": obs_aula})
            st.success("Aula Salva!")
    else:
        st.warning("⚠️ Rodízio não gerado para esta data.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
else:
    st.header("📊 Inteligência de Desempenho")
    alu_an = st.selectbox("Selecione a Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    
    # Histórico de Aulas e Chamadas
    st.subheader("📋 Histórico Geral")
    df_h = pd.DataFrame(st.session_state.historico_geral)
    if not df_h.empty:
        df_alu = df_h[df_h["Aluna"] == alu_an][["Data", "Tipo", "Status", "Obs"]]
        st.table(df_alu)
        st.markdown(baixar_tabela_como_html(df_alu, f"Historico_{alu_an}"), unsafe_allow_html=True)
    
    # Histórico de Correções
    st.subheader("📋 Correções da Secretaria")
    df_c = pd.DataFrame(st.session_state.controle_licoes)
    if not df_c.empty:
        df_c_alu = df_c[df_c["Aluna"] == alu_an][["Data", "Secretaria", "Categoria", "Status", "Obs"]]
        st.table(df_c_alu)
        st.markdown(baixar_tabela_como_html(df_c_alu, f"Correcoes_{alu_an}"), unsafe_allow_html=True)
