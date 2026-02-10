import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÃO SUPABASE ---
SUPABASE_URL = "https://ixaqtoyqoianumczsjai.supabase.co"
SUPABASE_KEY = "sb_publishable_HwYONu26I0AzTR96yoy-Zg_nVxTlJD1"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- DADOS MESTRE ---
PROFESSORAS_LISTA = ["Cassia", "Elaine", "Ester", "Luciene", "Patricia", "Roberta", "Téta", "Vanessa", "Flávia", "Kamyla"]
# Mapeia cada professora a uma sala de 1 a 10 permanentemente
MAPA_SALAS_FIXAS = {prof: i + 1 for i, prof in enumerate(PROFESSORAS_LISTA)}

TURMAS = {
    "Turma 1": ["Rebecca A.", "Amanda S.", "Ingrid M.", "Rebeka S.", "Mellina S.", "Rebeca R.", "Caroline C."],
    "Turma 2": ["Vitória A.", "Elisa F.", "Sarah S.", "Gabrielly V.", "Emily O.", "Julya O.", "Stephany O."],
    "Turma 3": ["Heloísa R.", "Ana Marcela S.", "Vitória Bella T.", "Júlia S.", "Micaelle S.", "Raquel L.", "Júlia Cristina"]
}

HORARIOS_LABELS = [
    "08h45 às 09h30 (1ª Aula - Igreja)", 
    "09h35 às 10h05 (2ª Aula)", 
    "10h10 às 10h40 (3ª Aula)", 
    "10h45 às 11h15 (4ª Aula)"
]

st.title("🎼 Gerador de Rodízio Sem Conflitos")

# --- SELEÇÃO DE DATA ---
c1, c2 = st.columns(2)
mes = c1.selectbox("Mês:", list(range(1, 13)), index=datetime.now().month - 1)
ano = 2026
cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
sabados = [d for sem in cal.monthdatescalendar(ano, mes) for d in sem if d.weekday() == calendar.SATURDAY and d.month == mes]
d_str = st.selectbox("Data do Rodízio:", [s.strftime("%d/%m/%Y") for s in sabados])

# --- INTERFACE DE CONFIGURAÇÃO ---
st.markdown("### 🛠️ Configuração de Coletivas e Folgas")
col1, col2 = st.columns(2)
with col1:
    pt2 = st.selectbox("Teoria H2 (T1):", PROFESSORAS_LISTA, index=0)
    pt3 = st.selectbox("Teoria H3 (T2):", PROFESSORAS_LISTA, index=1)
    pt4 = st.selectbox("Teoria H4 (T3):", PROFESSORAS_LISTA, index=2)
with col2:
    ps2 = st.selectbox("Solfejo H2 (T2):", PROFESSORAS_LISTA, index=3)
    ps3 = st.selectbox("Solfejo H3 (T3):", PROFESSORAS_LISTA, index=4)
    ps4 = st.selectbox("Solfejo H4 (T1):", PROFESSORAS_LISTA, index=5)

folgas = st.multiselect("Professoras de Folga:", PROFESSORAS_LISTA)

if st.button("🚀 Gerar Rodízio Oficial"):
    escala_final = []
    
    # Definição de quem está ocupado em cada horário
    fluxo_coletivo = {
        HORARIOS_LABELS[1]: {"Teo": ("Turma 1", pt2), "Sol": ("Turma 2", ps2)},
        HORARIOS_LABELS[2]: {"Teo": ("Turma 2", pt3), "Sol": ("Turma 3", ps3)},
        HORARIOS_LABELS[3]: {"Teo": ("Turma 3", pt4), "Sol": ("Turma 1", ps4)}
    }

    # Processar cada horário individualmente para garantir a separação de salas
    for t_nome, alunas in TURMAS.items():
        for i, aluna in enumerate(alunas):
            agenda = {"Aluna": aluna, "Turma": t_nome, HORARIOS_LABELS[0]: "⛪ IGREJA"}
            
            for h_idx in [1, 2, 3]:
                h_label = HORARIOS_LABELS[h_idx]
                cfg = fluxo_coletivo[h_label]
                
                # 1. Verificamos se a aluna está em aula coletiva
                if cfg["Teo"][0] == t_nome:
                    agenda[h_label] = f"📚 SALA 8 | Teoria ({cfg['Teo'][1]})"
                elif cfg["Sol"][0] == t_nome:
                    agenda[h_label] = f"🔊 SALA 9 | Solfejo ({cfg['Sol'][1]})"
                else:
                    # 2. ALUNA EM AULA PRÁTICA:
                    # Identificar professoras disponíveis (que não estão na Teoria, Solfejo ou Folga)
                    prof_ocupadas_agora = [cfg["Teo"][1], cfg["Sol"][1]] + folgas
                    prof_disponiveis = [p for p in PROFESSORAS_LISTA if p not in prof_ocupadas_agora]
                    
                    # Seleciona a professora usando o índice da aluna (i) 
                    # para garantir que cada aluna pegue uma prof diferente
                    if i < len(prof_disponiveis):
                        instrutora = prof_disponiveis[i]
                        # A sala é buscada no MAPA FIXO. Como as professoras são únicas, a sala será única.
                        num_sala = MAPA_SALAS_FIXAS[instrutora]
                        agenda[h_label] = f"🎹 SALA {num_sala} | Prática ({instrutora})"
                    else:
                        agenda[h_label] = "⚠️ Sem Prof. Disponível"
            
            escala_final.append(agenda)

    # SALVAR NO SUPABASE
    try:
        supabase.table("calendario").upsert({"id": d_str, "escala": escala_final}).execute()
        st.success(f"Rodízio de {d_str} salvo com sucesso! As salas 1 a 7 agora são exclusivas por professora.")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- EXIBIÇÃO ---
st.divider()
try:
    res = supabase.table("calendario").select("*").eq("id", d_str).execute()
    if res.data:
        st.subheader(f"📅 Escala Atual: {d_str}")
        df = pd.DataFrame(res.data[0]['escala'])
        st.dataframe(df, use_container_width=True)
        
        # Botão para deletar
        if st.button("🗑️ Limpar Escala desta Data"):
            supabase.table("calendario").delete().eq("id", d_str).execute()
            st.rerun()
except:
    st.info("Nenhuma escala salva para esta data.")
