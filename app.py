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
    tab_gerar, tab_chamada, tab_controle = st.tabs(["🗓️ Planejar Sábado", "📍 Chamada", "✅ Correção de Atividades"])

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
            st.table(pd.DataFrame(st.session_state.calendario_anual[data_str]["tabela"]))

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

        if st.button("💾 SALVAR CHAMADA COMPLETA", use_container_width=True):
            for r in chamada_temp:
                st.session_state.historico_geral.append({"Data": dt_ch, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Motivo": r["Motivo"]})
            st.success("Chamada salva!")

    with tab_controle:
        st.subheader("✅ Correção de Atividades")
        c_sec1, c_sec2 = st.columns(2)
        with c_sec1:
            sec_resp = st.selectbox("Secretária Responsável pela Correção:", SECRETARIAS)
            alu_sec = st.selectbox("Aluna:", alunas_lista)
            cat_sec = st.multiselect("Livro/Apostila:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila"])
        with c_sec2:
            status_corr = st.radio("Status da Atividade:", ["Realizada", "Não Realizada", "Devolvida para Correção"])
            detalhe_atv = st.text_input("Lições/Páginas corrigidas")
            obs_sec = st.text_area("Observações da Secretaria")
            
        if st.button("💾 Salvar Registro de Correção", use_container_width=True):
            st.session_state.controle_licoes.append({
                "Data": data_str, "Aluna": alu_sec, "Secretaria": sec_resp,
                "Status": status_corr, "Atividade": detalhe_atv, "Categoria": cat_sec, "Obs": obs_sec
            })
            st.success(f"Registrado por {sec_resp}!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Registro de Aula")
    instr_sel = st.selectbox("👤 Identifique-se (Instrutora):", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        
        # Identificação automática do tipo de aula (Teoria/Solfejo ou Prática)
        conteudo_rodizio = ""
        aluna_pratica = "---"
        turma_teoria = "---"
        tipo_aula = "Prática" # Default
        
        for linha in st.session_state.calendario_anual[d_str]["tabela"]:
            celula = str(linha.get(h_sel, ""))
            if f"({instr_sel})" in celula:
                conteudo_rodizio = celula
                if "Teoria" in celula or "Solfejo" in celula:
                    tipo_aula = "Grupo"
                    turma_teoria = linha["Turma"]
                else:
                    tipo_aula = "Individual"
                    aluna_pratica = linha["Aluna"]
                break

        # EXIBIÇÃO DINÂMICA
        if tipo_aula == "Individual":
            st.error(f"🎹 AULA INDIVIDUAL | Aluna: **{aluna_pratica}** | {conteudo_rodizio}")
            check_alunas = [aluna_pratica] if aluna_pratica != "---" else []
        else:
            st.info(f"📚 AULA EM GRUPO | Turma: **{turma_teoria}** | {conteudo_rodizio}")
            st.markdown("### 👥 Selecione as alunas presentes nesta explicação:")
            alunas_da_turma = TURMAS.get(turma_teoria, [])
            check_alunas = []
            if alunas_da_turma:
                cols = st.columns(4)
                for i, aluna in enumerate(alunas_da_turma):
                    if cols[i % 4].checkbox(aluna, value=True, key=f"chk_{aluna}"):
                        check_alunas.append(aluna)

        st.divider()
        lic_aula = st.selectbox("Lição/Volume:", [str(i) for i in range(1, 41)] + ["MSA", "Hino"])
        
        st.markdown("**Checklist de Dificuldades Técnicas:**")
        dif_itens = ["Não estudou", "Estudou insatisfatório", "Sem vídeos", "Rítmica", "Nomes figuras", "Postura", "Punho", "Banqueta", "Falanges", "Unhas", "Dedos", "Pedal", "Pé esquerdo", "Metrônomo", "Clave sol", "Clave fá", "Articulação", "Dedilhado", "Sem dificuldades"]
        c1, c2, c3 = st.columns(3)
        selecionadas_dif = []
        for i, d in enumerate(dif_itens):
            target = c1 if i < 7 else (c2 if i < 14 else c3)
            if target.checkbox(d, key=f"dif_aula_{i}"): selecionadas_dif.append(d)
        
        obs_aula = st.text_area("📝 Evolução Detalhada:")
        
        if st.button("💾 SALVAR REGISTRO", use_container_width=True):
            if check_alunas and "---" not in check_alunas:
                for aluna in check_alunas:
                    st.session_state.historico_geral.append({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Licao": lic_aula, 
                        "Dificuldades": selecionadas_dif, "Obs": obs_aula, "Instrutora": instr_sel
                    })
                st.balloons()
                st.success("Salvo com sucesso!")
            else:
                st.error("Não há aluna identificada para este horário.")
    else:
        st.warning("⚠️ Rodízio não encontrado.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência e Filtros")
    alu_an = st.selectbox("Selecione a Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    df = pd.DataFrame(st.session_state.historico_geral)
    
    if not df.empty:
        df_f = df[df["Aluna"] == alu_an]
        df_aulas = df_f[df_f["Tipo"] == "Aula"]

        if not df_aulas.empty:
            st.subheader("🤖 Diagnóstico IA")
            todas_dif = [d for sub in df_aulas["Dificuldades"].tolist() if isinstance(sub, list) for d in sub]
            if todas_dif:
                mais_c = pd.Series(todas_dif).value_counts().idxmax()
                st.warning(f"**Atenção:** A aluna apresenta dificuldades recorrentes em: **{mais_c}**.")
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Evolução Técnica**")
                if todas_dif: st.bar_chart(pd.Series(todas_dif).value_counts())
            with c2:
                st.write("**Frequência**")
                df_ch = df_f[df_f["Tipo"] == "Chamada"]
                if not df_ch.empty: st.bar_chart(df_ch["Status"].value_counts())

            st.divider()
            for _, row in df_aulas.sort_index(ascending=False).iterrows():
                with st.expander(f"Aula {row['Data']} - Lição {row.get('Licao', '')}"):
                    st.write(f"**Checklist:** {', '.join(row.get('Dificuldades', []))}")
                    st.info(f"**Obs:** {row.get('Obs', '')}")
