import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from supabase import create_client, Client

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde - Gestão 2026", layout="wide", page_icon="🎼")

# --- CONEXÃO COM SUPABASE ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = init_supabase()

# --- FUNÇÕES DE BANCO DE DADOS ---
def db_get_calendario():
    try:
        res = supabase.table("calendario").select("*").execute()
        return {item['id']: item['escala'] for item in res.data}
    except: return {}

def db_save_calendario(d_str, escala):
    try:
        supabase.table("calendario").upsert({"id": d_str, "escala": escala}).execute()
    except Exception as e:
        st.error(f"Erro ao salvar rodízio: {e}")

def db_delete_calendario(d_str):
    supabase.table("calendario").delete().eq("id", d_str).execute()

def db_get_historico():
    try:
        res = supabase.table("historico_geral").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

def db_save_historico(dados):
    # Converte lista de dificuldades em texto para o banco
    if "Dificuldades" in dados and isinstance(dados["Dificuldades"], list):
        dados["Dificuldades"] = ", ".join(dados["Dificuldades"]) if dados["Dificuldades"] else "Nenhuma"
    
    try:
        supabase.table("historico_geral").insert(dados).execute()
        return True
    except Exception as e:
        if "42501" in str(e):
            st.error("🚨 BLOQUEIO DE SEGURANÇA: Vá ao painel do Supabase > Policies > historico_geral e ative a política de INSERT como 'true'.")
        else:
            st.error(f"Erro técnico: {e}")
        return False

# --- DADOS MESTRE ---
TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly C. V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia G. S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

def get_sabados_do_mes(ano, mes):
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    dias = cal.monthdatescalendar(ano, mes)
    return [dia for semana in dias for dia in semana if dia.weekday() == calendar.SATURDAY and dia.month == mes]

# --- INTERFACE ---
st.title("🎼 GEM Vila Verde - Gestão 2026")
perfil = st.sidebar.radio("Navegação:", ["🏠 Secretaria", "👩‍🏫 Professora", "📊 Analítico IA"])

calendario_anual = db_get_calendario()
historico_geral = db_get_historico()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================

# Definindo a variável que estava faltando para o sistema não travar
SECRETARIAS_LISTA = ["Ester", "Jéssica", "Larissa", "Lurdes", "Natasha", "Roseli"]

