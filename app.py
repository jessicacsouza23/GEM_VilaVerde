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

    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        dt_ch = st.date_input("Data da Chamada:", value=datetime.now(), key="dt_ch_input").strftime("%d/%m/%Y")
        alunas_lista = sorted([a for l in TURMAS.values() for a in l])
        
        if st.button("✅ Selecionar Todas como Presente"):
            for aluna in alunas_lista: st.session_state[f"ch_{aluna}"] = "Presente"

        chamada_temp = []
        for aluna in alunas_lista:
            c1, c2, c3 = st.columns([2, 3, 2])
            c1.write(f"👤 **{aluna}**")
            if f"ch_{aluna}" not in st.session_state: st.session_state[f"ch_{aluna}"] = "Presente"
            status = c2.radio(f"S_{aluna}", ["Presente", "Falta", "Justificada"], key=f"ch_{aluna}", horizontal=True, label_visibility="collapsed")
            motivo = ""
            if status == "Justificada":
                motivo = c3.text_input("Motivo:", key=f"mot_{aluna}")
            chamada_temp.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        if st.button("
