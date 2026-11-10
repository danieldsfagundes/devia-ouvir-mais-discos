import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import os
import requests

st.set_page_config(
    page_title="devia ouvir mais discos", 
    page_icon="🎶", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada com a estética de vinil (Dark Mode)
st.markdown("""
    <style>
    .main {
        background-color: #121212;
        color: #e0e0e0;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 8px;
    }
    div[data-testid="stMetricValue"] {
        color: #f59e0b;
    }
    .vinyl-card {
        background-color: #1a1a1a;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #2a2a2a;
        margin-bottom: 10px;
    }
    .spotify-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #1db954;
        color: #ffffff !important;
        font-weight: 700;
        font-size: 14px;
        padding: 10px 20px;
        border-radius: 25px;
        text-decoration: none !important;
        margin-top: 15px;
        transition: background-color 0.2s ease, transform 0.1s ease;
        box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
    }
    .spotify-btn:hover {
        background-color: #1ed760;
        transform: scale(1.02);
    }
    .spotify-icon {
        margin-right: 8px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: #ffffff; font-weight: 800;'>devia ouvir mais discos</h1>", unsafe_allow_html=True)
st.caption("Ouvindo, explorando e avaliando discos em toda a sua arte.")

MAPA_ISO = {
    "Brasil": "br", "Brazil": "br",
    "Estados Unidos": "us", "Eua": "us", "United States": "us",
    "Reino Unido": "gb", "Inglaterra": "gb", "United Kingdom": "gb",
    "França": "fr", "France": "fr",
    "Argentina": "ar",
    "Cuba": "cu",
    "México": "mx", "Mexico": "mx",
    "Chile": "cl",
    "Colômbia": "co", "Colombia": "co",
    "Panamá": "pa", "Panama": "pa",
    "Puerto Rico": "pr",
    "República Dominicana": "do",
    "Perú": "pe", "Peru": "pe",
    "Costa Rica": "cr",
    "Venezuela": "ve",
    "Bolívia": "bo", "Bolivia": "bo",
    "Uruguay": "uy", "Uruguai": "uy",
    "Guatemala": "gt",
    "El Salvador": "sv",
    "Paraguay": "py", "Paraguai": "py",
    "Ecuador": "ec", "Equador": "ec",
    "Nicaragua": "ni", "Nicarágua": "ni",
    "Honduras": "hn",
    "España": "es", "Espanha": "es", "Spain": "es",
    "Itália": "it", "Italia": "it", "Italy": "it",
    "Portugal": "pt",
    "Japão": "jp", "Japan": "jp",
    "Jamaica": "jm",
    "Canadá": "ca", "Canada": "ca",
    "Alemanha": "de", "Germany": "de"
}

def obter_html_bandeira(pais):
    if not isinstance(pais, str):
        return str(pais)
    p_limpo = pais.strip().title()
    primeiro_pais = p_limpo.split(',')[0].strip()
    iso = MAPA_ISO.get(primeiro_pais, "un")
    url_bandeira = f"https://flagcdn.com/16x12/{iso}.png"
    return f'<img src="{url_bandeira}" style="width: 16px; height: 12px; vertical-align: middle; margin-right: 2px; border-radius: 2px;" alt="{pais}">'

def render_estrelas(num):
    try:
        n = int(float(num)) if pd.notna(num) and str(num).strip() != '' and str(num).lower() != 'nan' else 0
    except:
        n = 0
    n = max(0, min(5, n))
    if n == 0:
        return "⚪ Não avaliado"
    return "⭐" * n + "☆" * (5 - n)

def carregar_dados_frescos():
    if not os.path.exists("albums.csv"):
        return pd.DataFrame()
    df = pd.read_csv("albums.csv", on_bad_lines='skip', dtype=str)
    
    colunas_obrigatorias = {
        'Cover_Rating': '0',
        'Total_Tracks': '10',
        'Liked_Tracks': '0',
        'Favorite_Track': '',
        'My_Review': '',
        'Country': 'Brasil',
        'Spotify_Link': 'Spotify',
        'Colecao': 'Não',
        'Released': '1975',
        'Status': 'Pendente'
    }
    for col, val_padrao in colunas_obrigatorias.items():
        if col not in df.columns:
            df[col] = val_padrao

    df = df.drop_duplicates(subset=['Artist', 'Album'], keep='first').reset_index(drop=True)
    
    df['Cover_Rating'] = pd.to_numeric(df['Cover_Rating'], errors='coerce').fillna(0).astype(int)
    df['Total_Tracks'] = pd.to_numeric(df['Total_Tracks'], errors='coerce').fillna(10).astype(int)
    df['Liked_Tracks'] = pd.to_numeric(df['Liked_Tracks'], errors='coerce').fillna(0).astype(int)
    df['Released'] = pd.to_numeric(df['Released'], errors='coerce').fillna(1975).astype(int)
    df['Colecao'] = df['Colecao'].fillna('Não').astype(str)
    df['Status'] = df['Status'].fillna('Pendente').astype(str)
    df['Favorite_Track'] = df['Favorite_Track'].fillna('').astype(str)
    df['Favorite_Track'] = df['Favorite_Track'].apply(lambda x: '' if x.lower() == 'nan' else x)
    
    prop = df['Liked_Tracks'] / df['Total_Tracks'].replace(0, 1)
    df['Nota_Calculada'] = (prop * 5.0 * 0.70) + (df['Cover_Rating'] * 0.30)
    
    return df

@st.cache_data
def buscar_capa_album(artist, album):
    try:
        termo = f"{artist} {album}"
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(termo)}&entity=album&limit=1"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                artwork = data['results'][0]['artworkUrl100']
                return artwork.replace('100x100b.jpg', '600x600bb.jpg').replace('100x100', '600x600')
    except Exception:
        pass
    return None

def obter_link_spotify(row):
    link_custom = str(row.get('Spotify_Link', '')).strip()
    if link_custom.startswith('http'):
        return link_custom
    query_sp = urllib.parse.quote(f"{row['Artist']} {row['Album']}")
    return f"https://open.spotify.com/search/{query_sp}"

df_albums = carregar_dados_frescos()

if df_albums.empty:
    st.stop()

if 'filtro_aba' not in st.session_state:
    st.session_state.filtro_aba = "álbum do dia"
if 'ignorar_pendente' not in st.session_state:
    st.session_state.ignorar_pendente = False

# MENU LATERAL COM A ORDEM SOLICITADA
st.sidebar.markdown("### 🎛️ menu")
abas_disponiveis = [
    "álbum do dia", 
    "histórico", 
    "minha coleção", 
    "avaliar depois", 
    "não avaliados", 
    "estatísticas", 
    "inserir manualmente"
]

try:
    default_idx = abas_disponiveis.index(st.session_state.filtro_aba)
except:
    default_idx = 0

aba = st.sidebar.radio(
    "navegar", 
    abas_disponiveis,
    index=default_idx,
    key="menu_navegacao_radio"
)

if aba != st.session_state.filtro_aba:
    st.session_state.filtro_aba = aba

# 1. ABA: ÁLBUM DO DIA
if st.session_state.filtro_aba == "álbum do dia":
    today_str = str(datetime.date.today())
    
    pendentes = df_albums[df_albums['Status'].str.strip().str.lower() == 'pendente']
    
    album_alvo = None
    if not pendentes.empty and not st.session_state.ignorar_pendente:
        album_alvo = pendentes.iloc[0]
        st.markdown(f"""
            <div class="vinyl-card" style="border: 1px solid #f59e0b; margin-bottom: 15px;">
                <b style="color: #f59e0b; font-size: 16px;">⚠️ Álbum Pendente de Avaliação</b><br>
                <span style="color: #ccc; font-size: 14px;">Você tem um álbum pendente ({album_alvo['Album']} - {album_alvo['Artist']}). O que deseja fazer com ele?</span>
            </div>
        """, unsafe_allow_html=True)
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            if st.button("🎵 Avaliar agora"):
                st.session_state.ignorar_pendente = False
                st.rerun()
        with c_p2:
            if st.button("⏳ Avaliar depois"):
                df_all = pd.read_csv("albums.csv", dtype=str)
                m_idx = df_all[(df_all['Album'] == str(album_alvo['Album'])) & (df_all['Artist'] == str(album_alvo['Artist']))].index
                if len(m_idx) > 0:
                    df_all.loc[m_idx[0], 'Status'] = 'Avaliar Depois'
                    df_all.to_csv("albums.csv", index=False)
                st.session_state.ignorar_pendente = True
                st.success("Movido para 'Avaliar depois'!")
                st.rerun()
        with c_p3:
            if st.button("❌ Não quero avaliar"):
                df_all = pd.read_csv("albums.csv", dtype=str)
                m_idx = df_all[(df_all['Album'] == str(album_alvo['Album'])) & (df_all['Artist'] == str(album_alvo['Artist']))].index
                if len(m_idx) > 0:
                    df_all.loc[m_idx[0], 'Status'] = 'Não Avaliado'
                    df_all.to_csv("albums.csv", index=False)
                st.session_state.ignorar_pendente = True
                st.success("Movido para 'Não avaliados'!")
                st.rerun()
        st.markdown("---")
    
    if album_alvo is None or (not pendentes.empty and st.session_state.ignorar_pendente):
        today_seed = int(datetime.date.today().strftime("%Y%m%d"))
        disponiveis_hoje = df_albums[df_albums['Status'].str.strip().str.lower().isin(['pendente', 'avaliado'])]
        if disponiveis_hoje.empty:
            disponiveis_hoje = df_albums
        album_alvo = disponiveis_hoje.sample(1, random_state=today_seed).iloc[0]
    
    st.markdown("### 💿 álbum do dia")
    
    col_pop1, col_pop2 = st.columns([1, 2])
    
    with col_pop1:
        st.markdown(f"### {album_alvo['Album']}")
        st.markdown(f"**Artista:** {album_alvo['Artist']}")
        
        pais_nome = str(album_alvo.get('Country', 'Brasil')).strip()
        html_bandeira = obter_html_bandeira(pais_nome)
        st.markdown(f"**País:** {html_bandeira} {pais_nome}", unsafe_allow_html=True)
        
        st.markdown(f"**Lançamento:** 📅 {int(album_alvo['Released']) if pd.notna(album_alvo['Released']) else ''}")
        
        capa_url = buscar_capa_album(album_alvo['Artist'], album_alvo['Album'])
        if capa_url:
            st.image(capa_url, caption=album_alvo['Album'], width=280)
        else:
            st.info("💿 Capa indisponível no momento")
        
        url_spotify = obter_link_spotify(album_alvo)
        st.markdown(f"""
            <a href="{url_spotify}" target="_blank" class="spotify-btn">
                <span class="spotify-icon">🎧</span> ouvir álbum completo
            </a>
        """, unsafe_allow_html=True)
        
    with col_pop2:
        st.markdown("#### 🎵 registre sua audição")
        st.markdown(f"**Nota atual da capa:** {render_estrelas(album_alvo.get('Cover_Rating', 0))}")
        st.markdown("alterar nota da capa (1 a 5)")
        feedback_estrelas = st.feedback("stars", key="pop_cov_feedback")
        
        tot_p = st.number_input("total de músicas", 1, 30, int(float(album_alvo.get('Total_Tracks', 10))), key="pop_tot")
        lik_p = st.number_input("músicas que gostou", 0, tot_p, int(float(album_alvo.get('Liked_Tracks', 0))), key="pop_lik")
        
        # Seleção de Coleção
        colecao_atual = str(album_alvo.get('Colecao', 'Não')).strip().capitalize()
        idx_col_pop = 0 if colecao_atual in ['Sim', 'S', 'True', 'Yes'] else 1
        pop_colecao = st.selectbox("minha coleção", ["Sim", "Não"], index=idx_col_pop, key="pop_colecao_select")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("salvar audição", type="primary"):
                df_all = pd.read_csv("albums.csv", dtype=str)
                m_idx = df_all[(df_all['Album'] == str(album_alvo['Album'])) & (df_all['Artist'] == str(album_alvo['Artist']))].index
                if len(m_idx) > 0:
                    idx_s = m_idx[0]
                    if feedback_estrelas is not None:
                        df_all.loc[idx_s, 'Cover_Rating'] = str(int(feedback_estrelas + 1))
                    df_all.loc[idx_s, 'Total_Tracks'] = str(int(tot_p))
                    df_all.loc[idx_s, 'Liked_Tracks'] = str(int(lik_p))
                    df_all.loc[idx_s, 'Colecao'] = str(pop_colecao)
                    df_all.loc[idx_s, 'Status'] = 'Avaliado'
                    df_all.to_csv("albums.csv", index=False)
                st.session_state.ignorar_pendente = False
                st.success("audição registrada com sucesso!")
                st.rerun()
        with col_b2:
            if st.button("⏳ avaliar depois"):
                df_all = pd.read_csv("albums.csv", dtype=str)
                m_idx = df_all[(df_all['Album'] == str(album_alvo['Album'])) & (df_all['Artist'] == str(album_alvo['Artist']))].index
                if len(m_idx) > 0:
                    df_all.loc[m_idx[0], 'Status'] = 'Avaliar Depois'
                    df_all.to_csv("albums.csv", index=False)
                st.success("Movido para 'Avaliar depois'!")
                st.rerun()
        with col_b3:
            if st.button("❌ não quero avaliar"):
                df_all = pd.read_csv("albums.csv", dtype=str)
                m_idx = df_all[(df_all['Album'] == str(album_alvo['Album'])) & (df_all['Artist'] == str(album_alvo['Artist']))].index
                if len(m_idx) > 0:
                    df_all.loc[m_idx[0], 'Status'] = 'Não Avaliado'
                    df_all.to_csv("albums.csv", index=False)
                st.success("Movido para 'Não avaliados'!")
                st.rerun()

# 2. ABA: HISTÓRICO
elif st.session_state.filtro_aba == "histórico":
    st.markdown("### 📚 histórico")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        artistas_disponiveis = ["todos"] + sorted(df_albums['Artist'].dropna().astype(str).unique().tolist())
        filtro_artista = st.selectbox("filtrar por artista", artistas_disponiveis)
    with col_f2:
        paises_disponiveis = ["todos"] + sorted(df_albums['Country'].dropna().astype(str).unique().tolist())
        filtro_pais = st.selectbox("filtrar por país", paises_disponiveis)
    with col_f3:
        anos_disponiveis = sorted(df_albums['Released'].dropna().unique().tolist())
        filtro_ano = st.selectbox("filtrar por ano", ["todos"] + [str(int(a)) for a in anos_disponiveis])
    with col_f4:
        pesquisa_livre = st.text_input("pesquisa (disco ou artista)", placeholder="digite para buscar...")

    df_filtrado = df_albums.copy()
    if filtro_artista != "todos":
        df_filtrado = df_filtrado[df_filtrado['Artist'] == filtro_artista]
    if filtro_pais != "todos":
        df_filtrado = df_filtrado[df_filtrado['Country'] == filtro_pais]
    if filtro_ano != "todos":
        df_filtrado = df_filtrado[df_filtrado['Released'].astype(int).astype(str) == filtro_ano]
    if pesquisa_livre:
        termo = pesquisa_livre.strip().lower()
        mask = df_filtrado['Album'].astype(str).str.lower().str.contains(termo, na=False) | \
               df_filtrado['Artist'].astype(str).str.lower().str.contains(termo, na=False)
        df_filtrado = df_filtrado[mask]

    df_filtrado = df_filtrado.sort_values(by='Nota_Calculada', ascending=False).reset_index(drop=True)
    st.caption(f"exibindo {len(df_filtrado)} discos no acervo.")
    
    lista_discos_hist = df_filtrado.head(24).to_dict('records')
    for row_idx in range(0, len(lista_discos_hist), 4):
        cols = st.columns(4)
        for col_idx in range(4):
            flat_idx = row_idx + col_idx
            if flat_idx < len(lista_discos_hist):
                r = lista_discos_hist[flat_idx]
                with cols[col_idx]:
                    pais_card = str(r.get('Country', 'Brasil')).strip()
                    ano_val = int(r['Released']) if pd.notna(r['Released']) else ''
                    c_val = int(float(r['Cover_Rating'])) if pd.notna(r['Cover_Rating']) and str(r['Cover_Rating']).strip() != '' else 0
                    n_val = float(r['Nota_Calculada'])
                    str_nota = f"{n_val:.1f}/5" if c_val > 0 else "Não avaliado"
                    html_bandeira = obter_html_bandeira(pais_card)
                    
                    st.markdown(f"""
                        <div class="vinyl-card">
                            <b style="color: #ffffff; font-size: 16px;">{r['Album']}</b><br>
                            <span style="color: #a0a0a0; font-size: 14px;">{r['Artist']}</span><br><br>
                            <span style="color: #ccc; font-size: 13px;">{html_bandeira} {pais_card}</span><br>
                            <span style="color: #ccc; font-size: 13px;">📅 {ano_val}</span>
                            <hr style="border: 0.5px solid #333; margin: 10px 0;">
                            <span style="color: #1db954; font-size: 12px;">Capa: {c_val}/5 | ⭐ Nota Final: {str_nota}</span>
                        </div>
                    """, unsafe_allow_html=True)

# 3. ABA: MINHA COLEÇÃO
elif st.session_state.filtro_aba == "minha coleção":
    st.markdown("### 💽 minha coleção de vinis")
    df_colecao = df_albums[df_albums['Colecao'].str.strip().str.lower().isin(['sim', 's', 'yes', 'true', '1'])].copy()
    df_colecao = df_colecao.sort_values(by='Nota_Calculada', ascending=False).reset_index(drop=True)
    
    st.caption(f"exibindo {len(df_colecao)} discos cadastrados na sua coleção.")
    if df_colecao.empty:
        st.info("💡 Nenhum disco marcado como 'Sim' na coleção ainda.")
    else:
        lista_discos = df_colecao.head(24).to_dict('records')
        for row_idx in range(0, len(lista_discos), 4):
            cols = st.columns(4)
            for col_idx in range(4):
                flat_idx = row_idx + col_idx
                if flat_idx < len(lista_discos):
                    r = lista_discos[flat_idx]
                    with cols[col_idx]:
                        pais_card = str(r.get('Country', 'Brasil')).strip()
                        ano_val = int(r['Released']) if pd.notna(r['Released']) else ''
                        c_val = int(float(r['Cover_Rating'])) if pd.notna(r['Cover_Rating']) and str(r['Cover_Rating']).strip() != '' else 0
                        n_val = float(r['Nota_Calculada'])
                        str_nota = f"{n_val:.1f}/5" if c_val > 0 else "Não avaliado"
                        html_bandeira = obter_html_bandeira(pais_card)
                        
                        st.markdown(f"""
                            <div class="vinyl-card">
                                <b style="color: #ffffff; font-size: 16px;">{r['Album']}</b><br>
                                <span style="color: #a0a0a0; font-size: 14px;">{r['Artist']}</span><br><br>
                                <span style="color: #ccc; font-size: 13px;">{html_bandeira} {pais_card}</span><br>
                                <span style="color: #ccc; font-size: 13px;">📅 {ano_val}</span>
                                <hr style="border: 0.5px solid #333; margin: 10px 0;">
                                <span style="color: #1db954; font-size: 12px;">Capa: {c_val}/5 | ⭐ Nota Final: {str_nota}</span>
                            </div>
                        """, unsafe_allow_html=True)

# 4. ABA: AVALIAR DEPOIS
elif st.session_state.filtro_aba == "avaliar depois":
    st.markdown("### ⏳ fila de espera (avaliar depois)")
    df_depois = df_albums[df_albums['Status'].str.strip().str.lower() == 'avaliar depois'].copy()
    st.caption(f"exibindo {len(df_depois)} discos guardados para ouvir e avaliar depois.")
    
    if df_depois.empty:
        st.info("💡 Nenhum disco na fila 'Avaliar depois' no momento.")
    else:
        for idx, r in df_depois.iterrows():
            st.markdown(f"""
                <div class="vinyl-card">
                    <b style="color: #ffffff; font-size: 16px;">{r['Album']}</b> — <span style="color: #a0a0a0; font-size: 14px;">{r['Artist']}</span><br>
                    <span style="color: #ccc; font-size: 13px;">📅 {int(r['Released']) if pd.notna(r['Released']) else ''} | {r.get('Country', 'Brasil')}</span>
                </div>
            """, unsafe_allow_html=True)
            col_ad1, col_ad2 = st.columns(2)
            with col_ad1:
                if st.button("🎵 Avaliar agora", key=f"btn_ev_dep_{idx}0"):
                    df_all = pd.read_csv("albums.csv", dtype=str)
                    m_idx = df_all[(df_all['Album'] == str(r['Album'])) & (df_all['Artist'] == str(r['Artist']))].index
                    if len(m_idx) > 0:
                        df_all.loc[m_idx[0], 'Status'] = 'Pendente'
                        df_all.to_csv("albums.csv", index=False)
                    st.session_state.filtro_aba = "álbum do dia"
                    st.rerun()
            with col_ad2:
                if st.button("❌ Não quero avaliar", key=f"btn_ev_dep_{idx}1"):
                    df_all = pd.read_csv("albums.csv", dtype=str)
                    m_idx = df_all[(df_all['Album'] == str(r['Album'])) & (df_all['Artist'] == str(r['Artist']))].index
                    if len(m_idx) > 0:
                        df_all.loc[m_idx[0], 'Status'] = 'Não Avaliado'
                        df_all.to_csv("albums.csv", index=False)
                    st.rerun()

# 5. ABA: NÃO AVALIADOS
elif st.session_state.filtro_aba == "não avaliados":
    st.markdown("### ❌ discos não avaliados (descartados)")
    df_nao = df_albums[df_albums['Status'].str.strip().str.lower() == 'não avaliado'].copy()
    st.caption(f"exibindo {len(df_nao)} discos que você optou por não avaliar.")
    
    if df_nao.empty:
        st.info("💡 Nenhum disco descartado.")
    else:
        for idx, r in df_nao.iterrows():
            st.markdown(f"""
                <div class="vinyl-card">
                    <b style="color: #ffffff; font-size: 16px;">{r['Album']}</b> — <span style="color: #a0a0a0; font-size: 14px;">{r['Artist']}</span>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Voltar para Avaliar Depois", key=f"btn_nao_ev_{idx}"):
                df_all = pd.read_csv("albums.csv", dtype=str)
                m_idx = df_all[(df_all['Album'] == str(r['Album'])) & (df_all['Artist'] == str(r['Artist']))].index
                if len(m_idx) > 0:
                    df_all.loc[m_idx[0], 'Status'] = 'Avaliar Depois'
                    df_all.to_csv("albums.csv", index=False)
                st.rerun()

# 6. ABA: ESTATÍSTICAS
elif st.session_state.filtro_aba == "estatísticas":
    st.subheader("📊 estatísticas da sua coleção")
    c_s1, c_s2, c_s3 = st.columns(3)
    with c_s1:
        st.metric("total de discos catalogados", len(df_albums))
    with c_s2:
        media_aproveitamento = (df_albums['Liked_Tracks'].astype(float) / df_albums['Total_Tracks'].astype(float).replace(0, 1)).mean() * 100
        st.metric("aproveitamento médio de faixas", f"{media_aproveitamento:.1f}%")
    with c_s3:
        st.metric("média de nota das capas", f"{df_albums['Cover_Rating'].astype(float).mean():.1f} / 5")
    
    st.markdown("---")
    st.markdown("### 📥 backup dos dados")
    st.caption("baixe uma cópia atualizada da sua planilha de discos (`albums.csv`) para o seu computador.")
    if os.path.exists("albums.csv"):
        with open("albums.csv", "rb") as f:
            st.download_button(
                label="📥 baixar arquivo albums.csv",
                data=f,
                file_name="albums.csv",
                mime="text/csv"
            )

# 7. ABA: INSERIR MANUALMENTE
elif st.session_state.filtro_aba == "inserir manualmente":
    st.subheader("➕ inserir novo disco manualmente")
    with st.form("form_manual"):
        m_artista = st.text_input("artista")
        m_pais = st.text_input("país", value="Brasil")
        m_album = st.text_input("nome do álbum")
        m_ano = st.number_input("ano de lançamento", min_value=1900, max_value=2026, value=1975)
        m_spotify = st.text_input("link do álbum no Spotify", value="Spotify")
        m_colecao = st.selectbox("minha coleção", ["Sim", "Não"])
        
        st.markdown("nota da capa (1 a 5)")
        fb_man = st.feedback("stars", key="manual_stars")
        m_capa = (fb_man + 1) if fb_man is not None else 0
        
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            m_tot = st.number_input("total de músicas", 1, 30, 10)
        with c_m2:
            m_lik = st.number_input("músicas que gostou", 0, m_tot, 0)
            m_fav = st.text_input("música favorita")
            
        if st.form_submit_button("adicionar à coleção"):
            df_all = pd.read_csv("albums.csv", dtype=str)
            novo_registro = pd.DataFrame([{
                'Artist': str(m_artista),
                'Country': str(m_pais),
                'Album': str(m_album),
                'Released': str(int(m_ano)),
                'Spotify_Link': str(m_spotify),
                'Colecao': str(m_colecao),
                'Cover_Rating': str(int(m_capa)),
                'Total_Tracks': str(int(m_tot)),
                'Liked_Tracks': str(int(m_lik)),
                'Favorite_Track': str(m_fav),
                'My_Review': '',
                'Status': 'Pendente'
            }])
            df_atualizado = pd.concat([df_all, novo_registro], ignore_index=True)
            df_atualizado.to_csv("albums.csv", index=False)
            st.success(f"'{m_album}' adicionado com sucesso!")