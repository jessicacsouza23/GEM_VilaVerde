import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Oficial", layout="wide")

# --- DADOS MESTRES ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

TODAS_ALUNAS = sorted([aluna for lista in TURMAS.values() for aluna in lista])
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS = ["08h45 (1ª Aula)", "09h35 (2ª Aula)", "10h10 (3ª Aula)", "10h45 (Aula Final)"]

if "grade_publicada" not in st.session_state:
    st.session_state.grade_publicada = None

# --- TÍTULO ---
st.title("🎼 GEM Vila Verde - Gestão Integrada")
perfil = st.sidebar.radio("Navegação:", ["Secretaria", "Professora"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    tab_gerar, tab_chamada, tab_corr = st.tabs(["⚙️ Gerar Rodízio", "📍 Chamada Geral", "✅ Correção de Atividades"])

    with tab_gerar:
        st.subheader("Configuração das Instrutoras")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📚 Sala 8 - Teoria")
            pt1 = st.selectbox("Prof. Teoria - T1:", PROFESSORAS_LISTA, index=0)
            pt2 = st.selectbox("Prof. Teoria - T2:", PROFESSORAS_LISTA, index=1)
            pt3 = st.selectbox("Prof. Teoria - T3:", PROFESSORAS_LISTA, index=2)
        with c2:
            st.markdown("#### 🔊 Sala 9 - Solfejo")
            st1 = st.selectbox("Prof. Solfejo - T1:", PROFESSORAS_LISTA, index=3)
            st2 = st.selectbox("Prof. Solfejo - T2:", PROFESSORAS_LISTA, index=4)
            st3 = st.selectbox("Prof. Solfejo - T3:", PROFESSORAS_LISTA, index=5)
        
        folgas = st.multiselect("Professoras de FOLGA:", PROFESSORAS_LISTA)

        if st.button("🚀 Gerar Grade Oficial", use_container_width=True):
            fixas = [pt1, pt2, pt3, st1, st2, st3]
            prat_disp = [p for p in PROFESSORAS_LISTA if p not in folgas and p not in fixas]
            random.shuffle(prat_disp)
            
            tabela_mestre = []
            for i in range(7):
                prof_p = prat_disp[i] if i < len(prat_disp) else "Vago"
                tabela_mestre.append({
                    "Sala": f"Sala {i+1} (Prática)",
                    "Instrutora": prof_p,
                    "08h45 (H1)": TURMAS["Turma 3"][i],
                    "09h35 (H2)": TURMAS["Turma 1"][i],
                    "10h10 (H3)": TURMAS["Turma 2"][i]
                })
            
            tabela_mestre.append({"Sala": "Sala 8 (Teoria)", "Instrutora": "Por Turma", "08h45 (H1)": f"T1 ({pt1})", "09h35 (H2)": f"T2 ({pt2})", "10h10 (H3)": f"T3 ({pt3})"})
            tabela_mestre.append({"Sala": "Sala 9 (Solfejo)", "Instrutora": "Por Turma", "08h45 (H1)": f"T2 ({st2})", "09h35 (H2)": f"T3 ({st3})", "10h10 (H3)": f"T1 ({st1})"})

            st.session_state.grade_publicada = {
                "tabela": tabela_mestre,
                "config": {
                    "teoria": {"Turma 1": pt1, "Turma 2": pt2, "Turma 3": pt3},
                    "solfejo": {"Turma 1": st1, "Turma 2": st2, "Turma 3": st3},
                    "pratica": prat_disp
                }
            }
            st.success("Grade Publicada!")

        if st.session_state.grade_publicada:
            st.divider()
            st.table(pd.DataFrame(st.session_state.grade_publicada["tabela"]))

    with tab_chamada:
        st.subheader("📍 Chamada Unificada")
        col_n, col_p, col_j = st.columns([3, 1, 1])
        col_n.write("**Aluna**")
        col_p.write("**P**")
        col_j.write("**J**")
        
        for aluna in TODAS_ALUNAS:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(aluna)
            c2.checkbox("Presença", key=f"p_{aluna}", label_visibility="collapsed")
            c3.checkbox("Justificado", key=f"j_{aluna}", label_visibility="collapsed")
        
        if st.button("💾 Salvar Chamada"):
            st.success("Chamada Salva!")

    with tab_corr:
        st.subheader("✅ FORMULÁRIO DE CORREÇÃO (SECRETARIA)")
        sel_alu = st.selectbox("Selecionar Aluna para Vistoria:", TODAS_ALUNAS)
        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("Materiais Conferidos:", ["MSA (Verde)", "MSA (Preto)", "Caderno Pauta", "Apostila", "Folhas Avulsas"])
            st.radio("Apostila em mãos?", ["Sim", "Não", "Esqueceu"], horizontal=True)
        with c2:
            st.radio("Vídeos da Semana?", ["Sim", "Não", "Incompleto"], horizontal=True)
            st.radio("Exercícios de Pauta?", ["Sim", "Não", "Incompleto"], horizontal=True)
        st.text_area("Notas da Secretaria (Pendências/Aprovações):")
        st.button("Salvar Correção Secretaria")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("🎹 Área da Instrutora")
    if not st.session_state.grade_publicada:
        st.warning("⚠️ Rodízio não disponível.")
    else:
        conf = st.session_state.grade_publicada["config"]
        p_nome = st.selectbox("Instrutora:", PROFESSORAS_LISTA)
        h_atual = st.select_slider("Horário:", options=HORARIOS)

        rot = {
            HORARIOS[0]: {"teo": "Turma 1", "sol": "Turma 2", "prat": "Turma 3"},
            HORARIOS[1]: {"teo": "Turma 2", "sol": "Turma 3", "prat": "Turma 1"},
            HORARIOS[2]: {"teo": "Turma 3", "sol": "Turma 1", "prat": "Turma 2"},
            HORARIOS[3]: {"teo": "Geral", "sol": "Geral", "prat": "Fim"}
        }

        sala, atend, mat = "Não alocada", "---", "---"
        if h_atual != HORARIOS[3]:
            t_teo, t_sol = rot[h_atual]["teo"], rot[h_atual]["sol"]
            if p_nome == conf["teoria"].get(t_teo): sala, atend, mat = "Sala 8 (Teoria)", t_teo, "Teoria"
            elif p_nome == conf["solfejo"].get(t_sol): sala, atend, mat = "Sala 9 (Solfejo)", t_sol, "Solfejo"
            elif p_nome in conf["pratica"]:
                idx = conf["pratica"].index(p_nome)
                sala, mat = f"Sala {idx+1} (Prática)", "Prática"
                atend = TURMAS[rot[h_atual]["prat"]][idx]
        
        st.info(f"📍 **{sala}** | 👤 **Atendimento:** {atend}")

        # --- FORMULÁRIO: AULA PRÁTICA ---
        if mat == "Prática":
            st.subheader("📋 FORMULÁRIO DE AULA PRÁTICA (Checklist 25 itens)")
            st.selectbox("Lição:", [str(i) for i in range(1,41)])
            difs = ["Não estudou nada", "Estudo insatisfatório", "Não assistiu os vídeos",
                    "Dificuldade rítmica", "Nomes figuras rítmicas", "Adentrando às teclas",
                    "Postura (costas/ombros/braços)", "Punho alto/baixo", "Não senta no centro",
                    "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                    "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo",
                    "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Atividades apostila",
                    "Articulação ligada/semiligada", "Respirações", "Respirações passagem",
                    "Recurso de dedilhado", "Nota de apoio", "Não apresentou dificuldades"]
            cols = st.columns(2)
            for i, d in enumerate(difs): (cols[0] if i < 13 else cols[1]).checkbox(d, key=f"pra_{i}")

        # --- FORMULÁRIO: AULA TEÓRICA ---
        elif mat == "Teoria":
            st.subheader(f"📋 FORMULÁRIO DE AULA TEÓRICA - {atend}")
            c1, c2 = st.columns(2)
            with c1:
                st.checkbox("Explicação do Módulo MSA")
                st.checkbox("Correção de Exercícios de Pauta")
                st.checkbox("Aplicação de Teste Teórico")
            with c2:
                st.checkbox("Notas na Clave (Leitura)")
                st.checkbox("Intervalos / Armaduras / Tonalidades")
                st.checkbox("Participação / Comportamento")

        # --- FORMULÁRIO: AULA DE SOLFEJO (EXPANDIDO) ---
        elif mat == "Solfejo":
            st.subheader(f"📋 FORMULÁRIO DE AULA DE SOLFEJO - {atend}")
            st.write("**Avaliação de Técnica e Performance:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Rítmica**")
                st.checkbox("Linguagem Rítmica (Ti-ti)")
                st.checkbox("Pulsação Constante")
                st.checkbox("Respeito ao Metrônomo")
                st.checkbox("Divisão de Figuras")
            with col2:
                st.markdown("**Melódica**")
                st.checkbox("Afinação (Solfejo Melódico)")
                st.checkbox("Acentuação Métrica")
                st.checkbox("Leitura de Notas (Claves)")
                st.checkbox("Dinâmicas / Expressão")
            with col3:
                st.markdown("**Postura e Gestos**")
                st.checkbox("Movimento da Mão (Compasso)")
                st.checkbox("Postura Corporal")
                st.checkbox("Respiração (Fraseado)")
                st.checkbox("Entrada no Tempo (Anacruse/Tética)")

        st.divider()
        st.text_input("🏠 Lição para Casa:")
        st.text_area("📝 Observações da Instrutora:")
        st.button("Finalizar Registro de Aula")
