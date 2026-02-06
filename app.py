import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import base64
import calendar

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

# --- FUNÇÕES AUXILIARES ---
def get_sabados_do_mes(ano, mes):
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    dias = cal.monthdatescalendar(ano, mes)
    sabados = []
    for semana in dias:
        for dia in semana:
            if dia.weekday() == calendar.SATURDAY and dia.month == mes:
                sabados.append(dia)
    return sabados

def verificar_status_dia(data_str):
    realizado = any(item['Data'] == data_str for item in st.session_state.historico_geral)
    return "✅ REALIZADO" if realizado else "⏳ PENDENTE"

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_controle = st.tabs(["🗓️ Planejamento Mensal", "📍 Chamada", "✅ Correção de Atividades"])

    with tab_gerar:
        st.subheader("🗓️ Gestão de Rodízios Mensais")
        c_m1, c_m2 = st.columns(2)
        mes_ref = c_m1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano_ref = c_m2.selectbox("Ano:", [2026, 2027], index=0)
        
        sabados = get_sabados_do_mes(ano_ref, mes_ref)
        
        for idx_sab, sab in enumerate(sabados):
            d_str = sab.strftime("%d/%m/%Y")
            status = verificar_status_dia(d_str)
            
            with st.expander(f"📅 SÁBADO: {d_str} - {status}"):
                if d_str not in st.session_state.calendario_anual:
                    st.warning(f"Rodízio de {d_str} pendente.")
                    c1, c2 = st.columns(2)
                    with c1:
                        pt2 = st.selectbox(f"Teoria H2 ({d_str}):", PROFESSORAS_LISTA, index=0, key=f"pt2_{d_str}")
                        pt3 = st.selectbox(f"Teoria H3 ({d_str}):", PROFESSORAS_LISTA, index=1, key=f"pt3_{d_str}")
                        pt4 = st.selectbox(f"Teoria H4 ({d_str}):", PROFESSORAS_LISTA, index=2, key=f"pt4_{d_str}")
                    with c2:
                        st2 = st.selectbox(f"Solfejo H2 ({d_str}):", PROFESSORAS_LISTA, index=3, key=f"st2_{d_str}")
                        st3 = st.selectbox(f"Solfejo H3 ({d_str}):", PROFESSORAS_LISTA, index=4, key=f"st3_{d_str}")
                        st4 = st.selectbox(f"Solfejo H4 ({d_str}):", PROFESSORAS_LISTA, index=5, key=f"st4_{d_str}")
                    folgas = st.multiselect(f"Folgas ({d_str}):", PROFESSORAS_LISTA, key=f"f_{d_str}")

                    if st.button(f"🚀 Gerar Rodízio para {d_str}", key=f"btn_{d_str}"):
                        escala_final = []
                        fluxo = {
                            HORARIOS_LABELS[1]: {"Teo": "Turma 1", "Sol": "Turma 2", "Pra": "Turma 3", "ITeo": pt2, "ISol": st2},
                            HORARIOS_LABELS[2]: {"Teo": "Turma 2", "Sol": "Turma 3", "Pra": "Turma 1", "ITeo": pt3, "ISol": st3},
                            HORARIOS_LABELS[3]: {"Teo": "Turma 3", "Sol": "Turma 1", "Pra": "Turma 2", "ITeo": pt4, "ISol": st4}
                        }
                        
                        # LOGICA DE RODIZIO REFORÇADA: O salto muda a cada sábado do mês (idx_sab)
                        for t_nome, alunas in TURMAS.items():
                            for i, aluna in enumerate(alunas):
                                agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
                                for h_idx in [1, 2, 3]:
                                    h_label = HORARIOS_LABELS[h_idx]; cfg = fluxo[h_label]
                                    if cfg["Teo"] == t_nome: agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['ITeo']})"
                                    elif cfg["Sol"] == t_nome: agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['ISol']})"
                                    else:
                                        p_disp = [p for p in PROFESSORAS_LISTA if p not in [cfg["ITeo"], cfg["ISol"]] + folgas]
                                        # O cálculo da sala e professora agora depende da posição da aluna + índice do sábado + horário
                                        # Isso garante que a cada semana a rotação seja diferente
                                        salto = (i + idx_sab + h_idx) 
                                        sala_p = (salto % 7) + 1
                                        instr_p = p_disp[salto % len(p_disp)] if p_disp else "Vago"
                                        agenda[h_label] = f"🎹 SALA {sala_p} | Prática ({instr_p})"
                                escala_final.append(agenda)
                        st.session_state.calendario_anual[d_str] = escala_final
                        st.rerun()
                else:
                    st.success(f"Rodízio Ativo")
                    st.table(pd.DataFrame(st.session_state.calendario_anual[d_str]))
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        del st.session_state.calendario_anual[d_str]
                        st.rerun()

    with tab_chamada:
        st.subheader("📍 Chamada")
        data_ch_sel = st.selectbox("Selecione o Sábado:", [s.strftime("%d/%m/%Y") for s in sabados])
        alunas_lista = sorted([a for l in TURMAS.values() for a in l])
        
        if st.button("✅ Marcar Todas como Presente"):
            for aluna in alunas_lista: st.session_state[f"ch_{aluna}_{data_ch_sel}"] = "Presente"

        chamada_temp = []
        for aluna in alunas_lista:
            c1, c2, c3 = st.columns([2, 3, 2])
            c1.write(f"👤 **{aluna}**")
            key_ch = f"ch_{aluna}_{data_ch_sel}"
            if key_ch not in st.session_state: st.session_state[key_ch] = "Presente"
            status = c2.radio(f"Status_{aluna}", ["Presente", "Falta", "Justificada"], key=key_ch, horizontal=True, label_visibility="collapsed")
            motivo = c3.text_input("Motivo:", key=f"mot_{aluna}_{data_ch_sel}") if status == "Justificada" else ""
            chamada_temp.append({"Aluna": aluna, "Status": status, "Motivo": motivo})

        if st.button("💾 Salvar Chamada do Dia", use_container_width=True):
            for r in chamada_temp:
                st.session_state.historico_geral.append({"Data": data_ch_sel, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Motivo": r["Motivo"]})
            st.success("Chamada salva com sucesso!")

    with tab_controle:
        st.subheader("✅ Controle de Correções")
        c_sec1, c_sec2 = st.columns(2)
        with c_sec1:
            sec_resp = st.selectbox("Secretária Responsável:", SECRETARIAS)
            alu_sec = st.selectbox("Aluna:", alunas_lista)
            cat_sec = st.multiselect("Livro:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila"])
        with c_sec2:
            status_corr = st.radio("Status:", ["Realizada", "Não Realizada", "Devolvida para Correção"], horizontal=True)
            detalhe_atv = st.text_input("Lições/Páginas")
            obs_sec = st.text_area("Observações")
            
        if st.button("💾 Salvar Registro de Correção", use_container_width=True):
            st.session_state.controle_licoes.append({
                "Data": datetime.now().strftime("%d/%m/%Y"), "Aluna": alu_sec, "Secretaria": sec_resp,
                "Status": status_corr, "Atividade": detalhe_atv, "Categoria": cat_sec, "Obs": obs_sec
            })
            st.success(f"Registrado por {sec_resp}!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Sua Identificação (Instrutora):", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in st.session_state.calendario_anual:
        h_sel = st.radio("⏰ Selecione o Horário:", HORARIOS_LABELS, horizontal=True)
        
        atend_info = None
        for linha in st.session_state.calendario_anual[d_str]:
            if f"({instr_sel})" in str(linha.get(h_sel, "")):
                atend_info = linha
                break

        if atend_info:
            tipo_atendimento = atend_info[h_sel]
            if "Teoria" in tipo_atendimento or "Solfejo" in tipo_atendimento:
                st.info(f"📚 AULA EM GRUPO | Turma: {atend_info['Turma']} | {tipo_atendimento}")
                alunas_grupo = TURMAS[atend_info['Turma']]
                check_alunas = []
                cols = st.columns(4)
                for i, aluna in enumerate(alunas_grupo):
                    if cols[i%4].checkbox(aluna, value=True, key=f"p_chk_{aluna}"): check_alunas.append(aluna)
            else:
                st.error(f"🎹 AULA INDIVIDUAL | Aluna: {atend_info['Aluna']} | {tipo_atendimento}")
                check_alunas = [atend_info['Aluna']]

            st.divider()
            lic = st.selectbox("Lição/Volume:", [str(i) for i in range(1, 41)] + ["MSA", "Hino"])
            dif_itens = ["Rítmica", "Postura", "Punho", "Dedos", "Metrônomo", "Clave Fá", "Dedilhado", "Sem dificuldades"]
            c1, c2, c3 = st.columns(3)
            selecionadas = []
            for i, d in enumerate(dif_itens):
                target = c1 if i < 3 else (c2 if i < 6 else c3)
                if target.checkbox(d, key=f"dif_{i}"): selecionadas.append(d)
                
            obs = st.text_area("Relato de Evolução:")
            
            if st.button("💾 SALVAR REGISTRO", use_container_width=True):
                for aluna in check_alunas:
                    st.session_state.historico_geral.append({
                        "Data": d_str, "Aluna": aluna, "Tipo": "Aula", "Licao": lic, 
                        "Dificuldades": selecionadas, "Obs": obs, "Instrutora": instr_sel
                    })
                st.balloons()
                st.success("Aula registrada!")
        else:
            st.warning("Você não possui escala registrada para este horário.")
    else:
        st.warning("Rodízio não encontrado para esta data.")

# ==========================================
#              MÓDULO ANALÍTICO IA
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência de Dados e Histórico")
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
                st.warning(f"**Alerta Técnico:** A aluna tem maior dificuldade em: **{mais_c}**.")
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Resumo de Dificuldades**")
                if todas_dif: st.bar_chart(pd.Series(todas_dif).value_counts())
            with c2:
                st.write("**Frequência de Aulas**")
                df_ch = df_f[df_f["Tipo"] == "Chamada"]
                if not df_ch.empty: st.bar_chart(df_ch["Status"].value_counts())

            st.divider()
            st.write("**Linha do Tempo de Evolução:**")
            for _, row in df_aulas.sort_index(ascending=False).iterrows():
                with st.expander(f"Data: {row['Data']} | Lição: {row.get('Licao', '')}"):
                    st.write(f"**Instrutora:** {row['Instrutora']}")
                    st.write(f"**Checklist:** {', '.join(row.get('Dificuldades', []))}")
                    st.info(f"**Evolução:** {row.get('Obs', '')}")
    else:
        st.info("Nenhum dado registrado para análise até o momento.")
