import streamlit as st

# --- BANCO DE DADOS DE NOMES (OFICIAL) ---
SECRETARIAS = ["Selecione...", "Ester", "Jéssica", "Larissa", "Lourdes", "Natasha"]
ALUNAS = [
    "Amanda S. - Parque do Carmo II", "Ana Marcela S. - Vila Verde", "Caroline C. - Vila Ré",
    "Elisa F. - Vila Verde", "Emilly O. - Vila Curuçá Velha", "Gabrielly V. - Vila Verde",
    "Heloísa R. - Vila Verde", "Ingrid M. - Parque do Carmo II", "Júlia Cristina - União de Vila Nova",
    "Júlia S. - Vila Verde", "Julya O. - Vila Curuçá Velha", "Mellina S. - Jardim Lígia",
    "Micaelle S. - Vila Verde", "Raquel L. - Vila Verde", "Rebeca R. - Vila Ré",
    "Rebecca A. - Vila Verde", "Rebeka S. - Jardim Lígia", "Sarah S. - Vila Verde",
    "Stephany O. - Vila Curuçá Velha", "Vitória A. - Vila Verde", "Vitória Bella T. - Vila Verde"
]
CATEGORIAS = ["MSA (verde)", "MSA (preto)", "Caderno de pauta", "Apostila", "Folhas avulsas (teoria)"]
LICOES_NUM = [str(i) for i in range(1, 41)] + ["Outro"]

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GEM Vila Verde", layout="wide")

# --- MENU LATERAL ---
st.sidebar.title("🎼 GEM Vila Verde")
perfil = st.sidebar.selectbox("Selecione seu Perfil:", ["Selecione...", "Secretaria", "Professora"], key="nav_perfil")

# Placeholder para limpar a tela ao trocar de perfil
container_principal = st.empty()

# ==========================================
#              MÓDULO SECRETARIA
# ==========================================
if perfil == "Secretaria":
    with container_principal.container():
        st.title("📋 Módulo da Secretaria")
        
        # Sub-menu da Secretaria
        tarefa_sec = st.radio("Selecione a tarefa:", ["Lista de Presença", "Controle de Lições"], horizontal=True)
        st.divider()

        if tarefa_sec == "Lista de Presença":
            st.subheader("📍 Chamada do Dia")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                data_presenca = st.date_input("Data da Aula", format="DD/MM/YYYY", key="dt_pres")
                sec_resp_pres = st.selectbox("Secretária responsável:", SECRETARIAS, key="sec_pres")
            with col_p2:
                presentes = st.multiselect("Marque as alunas presentes:", ALUNAS, key="lista_pres")
            
            if st.button("Finalizar Chamada"):
                if sec_resp_pres == "Selecione...":
                    st.error("Selecione a secretária!")
                else:
                    st.success(f"Presença de {len(presentes)} alunas registrada!")

        elif tarefa_sec == "Controle de Lições":
            st.subheader("✅ Correção de Atividades")
            
            # Seção 1
            c1, c2 = st.columns(2)
            with c1:
                st.selectbox("Secretária *", SECRETARIAS, key="sec_lic")
                st.selectbox("Aluna *", ALUNAS, key="aluna_lic")
            with c2:
                st.date_input("Data da aula", format="DD/MM/YYYY", key="dt_lic")
                st.multiselect("Categoria", CATEGORIAS, key="cat_lic")
            
            st.divider()
            
        # --- SEÇÃO 2: CONFERÊNCIA DE ATIVIDADES (MAIS PRÁTICO) ---
        st.divider()
        st.subheader("✅ Conferência de Atividades")
        st.caption("Verifique os itens abaixo conforme o que foi passado pela professora:")

        # Simulação das tarefas que viriam do banco de dados (Passadas pela professora)
        tarefas_da_semana = [
            {"tipo": "Prática", "descricao": "Lição 15 - Volume 1"},
            {"tipo": "Teoria", "descricao": "Módulo 3 - Exercício 5"},
            {"tipo": "Apostila", "descricao": "Página 10"}
        ]

        # Criando uma linha para cada tarefa com botões de status
        for i, tarefa in enumerate(tarefas_da_semana):
            with st.expander(f"📌 {tarefa['tipo']}: {tarefa['descricao']}", expanded=True):
                col_status, col_obs = st.columns([2, 3])
                
                with col_status:
                    # Status prático por cliques
                    st.radio(
                        "Resultado:",
                        ["Realizada (OK)", "Refazer (Pendência)", "Não Realizada"],
                        key=f"status_{i}",
                        horizontal=False
                    )
                
                with col_obs:
                    # Observação específica para cada item
                    st.text_input("Observação específica:", placeholder="Ex: Teve dúvida no compasso...", key=f"obs_item_{i}")

        st.divider()
        st.subheader("📝 Observações Gerais")
        observacoes_finais = st.text_area("Notas adicionais da secretaria:", key="sec_obs_final")

        if st.button("Finalizar e Salvar Controle"):
            st.balloons()
            st.success("Conferência finalizada com sucesso!")

# ==========================================
#              MÓDULO PROFESSORA
# ==========================================
elif perfil == "Professora":
    with container_principal.container():
        st.title("🎹 Avaliação Técnica")
        
        col_prof1, col_prof2 = st.columns(2)
        with col_prof1:
            aluna_p = st.selectbox("Selecione a Aluna:", ALUNAS, key="p_aluna")
        with col_prof2:
            frente = st.radio("Frente:", ["Prática", "Teoria", "Solfejo"], horizontal=True, key="p_frente")

        st.divider()

        # --- PRÁTICA ---
        if frente == "Prática":
            st.selectbox("Lição/Volume *", LICOES_NUM, key="p_lic_v")
            st.write("**Dificuldades Prática:**")
            diff_p = st.multiselect("Selecione as dificuldades:", [
                "Não estudou nada", "Estudou insatisfatoriamente", "Postura", "Quebrando falanges", 
                "Punho alto/baixo", "Metrônomo", "Clave de Sol", "Clave de Fá", "Dedilhado"
            ]) # Adicionar todas as 25 aqui conforme o código anterior
            
        # --- TEORIA/SOLFEJO ---
        else:
            st.selectbox("Lição/Volume *", LICOES_NUM, key="t_lic_v")
            st.multiselect("Dificuldades:", [
                "Vídeos complementares", "Leitura rítmica", "Leitura métrica", 
                "Afinação", "Movimento da mão", "Metrônomo"
            ])

        st.text_area("Observações Técnicas", key="p_obs")
        st.divider()
        st.write("**Lição de Casa:**")
        st.selectbox("Lição Volume Prática *", LICOES_NUM, key="p_casa_v")
        st.text_input("Lição Apostila", key="p_casa_apo")

        if st.button("Finalizar Avaliação"):
            st.success("Avaliação técnica concluída!")