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
                HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": pt3},
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
        st.subheader("✅ Controle de Correções")
        c_sec1, c_sec2 = st.columns(2)
        with c_sec1:
            sec_resp = st.selectbox("Secretária Responsável:", SECRETARIAS)
            alu_sec = st.selectbox("Aluna:", alunas_lista)
            cat_sec = st.multiselect("Livro/Apostila:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila"])
        with c_sec2:
            status_corr = st.radio("Status da Atividade:", ["Realizada", "Não Realizada", "Devolvida para Correção"])
            detalhe_atv = st.text_input("Lições/Páginas (Ex: 1 a 5)")
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
    st.header("👩‍🏫 Registro de Aula (Coletivo ou Individual)")
    instr_sel = st.selectbox("👤 Identifique-se (Instrutora):", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        
        # BUSCA DA TURMA NO RODÍZIO
        turma_atendida = "---"
        for linha in st.session_state.calendario_anual[d_str]["tabela"]:
            if f"({instr_sel})" in str(linha.get(h_sel, "")):
                turma_atendida = linha["Turma"]
                break
        
        st.info(f"📍 Turma vinculada ao seu horário: **{turma_atendida}**")
        
        # SELEÇÃO DE ALUNAS (Grupo ou Individual)
        st.markdown("### 👥 Selecione as Alunas que participaram desta explicação:")
        alunas_da_turma = TURMAS.get(turma_atendida, []) if turma_atendida != "---" else []
        
        if alunas_da_turma:
            check_alunas = []
            c_alu1, c_alu2 = st.columns(2)
            for i, aluna in enumerate(alunas_da_turma):
                if (c_alu1 if i < len(alunas_da_turma)/2 else c_alu2).checkbox(aluna, value=True, key=f"aula_check_{aluna}"):
                    check_alunas.append(aluna)
        else:
            st.warning("Nenhuma turma localizada para você neste horário no rodízio.")
            check_alunas = []

        st.divider()
        lic_aula = st.selectbox("Lição/Volume abordado:", [str(i) for i in range(1, 41)] + ["MSA", "Hino"])
        
        st.markdown("**Checklist de Dificuldades (Geral para as selecionadas):**")
        dif_itens = ["Não estudou", "Estudou insatisfatório", "Sem vídeos", "Rítmica", "Nomes figuras", "Adentrando teclas", "Postura", "Punho", "Banqueta", "Falanges", "Unhas", "Dedos", "Pedal", "Pé esquerdo", "Metrônomo", "Clave sol", "Clave fá", "Articulação", "Respirações", "Dedilhado", "Sem dificuldades"]
        c1, c2 = st.columns(2)
        selecionadas_dif = []
        for i, d in enumerate(dif_itens):
            if (c1 if i < 10 else c2).checkbox(d, key=f"dif_aula_{i}"): selecionadas_dif.append(d)
        
        obs_aula = st.text_area("📝 Observações Gerais (O que foi ensinado hoje):")
        
        if st.button("💾 SALVAR REGISTRO", use_container_width=True):
            if check_alunas:
                for aluna in check_alunas:
                    st.session_state.historico_geral.append({
                        "Data": d_str, "Aluna": aluna, "Turma": turma_atendida, "Tipo": "Aula",
                        "Licao": lic_aula, "Dificuldades": selecionadas_dif, "Obs": obs_aula, "Instrutora": instr_sel
                    })
                st.balloons()
                st.success(f"Registro salvo para {len(check_alunas)} aluna(s)!")
            else:
                st.error("Selecione pelo menos uma aluna para salvar.")
    else:
        st.warning("⚠️ Rodízio não encontrado.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Análise de Desempenho")
    
    st.sidebar.subheader("📅 Período")
    tipo_p = st.sidebar.selectbox("Filtro:", ["Personalizado", "Diário", "Mensal", "Bimestral", "Semestral", "Anual"])
    fim = datetime.now()
    if tipo_p == "Diário": ini = fim
    elif tipo_p == "Mensal": ini = fim - timedelta(days=30)
    elif tipo_p == "Bimestral": ini = fim - timedelta(days=60)
    elif tipo_p == "Semestral": ini = fim - timedelta(days=180)
    elif tipo_p == "Anual": ini = fim - timedelta(days=365)
    else:
        ini = st.sidebar.date_input("Início:", value=fim - timedelta(days=30))
        fim = st.sidebar.date_input("Fim:", value=fim)

    alu_an = st.selectbox("Aluna:", sorted([a for l in TURMAS.values() for a in l]))
    df = pd.DataFrame(st.session_state.historico_geral)
    
    if not df.empty:
        df['Dt_Obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        mask = (df['Aluna'] == alu_an) & (df['Dt_Obj'] >= pd.Timestamp(ini)) & (df['Dt_Obj'] <= pd.Timestamp(fim))
        df_f = df.loc[mask]
        df_aulas = df_f[df_f["Tipo"] == "Aula"]

        st.subheader("🤖 Parecer IA")
        if not df_aulas.empty:
            todas_dif = [d for sub in df_aulas["Dificuldades"].tolist() if isinstance(sub, list) for d in sub]
            if todas_dif:
                mais_c = pd.Series(todas_dif).value_counts().idxmax()
                st.warning(f"**Análise:** Foco recorrente em '{mais_c}' no período.")
                st.info(f"**IA Sugere:** Revisar fundamentos de {mais_c} com a aluna.")

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Desempenho Técnico**")
            if not df_aulas.empty and todas_dif: st.bar_chart(pd.Series(todas_dif).value_counts())
        with c2:
            st.write("**Assiduidade**")
            df_ch = df_f[df_f["Tipo"] == "Chamada"]
            if not df_ch.empty: st.bar_chart(df_ch["Status"].value_counts())

        st.divider()
        st.subheader("📅 Histórico")
        for _, row in df_aulas.sort_index(ascending=False).iterrows():
            with st.expander(f"Aula {row['Data']} | Lição {row.get('Licao', '')}"):
                st.write(f"**Instrutora:** {row.get('Instrutora', '---')}")
                st.write(f"**Dificuldades:** {', '.join(row.get('Dificuldades', []))}")
                st.info(f"**Obs:** {row.get('Obs', '')}")
