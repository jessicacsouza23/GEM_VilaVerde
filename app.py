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
    return f'<a href="data:text/html;base64,{b64}" download="{titulo}.html" style="text-decoration: none; background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px;">📥 Salvar Arquivo para Print</a>'

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
        data_sel = st.date_input("Escolha a Data:", value=datetime.now())
        data_str = data_sel.strftime("%d/%m/%Y")
        ja_existe = data_str in st.session_state.calendario_anual

        offset_semana = (data_sel.day // 7) % 7
        c1, c2 = st.columns(2)
        with c1:
            pt2 = st.selectbox("Instrutora Teoria H2 (T1):", PROFESSORAS_LISTA, index=0, key="pt2")
            pt3 = st.selectbox("Instrutora Teoria H3 (T2):", PROFESSORAS_LISTA, index=1, key="pt3")
            pt4 = st.selectbox("Instrutora Teoria H4 (T3):", PROFESSORAS_LISTA, index=2, key="pt4")
        with c2:
            st2 = st.selectbox("Instrutora Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3, key="st2")
            st3 = st.selectbox("Instrutora Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4, key="st3")
            st4 = st.selectbox("Instrutora Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5, key="st4")
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

        if ja_existe:
            df_rd = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            st.table(df_rd)
            st.markdown(baixar_tabela_como_html(df_rd, f"Rodizio_{data_str}"), unsafe_allow_html=True)

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        dt_ch = st.date_input("Data da Chamada:", value=datetime.now(), key="dt_ch").strftime("%d/%m/%Y")
        chamada_lista = []
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            c_a, c_b, c_c = st.columns([2, 2, 2])
            c_a.write(f"👤 **{aluna}**")
            status = c_b.radio(f"Status_{aluna}", ["Presente", "Falta", "Justificada"], horizontal=True, label_visibility="collapsed")
            motivo = c_c.text_input("Motivo:", key=f"mot_{aluna}") if status == "Justificada" else ""
            chamada_lista.append({"Aluna": aluna, "Status": status, "Motivo": motivo})
        if st.button("💾 SALVAR CHAMADA COMPLETA"):
            for r in chamada_lista:
                st.session_state.historico_geral.append({"Data": dt_ch, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Motivo": r["Motivo"]})
            st.success("Chamada Salva!")

    with tab_controle:
        st.subheader("📋 Controle de Lições (Secretaria)")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sec_resp = st.selectbox("Secretária responsável:", SECRETARIAS)
            alu_sec = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]), key="alu_sec")
            cat_sec = st.multiselect("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila"])
        with col_s2:
            r_ok = st.text_input("📝 Realizadas - sem pendência")
            r_ref = st.text_input("⚠️ Realizada - devolvida para refazer")
            r_no = st.text_input("❌ Não realizada")
        obs_sec = st.text_area("Observações Gerais")
        if st.button("💾 Salvar Controle Secretaria"):
            st.session_state.controle_licoes.append({
                "Data": data_str, "Aluna": alu_sec, "Secretaria": sec_resp, "Categoria": cat_sec, "Status": r_ok, "Obs": obs_sec
            })
            st.success("Salvo com sucesso!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    instr_sel = st.selectbox("👤 Selecione seu Nome:", PROFESSORAS_LISTA)
    data_p = st.date_input("📅 Data da Aula:", value=datetime.now(), key="dt_p")
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", options=HORARIOS_LABELS, horizontal=True)
        atend = "---"
        for linha in st.session_state.calendario_anual[d_str]["tabela"]:
            if f"({instr_sel})" in str(linha.values()): atend = linha["Aluna"]
        
        st.error(f"👤 Atendimento: **{atend}**")
        lic_aula = st.selectbox("Lição/Volume (1 a 40):", [str(i) for i in range(1, 41)] + ["MSA", "Hino"])
        
        st.markdown("**Checklist de Dificuldades Técnicas:**")
        dif_itens = [
            "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos",
            "Dificuldade ritmica", "Dificuldade nomes figuras", "Adentrando às teclas", 
            "Postura", "Punho alto/baixo", "Posição banqueta", "Quebrando falanges", 
            "Unhas compridas", "Dedos arredondados", "Pedal de expressão", "Pé esquerdo", 
            "Metrônomo", "Estuda sem metrônomo", "Clave sol", "Clave fá", "Apostila", 
            "Articulação", "Respirações", "Respiração passagem", "Dedilhado", "Nota de apoio", "Sem dificuldades"
        ]
        c1, c2 = st.columns(2)
        selecionadas = []
        for i, d in enumerate(dif_itens):
            if (c1 if i < 13 else c2).checkbox(d, key=f"dif_{i}"): selecionadas.append(d)
        
        obs_aula = st.text_area("📝 Evolução Detalhada desta Aula:")
        if st.button("💾 SALVAR REGISTRO DE AULA", use_container_width=True):
            st.session_state.historico_geral.append({
                "Data": d_str, "Aluna": atend, "Tipo": "Aula", "Licao": lic_aula, 
                "Dificuldades": selecionadas, "Obs": obs_aula, "Instrutora": instr_sel
            })
            st.success(f"Aula de {atend} salva!")
    else:
        st.warning("⚠️ Peça para a Secretaria gerar o rodízio de hoje.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise de Desempenho e Diário Diário")
    alu_an = st.selectbox("Selecione a Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    
    df_h = pd.DataFrame(st.session_state.historico_geral)
    
    if not df_h.empty:
        df_aluna = df_h[df_h["Aluna"] == alu_an]
        df_aulas = df_aluna[df_aluna["Tipo"] == "Aula"]
        
        # --- MÉTRICAS ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Aulas Realizadas", len(df_aulas))
        m2.metric("Lições Únicas", df_aulas["Licao"].nunique() if "Licao" in df_aulas.columns else 0)
        
        # --- DIÁRIO DETALHADO (AULA POR AULA) ---
        st.divider()
        st.subheader("📅 Diário Detalhado (Evolução Diária)")
        if not df_aulas.empty:
            for _, row in df_aulas.sort_index(ascending=False).iterrows():
                with st.expander(f"Data: {row['Data']} | Lição: {row.get('Licao', 'S/L')} | Instrutora: {row.get('Instrutora', '---')}"):
                    st.write(f"**Dificuldades:** {', '.join(row.get('Dificuldades', []))}")
                    st.info(f"**Evolução:** {row.get('Obs', '')}")
            
            st.markdown(baixar_tabela_como_html(df_aulas, f"Relatorio_Diario_{alu_an}"), unsafe_allow_html=True)
        else:
            st.write("Nenhuma aula registrada para esta aluna.")
    else:
        st.write("Sem dados no sistema.")
