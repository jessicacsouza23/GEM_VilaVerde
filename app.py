import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from fpdf import FPDF
import io

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

# --- FUNÇÃO PARA GERAR PDF DA ANÁLISE ---
def gerar_pdf_analise(aluna, periodo, historico):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio de Desempenho - GEM Vila Verde", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Aluna: {aluna} | Periodo: {periodo}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Historico de Aulas e Observacoes:", ln=True)
    pdf.set_font("Arial", "", 10)
    
    for item in historico:
        if item["Aluna"] == aluna:
            texto = f"Data: {item['Data']} | Status: {item.get('Status', 'Aula')} | Obs: {item.get('Obs', 'N/A')}"
            pdf.multi_cell(190, 10, texto)
            pdf.ln(2)
            
    return pdf.output(dest="S").encode("latin-1")

# --- INICIALIZAÇÃO DE MEMÓRIA ---
if "calendario_anual" not in st.session_state:
    st.session_state.calendario_anual = {}
if "historico_geral" not in st.session_state:
    st.session_state.historico_geral = []
if "presenca_temp" not in st.session_state:
    st.session_state.presenca_temp = {}

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

        if st.button("🚀 Gerar/Atualizar Rodízio", use_container_width=True):
            escala_final = []
            fluxo = {
                HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
            }
            offset_semana = (data_sel.day // 7) % 7
            for t_nome, alunas in TURMAS.items():
                for i, aluna in enumerate(alunas):
                    agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                    for h_idx in [1, 2, 3]:
                        h_label = HORARIOS_LABELS[h_idx]
                        config = fluxo[h_label]
                        if config["Teo"] == t_nome: agenda[h_label] = f"📚 S8|Teo({config['ITeo']})"
                        elif config["Sol"] == t_nome: agenda[h_label] = f"🔊 S9|Sol({config['ISol']})"
                        else:
                            p_disp = [p for p in PROFESSORAS_LISTA if p not in [config["ITeo"], config["ISol"]] + folgas]
                            sala_p = (i + offset_semana + h_idx) % 7 + 1
                            instr_p = p_disp[i % len(p_disp)] if p_disp else "Vago"
                            agenda[h_label] = f"🎹 S{sala_p}|Pra({instr_p})"
                    escala_final.append(agenda)
            st.session_state.calendario_anual[data_str] = {"tabela": escala_final}

        if ja_existe:
            st.divider()
            st.subheader(f"🖼️ Rodízio Visual - {data_str}")
            df_view = pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"])
            
            # Estilização para parecer uma imagem organizada
            st.dataframe(df_view.style.set_properties(**{
                'background-color': '#f0f2f6',
                'color': 'black',
                'border-color': 'white'
            }), use_container_width=True)
            
            st.info("💡 Para salvar como imagem: Use a ferramenta de captura (Print) desta tabela acima ou exporte para CSV abaixo.")
            st.download_button("📥 Baixar Rodízio (CSV)", df_view.to_csv(index=False).encode('utf-8'), f"rodizio_{data_str}.csv", "text/csv")

    with tab_chamada:
        st.subheader("📍 Chamada")
        data_ch_str = data_sel.strftime("%d/%m/%Y")
        if st.button("✅ Todas Presentes"):
            for aluna in sorted([a for l in TURMAS.values() for a in l]):
                st.session_state.presenca_temp[aluna] = "Presente"
        
        chamada_lista = []
        for aluna in sorted([a for l in TURMAS.values() for a in l]):
            c_a, c_b, c_c = st.columns([2, 2, 2])
            c_a.write(f"👤 **{aluna}**")
            val_p = st.session_state.presenca_temp.get(aluna, "Presente")
            idx_p = ["Presente", "Falta", "Justificada"].index(val_p)
            status = c_b.radio(f"Status_{aluna}", ["Presente", "Falta", "Justificada"], index=idx_p, key=f"rad_{aluna}", horizontal=True, label_visibility="collapsed")
            motivo = c_c.text_input("Motivo:", key=f"mot_{aluna}") if status == "Justificada" else ""
            chamada_lista.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        if st.button("💾 SALVAR CHAMADA COMPLETA", type="primary"):
            for r in chamada_lista:
                st.session_state.historico_geral.append({"Data": data_ch_str, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Obs": r["Motivo"]})
            st.success("Chamada Salva!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Portal da Instrutora")
    data_p = st.date_input("📅 Data da Aula:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")
    instr_sel = st.selectbox("👤 Seu Nome:", PROFESSORAS_LISTA)

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", options=HORARIOS_LABELS, horizontal=True)
        info = st.session_state.calendario_anual[d_str]
        atend, local, mat = "---", "---", "---"

        for linha in info["tabela"]:
            if f"({instr_sel})" in linha.get(h_sel, ""):
                atend, local = linha["Aluna"], linha[h_sel].split("|")[0]
                mat = "Teoria" if "S8" in local else "Solfejo" if "S9" in local else "Prática"

        st.divider()
        st.error(f"📍 {local} | 👤 Aluna: {atend}")
        
        obs_aula = st.text_area("📝 Evolução da Aluna:")
        if st.button("💾 Salvar Aula"):
            st.session_state.historico_geral.append({"Data": d_str, "Aluna": atend, "Tipo": "Aula", "Materia": mat, "Obs": obs_aula})
            st.success("Registrado!")
    else:
        st.warning("Rodízio não gerado para hoje.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Analítico IA e Relatórios")
    alu_an = st.selectbox("Selecione a Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    per_an = st.select_slider("Período:", ["Mensal", "Bimestral", "Semestral", "Anual"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Frequência")
        chart_data = pd.DataFrame({"Mês": ["Jan", "Fev", "Mar"], "Presenças": [4, 3, 4]})
        st.bar_chart(chart_data, x="Mês")
    
    with col2:
        st.subheader("📄 Gerar Documento")
        if st.button("📝 Gerar Relatório PDF"):
            pdf_bytes = gerar_pdf_analise(alu_an, per_an, st.session_state.historico_geral)
            st.download_button(label="📥 Baixar PDF", data=pdf_bytes, file_name=f"Relatorio_{alu_an}.pdf", mime="application/pdf")

    st.subheader("📋 Histórico Completo")
    df_h = pd.DataFrame(st.session_state.historico_geral)
    if not df_h.empty:
        st.dataframe(df_h[df_h["Aluna"] == alu_an], use_container_width=True)
