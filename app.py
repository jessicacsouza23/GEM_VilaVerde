import streamlit as st
import pandas as pd
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

if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão de Aulas e Rodízio")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora"])

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

        if st.button("🚀 Gerar e Mostrar Grade", use_container_width=True):
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

        if data_str in st.session_state.calendario_anual:
            st.divider()
            st.subheader(f"📊 Escala de Rodízio - {data_str}")
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

    with tab_chamada:
        st.subheader("📍 Chamada")
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"👤 {aluna}")
            col_b.checkbox("Presente", key=f"ch_{aluna}")

    with tab_controle:
        st.subheader("📋 Controle de Lições (Secretaria)")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.selectbox("Secretária responsável:", SECRETARIAS)
            st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
        with col_s2:
            st.multiselect("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"])
        
        st.divider()
        st.text_input("📝 Realizadas - sem pendência")
        st.text_input("⚠️ Realizada - devolvida para refazer")
        st.text_input("❌ Não realizada")
        st.text_area("🗒️ Observações (Controle)")
        st.button("💾 Salvar Controle de Lições")

    with tab_admin:
        if st.button("🔥 LIMPAR SISTEMA"):
            st.session_state.calendario_anual = {}
            st.rerun()

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
else:
    st.header("👩‍🏫 Portal da Instrutora")
    data_p = st.date_input("Data da Aula:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        instr_sel = st.selectbox("Selecione seu Nome:", PROFESSORAS_LISTA)
        h_sel = st.select_slider("Horário:", options=HORARIOS_LABELS)
        info = st.session_state.calendario_anual[d_str]
        
        atend, local, mat = "---", "---", "---"

        if h_sel == HORARIOS_LABELS[0]:
            local, atend, mat = "⛪ Igreja", "Todas as Alunas", "Solfejo Melódico"
        else:
            for linha in info["tabela"]:
                if f"({instr_sel})" in linha.get(h_sel, ""):
                    atend, local = linha["Aluna"], linha[h_sel].split(" | ")[0]
                    mat = "Teoria" if "SALA 8" in local else "Solfejo" if "SALA 9" in local else "Prática"

        if "SALA 8" in local: st.warning(f"📚 {local} | 👤 Aluna: {atend}")
        elif "SALA 9" in local: st.success(f"🔊 {local} | 👤 Aluna: {atend}")
        elif "Igreja" in local: st.info(f"⛪ {local} | 👤 Aluna: {atend}")
        else: st.error(f"🎹 {local} | 👤 Aluna: {atend}")

        st.divider()

        # --- FORMULÁRIO DE ACORDO COM A MATÉRIA ---
        if mat == "Prática":
            st.subheader("🎹 Controle de Desempenho - Aula Prática")
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Lição/Volume (Prática):", [str(i) for i in range(1, 41)] + ["Outro"], key="lic_pr")
            
            st.markdown("**Dificuldades (Marque todas que se aplicam):**")
            dif_pr = [
                "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos dos métodos",
                "Dificuldade ritmica", "Dificuldade em distinguir os nomes das figuras ritmicas",
                "Está adentrando às teclas", "Dificuldade com a postura (costas, ombros e braços)",
                "Está deixando o punho alto ou baixo", "Não senta no centro da banqueta", "Está quebrando as falanges",
                "Unhas muito compridas", "Dificuldade em deixar os dedos arredondados",
                "Esquece de colocar o pé direito no pedal de expressão", "Faz movimentos desnecessários com o pé esquerdo na pedaleira",
                "Dificuldade com o uso do metrônomo", "Estuda sem o metrônomo", "Dificuldades em ler as notas na clave de sol",
                "Dificuldades em ler as notas na clave de fá", "Não realizou as atividades da apostila",
                "Dificuldade em fazer a articulação ligada e semiligada", "Dificuldade com as respirações",
                "Dificuldade com as respirações sobre passagem", "Dificuldades em recurso de dedilhado",
                "Dificuldade em fazer nota de apoio", "Não apresentou dificuldades"
            ]
            c_a, c_b = st.columns(2)
            for i, d in enumerate(dif_pr): (c_a if i < 13 else c_b).checkbox(d, key=f"d_pr_{i}")
            
            st.divider()
            st.selectbox("Lição de casa - Volume prática:", [str(i) for i in range(1, 41)] + ["Outro"], key="home_pr")
            st.text_input("Lição de casa - Apostila:")

        elif mat == "Teoria":
            st.subheader("📚 Controle de Desempenho - Aula Teoria")
            st.text_input("Lição/Volume (Teoria):")
            
            st.markdown("**Dificuldades:**")
            dif_te = [
                "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
                "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
                "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
                "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
                "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
                "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
            ]
            c_te1, c_te2 = st.columns(2)
            for i, d in enumerate(dif_te): (c_te1 if i < 8 else c_te2).checkbox(d, key=f"d_te_{i}")
            st.text_input("Lição de casa (Teoria):")

        elif "Solfejo" in mat:
            st.subheader("🔊 Controle de Desempenho - Aula Solfejo")
            st.text_input("Lição/Volume (Solfejo):")
            
            st.markdown("**Dificuldades:**")
            dif_so = [
                "Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol",
                "Dificuldades em ler as notas na clave de fá", "Dificuldade no uso do metrônomo", "Estuda sem metrônomo",
                "Não realizou as atividades", "Dificuldade em leitura ritmica", "Dificuldades em leitura métrica",
                "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão",
                "Dificuldades na ordem das notas", "Não realizou as atividades da apostila",
                "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"
            ]
            c_so1, c_so2 = st.columns(2)
            for i, d in enumerate(dif_so): (c_so1 if i < 8 else c_so2).checkbox(d, key=f"d_so_{i}")
            st.text_input("Lição de casa (Solfejo):")

        st.divider()
        st.text_area("📝 Observações finais:")
        st.button("💾 Salvar Registro de Aula")
    else:
        st.error("Escala não gerada para hoje.")
