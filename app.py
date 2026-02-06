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
if perfil == "🏠 Secretaria":
    tab_gerar, tab_chamada, tab_correcao = st.tabs(["🗓️ Planejamento", "📍 Chamada", "✅ Correção de Atividades"])

    # --- ABA 1: PLANEJAMENTO (RODÍZIO) ---
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
                    
                    # CORREÇÃO DO ERRO: Proteção com 'min()' para o index não estourar a lista
                    with c1:
                        pt_campos = []
                        for i in range(2, 5):
                            idx_seguro = min(i-2, len(PROFESSORAS_LISTA)-1)
                            sel = st.selectbox(f"Teoria H{i} ({d_str}):", PROFESSORAS_LISTA, index=idx_seguro, key=f"pt{i}_{d_str}")
                            pt_campos.append(sel)
                        pt2, pt3, pt4 = pt_campos
                        
                    with c2:
                        st_campos = []
                        for i in range(2, 5):
                            idx_seguro = min(i+1, len(PROFESSORAS_LISTA)-1)
                            sel = st.selectbox(f"Solfejo H{i} ({d_str}):", PROFESSORAS_LISTA, index=idx_seguro, key=f"st{i}_{d_str}")
                            st_campos.append(sel)
                        st2, st3, st4 = st_campos

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

    # --- ABA 3: CORREÇÃO DE ATIVIDADES (PEDAGÓGICO) ---
    with tab_correcao:
        st.subheader("✅ Correção e Análise Pedagógica")
        
        # 1. IDENTIFICAÇÃO DA SECRETARIA
        # Se você tiver uma lista de secretarias, coloque o nome da variável aqui
        # Caso contrário, deixei um campo de texto aberto para não inventar nomes
        sec_resp = st.text_input("Secretária Responsável:", key="sec_resp_manual")
        
        # Busca automática das alunas das suas turmas reais
        todas_alunas = sorted([aluna for sublist in TURMAS.values() for aluna in sublist])
        alu_corr = st.selectbox("Selecionar Aluna para Correção:", todas_alunas)

        # 2. BUSCA DAS ATIVIDADES LANÇADAS PELAS INSTRUTORAS (MSA, APOSTILA, MATÉRIA)
        lista_atividades = []
        if st.session_state.historico_geral:
            df_h = pd.DataFrame(st.session_state.historico_geral)
            # Filtra apenas as aulas reais da aluna selecionada
            df_a = df_h[(df_h["Aluna"] == alu_corr) & (df_h["Tipo"] == "Aula")]
            
            for _, row in df_a.iterrows():
                lista_atividades.append({
                    "label": f"{row['Data']} - {row.get('Materia', 'Aula')} (Prof. {row.get('Instrutora', '---')})",
                    "msa": row.get('Home_M', 'Não informado'),
                    "apostila": row.get('Home_A', 'Não informado'),
                    "materia": row.get('Materia', '---')
                })

        if not lista_atividades:
            st.warning(f"Nenhuma atividade de casa pendente encontrada para {alu_corr}.")
        else:
            selecao = st.selectbox("Qual atividade está sendo corrigida?", 
                                   lista_atividades, format_func=lambda x: x['label'])

            st.divider()
            
            # 3. EXIBIÇÃO DAS ATIVIDADES PARA CASA (O QUE A INSTRUTORA PASSOU)
            st.markdown(f"### 📋 Conferência: {selecao['materia']}")
            
            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.info(f"📖 **Atividade de MSA/Método:**\n\n{selecao['msa']}")
                status_msa = st.selectbox("Veredito MSA:", ["✅ Realizada", "❌ Não Realizada", "⚠️ Incompleta"], key="v_msa_sec")
            
            with c_info2:
                st.info(f"📝 **Atividade de Apostila:**\n\n{selecao['apostila']}")
                status_apo = st.selectbox("Veredito Apostila:", ["✅ Realizada", "❌ Não Realizada", "⚠️ Incompleta"], key="v_apo_sec")

            st.markdown("---")
            
            # 4. ANÁLISE DETALHADA POR ÁREAS (PARA A BANCA SEMESTRAL)
            st.markdown("### 🔍 Análise Técnica (Dificuldades por Área)")
            st.write("Preencha os detalhes para a análise pedagógica que ficará congelada:")
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                dif_postura = st.text_area("1. Postura (Mão, corpo, embocadura):", height=100)
                dif_tecnica = st.text_area("2. Técnica (Dedilhado, articulação):", height=100)
            with col_d2:
                dif_ritmo = st.text_area("3. Ritmo (Divisão, pulsação, MSA):", height=100)
                dif_teoria = st.text_area("4. Teoria (Conceitos, fórmulas):", height=100)

            # 5. RESUMO DA SECRETARIA E METAS
            st.markdown("### 🎯 Metas e Resumo para a Banca")
            resumo_sec = st.text_area("Resumo Pedagógico da Secretaria (Histórico Evolutivo):")
            proxima_meta = st.text_input("Dica/Meta para a próxima aula:")

            # 6. SALVAMENTO "CONGELADO"
            if st.button("💾 SALVAR E CONGELAR ANÁLISE", type="primary", use_container_width=True):
                analise_pedagogica = {
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Aluna": alu_corr,
                    "Referencia": selecao['label'],
                    "Secretaria": sec_resp,
                    "Resultados": {"MSA": status_msa, "Apostila": status_apo},
                    "Dificuldades": {
                        "Postura": dif_postura,
                        "Tecnica": dif_tecnica,
                        "Ritmo": dif_ritmo,
                        "Teoria": dif_teoria
                    },
                    "Resumo_Secretaria": resumo_sec,
                    "Meta": proxima_meta,
                    "Tipo": "Analise_Congelada_Banca"
                }
                st.session_state.correcoes_secretaria.append(analise_pedagogica)
                st.success(f"Análise técnica de {alu_corr} salva com sucesso!")
                
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