if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_correcao = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Correção de Atividades"])

    # --- ABA 1: PLANEJAMENTO (MANTIDA ORIGINAL) ---
    with tab_gerar:
        st.subheader("🗓️ Gestão de Rodízios")
        c_m1, c_m2 = st.columns(2)
        mes_ref = c_m1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
        ano_ref = c_m2.selectbox("Ano:", [2026, 2027], index=0)
        sabados = get_sabados_do_mes(ano_ref, mes_ref)
        
        for idx_sab, sab in enumerate(sabados):
            d_str = sab.strftime("%d/%m/%Y")
            with st.expander(f"📅 SÁBADO: {d_str}"):
                if d_str not in st.session_state.calendario_anual:
                    c1, c2 = st.columns(2)
                    with c1:
                        pt2, pt3, pt4 = [st.selectbox(f"Teoria H{i} ({d_str}):", PROFESSORAS_LISTA, index=i-2, key=f"pt{i}_{d_str}") for i in range(2, 5)]
                    with c2:
                        st2, st3, st4 = [st.selectbox(f"Solfejo H{i} ({d_str}):", PROFESSORAS_LISTA, index=i+1, key=f"st{i}_{d_str}") for i in range(2, 5)]
                    folgas = st.multiselect(f"Folgas ({d_str}):", PROFESSORAS_LISTA, key=f"f_{d_str}")

                    if st.button(f"🚀 Gerar Rodízio para {d_str}", key=f"btn_{d_str}"):
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
                                        f_rot = (i + (idx_sab * 3) + h_idx)
                                        instr_p = p_disp[f_rot % len(p_disp)] if p_disp else "Vago"
                                        idx_instr = PROFESSORAS_LISTA.index(instr_p) if instr_p in PROFESSORAS_LISTA else 0
                                        sala_fixa = ((idx_instr + idx_sab) % 7) + 1
                                        agenda[h_label] = f"🎹 SALA {sala_fixa} | Prática ({instr_p})"
                                escala_final.append(agenda)
                        st.session_state.calendario_anual[d_str] = escala_final
                        st.rerun()
                else:
                    st.table(pd.DataFrame(st.session_state.calendario_anual[d_str]))
                    if st.button(f"🗑️ Excluir Rodízio {d_str}", key=f"del_{d_str}"):
                        del st.session_state.calendario_anual[d_str]
                        st.rerun()

    # --- ABA 2: CHAMADA ---
    with tab_chamada:
        st.subheader("📍 Chamada Geral")
        data_ch_sel = st.selectbox("Selecione a Data:", [s.strftime("%d/%m/%Y") for s in sabados], key="data_ch_sec")
        
        # Botão para Presença Geral
        if st.button("✅ Marcar Todas como Presentes"):
            st.session_state["presenca_geral"] = True
        
        alunas_lista = [
            "Amanda S. - Pq do Carmo II", "Ana Marcela S. - Vila Verde", "Caroline C. - Vila Ré",
            "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá", "Gabrielly V. - Vila Verde",
            "Heloísa R. - Vila Verde", "Ingrid M. - Pq do Carmo II", "Júlia Cristina - União Vila Nova",
            "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá", "Mellina S. - Jd Lígia",
            "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", "Rebeca R. - Vila Ré",
            "Rebecca A. - Vila Verde", "Rebeka S. - Jd Lígia", "Sarah S. - Vila Verde",
            "Stephany O. - Vila Curuçá", "Vitória A. - Vila Verde", "Vitória Bella T. - Vila Verde"
        ]
        
        registros_ch = []
        for aluna in alunas_lista:
            c1, c2, c3 = st.columns([2, 2, 2])
            c1.write(f"**{aluna}**")
            
            # Valor padrão se "Presença Geral" for clicado
            index_padrao = 0 if st.session_state.get("presenca_geral", False) else 1 # P=0, F=1
            
            st_ch = c2.radio(f"Status {aluna}", ["P", "F", "J"], index=index_padrao, horizontal=True, key=f"ch_{aluna}_{data_ch_sel}", label_visibility="collapsed")
            
            motivo = ""
            if st_ch == "J":
                motivo = c3.text_input("Motivo da Justificativa", key=f"mot_{aluna}_{data_ch_sel}", placeholder="Ex: Doença")
            
            registros_ch.append({"Aluna": aluna, "Status": st_ch, "Motivo": motivo})

        if st.button("💾 SALVAR CHAMADA", type="primary", use_container_width=True):
            for r in registros_ch: 
                st.session_state.historico_geral.append({"Data": data_ch_sel, "Aluna": r["Aluna"], "Tipo": "Chamada", "Status": r["Status"], "Justificativa": r["Motivo"]})
            st.session_state["presenca_geral"] = False # Reseta o gatilho
            st.success("Chamada salva!")

    # --- ABA 3: CORREÇÃO E ANÁLISE PEDAGÓGICA ---
    with tab_correcao:
        st.subheader("✅ Controle de Lições e Relatório")
        
        col_id1, col_id2, col_id3 = st.columns(3)
        with col_id1:
            data_aula = st.date_input("Data da aula:", value=datetime.now())
        with col_id2:
            sec_resp = st.selectbox("Secretária:", ["Ester", "Jéssica", "Larissa", "Lourdes", "Natasha", "Roseli"])
        with col_id3:
            alu_corr = st.selectbox("Aluna:", alunas_lista)

        categoria = st.multiselect("Categoria:", ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"])

        st.divider()
        st.markdown("### 🔍 Detalhamento Técnico")
        c_tec1, c_tec2 = st.columns(2)
        with c_tec1:
            d_postura = st.text_input("Postura:", key="ped_pos", placeholder="Mão, arco, coluna...")
            d_tecnica = st.text_input("Técnica:", key="ped_tec", placeholder="Dedilhado, articulação...")
        with c_tec2:
            d_ritmo = st.text_input("Ritmo/Divisão:", key="ped_rit", placeholder="MSA, pulsação...")
            d_teoria = st.text_input("Teoria:", key="ped_teo", placeholder="Conceitos, leitura...")

        st.markdown("### 📝 Lições e Metas")
        l_realizada = st.text_area("Realizadas - sem pendência:")
        l_refazer = st.text_area("Realizada - devolvida para refazer:")
        l_nao_realizada = st.text_area("Não realizada:")
        
        resumo_banca = st.text_area("Observações (Histórico Evolutivo para Banca):")
        dica_meta = st.text_input("Dica específica para a próxima aula:")
        
        if st.button("💾 CONGELAR ANÁLISE COMPLETA", type="primary", use_container_width=True):
            if "correcoes_secretaria" not in st.session_state: st.session_state.correcoes_secretaria = []
            
            st.session_state.correcoes_secretaria.append({
                "Data": data_aula.strftime("%d/%m/%Y"),
                "Aluna": alu_corr,
                "Secretaria": sec_resp,
                "Categorias": categoria,
                "Dificuldades": {"Postura": d_postura, "Tecnica": d_tecnica, "Ritmo": d_ritmo, "Teoria": d_teoria},
                "Licoes": {"OK": l_realizada, "Refazer": l_refazer, "Pendentes": l_nao_realizada},
                "Resumo": resumo_banca,
                "Meta": dica_meta,
                "Tipo": "Analise_Banca"
            })
            st.success("Análise pedagógica congelada!")
            
# ========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "👩‍🏫 Professora":
    st.header("👩‍🏫 Diário de Classe")
    instr_sel = st.selectbox("👤 Professora:", PROFESSORAS_LISTA)
    data_p = st.date_input("Data:", value=datetime.now())
    d_str = data_p.strftime("%d/%m/%Y")

    if d_str in calendario_anual:
        h_sel = st.radio("⏰ Horário:", HORARIOS_LABELS, horizontal=True)
        atend = next((l for l in calendario_anual[d_str] if f"({instr_sel})" in str(l.get(h_sel, ""))), None)
        
        if atend:
            # Lógica de Matéria corrigida
            mat = "Teoria" if "Teoria" in atend[h_sel] else ("Solfejo" if "Solfejo" in atend[h_sel] else "Prática")
            st.warning(f"📍 Atendimento: {atend['Aluna'] if mat == 'Prática' else atend['Turma']} ({mat})")
            
            # Seleção de Alunas (Individual para Prática, Lista para Teoria/Solfejo)
            if mat == "Prática":
                check_alunas = [atend['Aluna']]
            else:
                st.write("---")
                st.write("**Chamada da Turma:**")
                turma_nome = atend['Turma']
                check_alunas = [a for a in TURMAS.get(turma_nome, []) if st.checkbox(a, value=True, key=f"chk_{a}")]
            
            selecionadas = []
            
            # FORMULÁRIO PEDAGÓGICO
            if mat == "Prática":
                st.subheader("🎹 Dificuldades Técnicas e Postura")
                lista_dif = [
                    "Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos",
                    "Dificuldade rítmica", "Nomes das figuras rítmicas", "Adentrando às teclas",
                    "Postura (costas/ombros/braços)", "Punho alto/baixo", "Não senta no centro",
                    "Quebrando falanges", "Unhas compridas", "Dedos arredondados",
                    "Pé no pedal expressão", "Movimentos pé esquerdo", "Uso do metrônomo",
                    "Estuda sem metrônomo", "Clave de sol", "Clave de fá", "Atividades apostila",
                    "Articulação ligada/semiligada", "Respirações", "Respirações sobre passagem",
                    "Recurso de dedilhado", "Nota de apoio", "Não apresentou dificuldades"
                ]
            elif mat == "Teoria": # CORRIGIDO: de 'else if' para 'elif'
                st.subheader("📚 Dificuldades Teóricas")
                lista_dif = [
                    "Não assistiu vídeos complementares", "Dificuldades em ler as notas na clave de sol", 
                    "Dificuldades em ler as notas na clave de fá", "Uso do metrônomo", 
                    "Estuda sem metrônomo", "Não realizou atividades", "Leitura rítmica", 
                    "Leitura métrica", "Solfejo (afinação)", "Movimento da mão", 
                    "Ordem das notas (asc/desc)", "Atividades da apostila",
                    "Não estudou nada", "Estudou insatisfatoriamente", "Não apresentou dificuldades"                                
                ]
            else: # Solfejo
                st.subheader("📚 Dificuldades Solfejo")
                lista_dif = [
                    "Não assistiu vídeos complementares", "Dificuldades em ler as notas na clave de sol", 
                    "Dificuldades em ler as notas na clave de fá", "Uso do metrônomo", 
                    "Estuda sem metrônomo", "Não realizou atividades", "Leitura rítmica", 
                    "Leitura métrica", "Solfejo (afinação)", "Movimento da mão", 
                    "Ordem das notas (asc/desc)", "Atividades da apostila",
                    "Não estudou nada", "Estudou insatisfatoriamente", "Não apresentou dificuldades"                                
                ]

            # Exibição em duas colunas para facilitar a marcação
            cols = st.columns(2)
            for i, d in enumerate(lista_dif):
                if cols[i % 2].checkbox(d, key=f"f_{i}_{d_str}"): 
                    selecionadas.append(d)
            
            st.write("---")
            l_hj = st.text_input("📖 Lição dada hoje (Ex: Hino 10, Método p. 20):")
            p_m = st.text_input("🏠 Para casa (Método):")
            p_a = st.text_input("🏠 Para casa (Apostila/Outros):")
            obs_f = st.text_area("✍️ Relato Pedagógico (O que observar na próxima aula):")

            if st.button("💾 SALVAR REGISTRO DE AULA", type="primary"):
                if not selecionadas:
                    st.error("Por favor, selecione ao menos uma opção nas dificuldades (ou 'Não apresentou dificuldades').")
                else:
                    sucesso = True
                    # Salva o registro para cada aluna selecionada (importante para turmas)
                    for aluna in check_alunas:
                        res = db_save_historico({
                            "Data": d_str, 
                            "Aluna": aluna, 
                            "Tipo": "Aula", 
                            "Materia": mat,
                            "Licao": l_hj, 
                            "Dificuldades": ", ".join(selecionadas), 
                            "Obs": obs_f,
                            "Home_M": p_m, 
                            "Home_A": p_a, 
                            "Instrutora": instr_sel
                        })
                        if not res: sucesso = False
                    
                    if sucesso:
                        st.success(f"Aula de {mat} registrada com sucesso para {len(check_alunas)} aluna(s)!")
                        st.balloons()
        else:
            st.info(f"Sra. {instr_sel}, não encontramos aula agendada para este horário hoje.")
    else:
        st.error("Cronograma de rodízio não localizado para esta data.")

# ==========================================
#              MÓDULO ANALÍTICO
# ==========================================
elif perfil == "📊 Analítico IA":
    st.header("📊 Inteligência Pedagógica - Vila Verde")
    from PIL import Image, ImageDraw, ImageFont
    import io

    if "analises_fixas_salvas" not in st.session_state:
        st.session_state.analises_fixas_salvas = {}
    
    if not historico_geral:
        st.info("Aguardando registros no histórico para iniciar as análises.")
    else:
        df_geral = pd.DataFrame(historico_geral)
        todas_alunas = sorted(df_geral["Aluna"].unique())
        
        c1, c2, c3 = st.columns([2, 2, 2])
        aluna_sel = c1.selectbox("Selecione a Aluna:", todas_alunas)
        periodo_tipo = c2.selectbox("Tipo de Período:", ["Diário", "Mensal", "Bimestral", "Semestral", "Anual"])
        data_ini_ref = c3.date_input("Data Inicial da Análise:") 

        id_analise = f"{aluna_sel}_{data_ini_ref}_{periodo_tipo}"
        
        from datetime import timedelta
        df_geral['dt_obj'] = pd.to_datetime(df_geral['Data'], format='%d/%m/%Y').dt.date
        delta_dias = {"Diário":0, "Mensal":30, "Bimestral":60, "Semestral":180, "Anual":365}[periodo_tipo]
        d_fim = data_ini_ref + timedelta(days=delta_dias)
        
        df_f = df_geral[(df_geral["Aluna"] == aluna_sel) & (df_geral["dt_obj"] >= data_ini_ref) & (df_geral["dt_obj"] <= d_fim)]

        if not df_f.empty:
            df_aulas = df_f[df_f["Tipo"] == "Aula"].copy()
            df_ch = df_f[df_f["Tipo"] == "Chamada"]

            # --- 1. GRÁFICOS DETALHADOS ---
            st.subheader("📈 Diagnóstico de Performance")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if not df_aulas.empty:
                    def calc_nota(txt):
                        if "Sem dificuldades" in str(txt): return 100
                        return max(0, 100 - (len(str(txt).split(",")) * 12))
                    df_aulas['Nota'] = df_aulas['Dificuldades'].apply(calc_nota)
                    st.write("**Aproveitamento por Matéria (%)**")
                    st.bar_chart(df_aulas.groupby('Materia')['Nota'].mean())
            with col_g2:
                if not df_ch.empty:
                    st.write("**Assiduidade (Presenças vs Faltas)**")
                    st.bar_chart(df_ch["Status"].value_counts())

            st.divider()

            # --- 2. RELATÓRIO PEDAGÓGICO CONGELADO ---
            if id_analise in st.session_state.analises_fixas_salvas:
                d = st.session_state.analises_fixas_salvas[id_analise]
                
                with st.container(border=True):
                    st.markdown(f"## 📋 Ficha de Avaliação: {aluna_sel}")
                    st.caption(f"Período: {data_ini_ref.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')} | Ref: {periodo_tipo}")
                    
                    # Resumo da Secretaria
                    st.markdown("### 🏢 Resumo Secretaria")
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Aulas Totais", d['qtd_aulas'])
                    s2.metric("Frequência", f"{d['freq']:.1f}%")
                    s3.metric("Status Licao", d['ultima_licao'])

                    st.markdown("---")
                    
                    # Detalhamento por Área
                    st.markdown("### 🎹 Análise Pedagógica Detalhada")
                    t1, t2 = st.columns(2)
                    with t1:
                        st.error(f"**🔹 POSTURA & TÉCNICA**\n\n{d['difs_tecnica']}")
                        st.warning(f"**🔹 RITMO & TEORIA**\n\n{d['difs_ritmo']}")
                    with t2:
                        st.info(f"**💡 DICAS PARA PRÓXIMA AULA**\n\n{d['dicas']}")
                        st.success(f"**🎯 FOCO BANCA SEMESTRAL**\n\n{d['banca']}")
                
                # --- GERADOR DE IMAGEM PNG PROFISSIONAL ---
                img = Image.new('RGB', (1200, 1000), color=(255, 255, 255))
                draw = ImageDraw.Draw(img)
                
                texto_png = [
                    "GEM VILA VERDE - RELATÓRIO PEDAGÓGICO COMPLETO",
                    f"ALUNA: {aluna_sel} | TIPO: {periodo_tipo}",
                    f"DATA: {data_ini_ref.strftime('%d/%m/%Y')} - {d_fim.strftime('%d/%m/%Y')}",
                    "="*50,
                    f"AULAS REALIZADAS: {d['qtd_aulas']} | FREQUÊNCIA: {d['freq']:.1f}%",
                    f"ÚLTIMA LIÇÃO: {d['ultima_licao']}",
                    "-"*50,
                    "[ANÁLISE DE POSTURA E TÉCNICA]",
                    f"{d['difs_tecnica']}",
                    "",
                    "[ANÁLISE DE RITMO E TEORIA]",
                    f"{d['difs_ritmo']}",
                    "",
                    "[ORIENTAÇÕES PARA A PRÓXIMA AULA]",
                    f"{d['dicas']}",
                    "",
                    "[REQUISITOS PARA BANCA SEMESTRAL]",
                    f"{d['banca']}",
                    "="*50,
                    f"Documento Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                ]
                
                curr_y = 50
                for line in texto_png:
                    draw.text((60, curr_y), line, fill=(0, 0, 0))
                    curr_y += 38

                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.download_button(f"📥 Exportar PNG Detalhado", buf.getvalue(), f"Analise_Completa_{aluna_sel}.png", "image/png")

                if st.button("🗑️ Gerar Novo Diagnóstico (Limpar Anterior)"):
                    del st.session_state.analises_fixas_salvas[id_analise]
                    st.rerun()

            else:
                if st.button("✨ EXECUTAR DIAGNÓSTICO PEDAGÓGICO"):
                    def filtrar_dif(palavras):
                        achadas = [d for d in df_aulas['Dificuldades'].astype(str) if any(p in d.lower() for p in palavras)]
                        return "- " + "\n- ".join(set(achadas)) if achadas else "Nenhuma pendência crítica registrada nesta área."

                    # Lógica de Dicas Automáticas baseada nas dificuldades
                    difs_raw = " ".join(df_aulas['Dificuldades'].astype(str)).lower()
                    dica_ia = "Reforçar o estudo diário com mãos separadas."
                    if "metrônomo" in difs_raw: dica_ia = "Obrigatório uso de metrônomo em todas as lições, começando em 40 BPM."
                    if "postura" in difs_raw or "punho" in difs_raw: dica_ia = "Aplicar exercícios de relaxamento de ombros e correção de altura do banco."

                    st.session_state.analises_fixas_salvas[id_analise] = {
                        "qtd_aulas": len(df_aulas),
                        "freq": (len(df_ch[df_ch["Status"] == "P"]) / len(df_ch) * 100) if len(df_ch) > 0 else 0,
                        "ultima_licao": df_aulas.iloc[0]['Licao'] if not df_aulas.empty else "N/A",
                        "difs_tecnica": filtrar_dif(["postura", "punho", "dedo", "falange", "articulação", "pedal", "tecla"]),
                        "difs_ritmo": filtrar_dif(["metrônomo", "rítmica", "clave", "solfejo", "teoria", "figura", "leitura"]),
                        "dicas": dica_ia,
                        "banca": "Para a banca, a aluna precisa estabilizar o tempo rítmico e manter o punho nivelado, sem quebrar as falanges."
                    }
                    st.rerun()

            st.divider()
            # --- 3. LOGS DE AUDITORIA (SECRETARIA E PROFESSORA) ---
            st.subheader("📂 Histórico de Logs para Auditoria")
            with st.expander("Ver Logs das Aulas (Detalhado)"):
                st.dataframe(df_aulas[['Data', 'Materia', 'Licao', 'Dificuldades', 'Instrutora', 'Obs']], use_container_width=True)
            
            with st.expander("Ver Logs de Frequência (Secretaria)"):
                st.table(df_ch[['Data', 'Status']])
       
        else:
            st.warning("Não há registros suficientes para gerar um relatório detalhado desta aluna no período.")






















