import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import requests

# COLE AQUI A URL GERADA NO GOOGLE APPS SCRIPT
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzCSBNBbDg7U4VGGYa6eriu-73tDgFAYHhU_tKaiRI3wKQr6epknsttqK38-mSiOSMtkQ/exec"

st.set_page_config(
    page_title="devia ouvir mais discos", 
    page_icon="🎶", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        margin-bottom: 5px;
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
    "Brasil": "br", "Brazil": "br", "Estados Unidos": "us", "Eua": "us", "United States": "us",
    "Reino Unido": "gb", "Inglaterra": "gb", "United Kingdom": "gb", "França": "fr", "France": "fr",
    "Argentina": "ar", "Cuba": "cu", "México": "mx", "Mexico": "mx", "Chile": "cl",
    "Colômbia": "co", "Colombia": "co", "Panamá": "pa", "Puerto Rico": "pr",
    "República Dominicana": "do", "Perú": "pe", "Peru": "pe", "Costa Rica": "cr",
    "Venezuela": "ve", "Bolívia": "bo", "Uruguay": "uy", "Uruguai": "uy", "Guatemala": "gt",
    "El Salvador": "sv", "Paraguay": "py", "Ecuador": "ec", "Nicaragua": "ni",
    "Honduras": "hn", "España": "es", "Espanha": "es", "Spain": "es", "Itália": "it",
    "Italia": "it", "Italy": "it", "Portugal": "pt", "Japão": "jp", "Japan": "jp",
    "Jamaica": "jm", "Canadá": "ca", "Alemanha": "de"
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

def carregar_dados_online():
    if "COLE_SUA_URL" in APPS_SCRIPT_URL or not APPS_SCRIPT_URL.startswith("http"):
        st.error("⚠️ Cole a URL do Google Apps Script na variável APPS_SCRIPT_URL no início do código.")
        st.stop()
        
    try:
        response = requests.get(APPS_SCRIPT_URL, timeout=15)
        response.raise_for_status()
        dados_json = response.json()
        df = pd.DataFrame(dados_json)
    except Exception as e:
        st.error(f"Erro ao ler dados do Google Sheets: {e}")
        st.stop()

    if df.empty:
        return pd.DataFrame()

    df = df.astype(str)
    colunas_obrigatorias = {
        'Artist': '', 'Country': 'Brasil', 'Album': '', 'Released': '1975',
        'Cover_Rating': '0', 'Total_Tracks': '10', 'Liked_Tracks': '0',
        'Favorite_Track': '', 'My_Review': '', 'Spotify_Link': 'Spotify',
        'Status': 'Pendente', 'Colecao': 'Não', 'Ultima_Audicao': ''
    }
    for col, val_padrao in colunas_obrigatorias.items():
        if col not in df.columns:
            df[col] = val_padrao
        df[col] = df[col].replace({'nan': val_padrao, 'None': val_padrao, '': val_padrao})

    df = df.drop_duplicates(subset=['Artist', 'Album'], keep='first').reset_index(drop=True)
    df['Cover_Rating'] = pd.to_numeric(df['Cover_Rating'], errors='coerce').fillna(0).astype(int)
    df['Total_Tracks'] = pd.to_numeric(df['Total_Tracks'], errors='coerce').fillna(10).astype(int)
    df['Liked_Tracks'] = pd.to_numeric(df['Liked_Tracks'], errors='coerce').fillna(0).astype(int)
    df['Released'] = pd.to_numeric(df['Released'], errors='coerce').fillna(1975).astype(int)
    
    df['Ultima_Audicao'] = df['Ultima_Audicao'].apply(lambda x: str(x)[:10] if len(str(x)) >= 10 and '-' in str(x) else str(x).strip())
    df.loc[df['Cover_Rating'] > 0, 'Status'] = 'Avaliado'
    
    prop = df['Liked_Tracks'] / df['Total_Tracks'].replace(0, 1)
    df['Nota_Calculada'] = (prop * 5.0 * 0.70) + (df['Cover_Rating'] * 0.30)
    return df

def salvar_dados_online(df_novo):
    cols_ordem = [
        'Artist', 'Country', 'Album', 'Released', 'Cover_Rating', 
        'Total_Tracks', 'Liked_Tracks', 'Favorite_Track', 'My_Review', 
        'Spotify_Link', 'Status', 'Colecao', 'Ultima_Audicao'
    ]
    df_export = df_novo[cols_ordem].copy()
    for col in cols_ordem:
        df_export[col] = df_export[col].astype(str).replace({'nan': '', 'None': ''})
        
    payload = {
        "action": "update_all",
        "data": df_export.to_dict(orient="records")
    }
    try:
        with st.spinner("Sincronizando com o Google Sheets..."):
            res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=20)
            res.raise_for_status()
        if 'df_cache' in st.session_state:
            del st.session_state.df_cache
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

def obter_df():
    if 'df_cache' not in st.session_state:
        st.session_state.df_cache = carregar_dados_online()
    return st.session_state.df_cache

def aplicar_filtros_comuns(df_base):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        artistas_disponiveis = ["todos"] + sorted(df_base['Artist'].dropna().astype(str).unique().tolist())
        f_art = st.selectbox("filtrar por artista", artistas_disponiveis, key=f"art_{st.session_state.filtro_aba}")
    with c2:
        paises_disponiveis = ["todos"] + sorted(df_base['Country'].dropna().astype(str).unique().tolist())
        f_pais = st.selectbox("filtrar por país", paises_disponiveis, key=f"pais_{st.session_state.filtro_aba}")
    with c3:
        anos_disponiveis = sorted(df_base['Released'].dropna().unique().tolist())
        f_ano = st.selectbox("filtrar por ano", ["todos"] + [str(int(a)) for a in anos_disponiveis], key=f"ano_{st.session_state.filtro_aba}")
    with c4:
        f_nota = st.selectbox("filtrar por nota final", ["todos", "1+", "2+", "3+", "4+", "5"], key=f"nota_{st.session_state.filtro_aba}")
    with c5:
        f_pesquisa = st.text_input("pesquisa livre", placeholder="disco ou artista...", key=f"pesq_{st.session_state.filtro_aba}")

    df_f = df_base.copy()
    if f_art != "todos":
        df_f = df_f[df_f['Artist'] == f_art]
    if f_pais != "todos":
        df_f = df_f[df_f['Country'] == f_pais]
    if f_ano != "todos":
        df_f = df_f[df_f['Released'].astype(int).astype(str) == f_ano]
    if f_nota != "todos":
        val_nota = float(f_nota[0])
        if f_nota == "5":
            df_f = df_f[(df_f['Cover_Rating'] > 0) & (df_f['Nota_Calculada'] >= 5.0)]
        else:
            df_f = df_f[(df_f['Cover_Rating'] > 0) & (df_f['Nota_Calculada'] >= val_nota) & (df_f['Nota_Calculada'] < val_nota + 1.0)]
    if f_pesquisa:
        termo = f_pesquisa.strip().lower()
        mask = df_f['Album'].astype(str).str.lower().str.contains(termo, na=False) | \
               df_f['Artist'].astype(str).str.lower().str.contains(termo, na=False)
        df_f = df_f[mask]
        
    return df_f.sort_values(by='Nota_Calculada', ascending=False).reset_index(drop=True)

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

df_albums = obter_df()

if df_albums.empty:
    st.warning("A planilha parece estar vazia.")
    st.stop()

if 'filtro_aba' not in st.session_state:
    st.session_state.filtro_aba = "álbum do dia"

st.sidebar.markdown("### 🎛️ menu")
abas_disponiveis = [
    "álbum do dia", "minhas avaliações", "minha coleção", 
    "avaliar depois", "não avaliados", "estatísticas", "inserir manualmente"
]

try:
    default_idx = abas_disponiveis.index(st.session_state.filtro_aba)
except:
    default_idx = 0

aba = st.sidebar.radio("navegar", abas_disponiveis, index=default_idx, key="menu_navegacao_radio")
if aba != st.session_state.filtro_aba:
    st.session_state.filtro_aba = aba

if st.sidebar.button("🔄 recarregar planilha"):
    if 'df_cache' in st.session_state:
        del st.session_state.df_cache
    st.rerun()

# 1. ABA: ÁLBUM DO DIA
if st.session_state.filtro_aba == "álbum do dia":
    today_str = str(datetime.date.today())
    
    decididos_hoje = df_albums[
        (df_albums['Ultima_Audicao'] == today_str) & 
        (df_albums['Status'].str.strip().str.lower().isin(['avaliado', 'avaliar depois', 'não avaliado']))
    ]
    
    if not decididos_hoje.empty:
        disco_hoje = decididos_hoje.iloc[0]
        acao_tomada = disco_hoje['Status']
        st.markdown(f"""
            <div class="vinyl-card" style="border: 1px solid #1db954; text-align: center; padding: 30px; margin-top: 20px;">
                <h2 style="color: #1db954;">✅ Disco do Dia concluído!</h2>
                <p style="color: #ffffff; font-size: 18px; margin-bottom: 5px;"><b>{disco_hoje['Album']}</b> — {disco_hoje['Artist']}</p>
                <p style="color: #f59e0b; font-size: 14px;">Status registrado hoje: <b>{acao_tomada}</b></p>
                <p style="color: #ccc; font-size: 15px; margin-top: 15px;">O limite é de 1 disco por dia. Um novo álbum será sorteado automaticamente amanhã (após 24h).</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        disponiveis_hoje = df_albums[df_albums['Status'].str.strip().str.lower() == 'pendente'].reset_index(drop=True)
        
        if disponiveis_hoje.empty:
            st.success("🎉 Parabéns! Você já concluiu todos os discos pendentes do seu acervo!")
            st.stop()
            
        today_seed = int(datetime.date.today().strftime("%Y%m%d"))
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
            st.markdown(f'<a href="{url_spotify}" target="_blank" class="spotify-btn"><span class="spotify-icon">🎧</span> ouvir álbum completo</a>', unsafe_allow_html=True)
            
        with col_pop2:
            st.markdown("#### 🎵 registre sua audição")
            st.markdown(f"**Nota atual da capa:** {render_estrelas(album_alvo.get('Cover_Rating', 0))}")
            st.markdown("alterar nota da capa (1 a 5)")
            feedback_estrelas = st.feedback("stars", key="pop_cov_feedback")
            
            tot_p = st.number_input("total de músicas", 1, 30, int(float(album_alvo.get('Total_Tracks', 10))), key="pop_tot")
            lik_p = st.number_input("músicas que gostou", 0, tot_p, int(float(album_alvo.get('Liked_Tracks', 0))), key="pop_lik")
            
            colecao_atual = str(album_alvo.get('Colecao', 'Não')).strip().capitalize()
            idx_col_pop = 0 if colecao_atual in ['Sim', 'S', 'True', 'Yes'] else 1
            pop_colecao = st.selectbox("minha coleção", ["Sim", "Não"], index=idx_col_pop, key="pop_colecao_select")
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("salvar audição", type="primary"):
                    m_idx = df_albums[(df_albums['Album'] == str(album_alvo['Album'])) & (df_albums['Artist'] == str(album_alvo['Artist']))].index
                    if len(m_idx) > 0:
                        idx_s = m_idx[0]
                        if feedback_estrelas is not None:
                            df_albums.loc[idx_s, 'Cover_Rating'] = int(feedback_estrelas + 1)
                        df_albums.loc[idx_s, 'Total_Tracks'] = int(tot_p)
                        df_albums.loc[idx_s, 'Liked_Tracks'] = int(lik_p)
                        df_albums.loc[idx_s, 'Colecao'] = str(pop_colecao)
                        df_albums.loc[idx_s, 'Status'] = 'Avaliado'
                        df_albums.loc[idx_s, 'Ultima_Audicao'] = today_str
                        salvar_dados_online(df_albums)
                    st.rerun()
            with col_b2:
                if st.button("⏳ avaliar depois"):
                    m_idx = df_albums[(df_albums['Album'] == str(album_alvo['Album'])) & (df_albums['Artist'] == str(album_alvo['Artist']))].index
                    if len(m_idx) > 0:
                        df_albums.loc[m_idx[0], 'Status'] = 'Avaliar Depois'
                        df_albums.loc[m_idx[0], 'Ultima_Audicao'] = today_str
                        salvar_dados_online(df_albums)
                    st.rerun()
            with col_b3:
                if st.button("❌ não quero avaliar"):
                    m_idx = df_albums[(df_albums['Album'] == str(album_alvo['Album'])) & (df_albums['Artist'] == str(album_alvo['Artist']))].index
                    if len(m_idx) > 0:
                        df_albums.loc[m_idx[0], 'Status'] = 'Não Avaliado'
                        df_albums.loc[m_idx[0], 'Ultima_Audicao'] = today_str
                        salvar_dados_online(df_albums)
                    st.rerun()

# 2. ABA: MINHAS AVALIAÇÕES
elif st.session_state.filtro_aba == "minhas avaliações":
    st.markdown("### ⭐ minhas avaliações")
    df_base = df_albums[
        (df_albums['Status'].str.strip().str.lower() == 'avaliado') | 
        (df_albums['Cover_Rating'] > 0)
    ].copy()
    df_filtrado = aplicar_filtros_comuns(df_base)
    st.caption(f"exibindo todos os {len(df_filtrado)} discos avaliados.")
    
    if df_filtrado.empty:
        st.info("💡 Nenhum disco avaliado encontrado com esses filtros.")
    else:
        lista_discos_hist = df_filtrado.to_dict('records')
        for row_idx in range(0, len(lista_discos_hist), 4):
            cols = st.columns(4)
            for col_idx in range(4):
                flat_idx = row_idx + col_idx
                if flat_idx < len(lista_discos_hist):
                    r = lista_discos_hist[flat_idx]
                    with cols[col_idx]:
                        pais_card = str(r.get('Country', 'Brasil')).strip()
                        ano_val = int(r['Released']) if pd.notna(r['Released']) else ''
                        c_val = int(float(r['Cover_Rating'])) if pd.notna(r['Cover_Rating']) else 0
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
                        
                        if st.button("editar / ver detalhes", key=f"btn_hist_{flat_idx}"):
                            if st.session_state.get('album_editando') == r['Album']:
                                del st.session_state.album_editando
                            else:
                                st.session_state.album_editando = r['Album']
                            st.rerun()

            for col_idx in range(4):
                flat_idx = row_idx + col_idx
                if flat_idx < len(lista_discos_hist):
                    r = lista_discos_hist[flat_idx]
                    if st.session_state.get('album_editando') == r['Album']:
                        st.markdown("---")
                        with st.container():
                            st.markdown(f"✏️ **Editando: {r['Album']} ({r['Artist']})**")
                            match_idx = df_albums[(df_albums['Album'] == r['Album']) & (df_albums['Artist'] == r['Artist'])].index
                            row_sel = df_albums.loc[match_idx[0]] if len(match_idx) > 0 else r
                            
                            c_ed1, c_ed2 = st.columns(2)
                            with c_ed1:
                                cap = buscar_capa_album(str(row_sel['Artist']), str(row_sel['Album']))
                                if cap:
                                    st.image(cap, width=220)
                                url_sp = obter_link_spotify(row_sel)
                                st.markdown(f'<a href="{url_sp}" target="_blank" class="spotify-btn">🎧 ouvir no spotify</a>', unsafe_allow_html=True)
                            with c_ed2:
                                c_salva = int(float(row_sel.get('Cover_Rating', 0)))
                                st.markdown(f"**Nota atual da capa:** {render_estrelas(c_salva)}")
                                st.markdown("alterar nota da capa (1 a 5)")
                                fb_ed = st.feedback("stars", key=f"hist_c_{flat_idx}")
                                
                                tot_val = int(float(row_sel.get('Total_Tracks', 10)))
                                tot_f = st.number_input("total de músicas", 1, 30, tot_val, key=f"hist_tot_{flat_idx}")
                                
                                lik_val = int(float(row_sel.get('Liked_Tracks', 0)))
                                lik_f = st.number_input("músicas que gostou", 0, tot_f, lik_val, key=f"hist_lik_{flat_idx}")
                                
                                colecao_atual = str(row_sel.get('Colecao', 'Não')).strip().capitalize()
                                idx_col = 0 if colecao_atual in ['Sim', 'S', 'True', 'Yes'] else 1
                                nova_colecao = st.selectbox("minha coleção", ["Sim", "Não"], index=idx_col, key=f"hist_s_{flat_idx}")
                                
                                if st.button("salvar alterações", type="primary", key=f"hist_save_{flat_idx}"):
                                    if len(match_idx) > 0:
                                        idx_s = match_idx[0]
                                        if fb_ed is not None:
                                            df_albums.loc[idx_s, 'Cover_Rating'] = int(fb_ed + 1)
                                        df_albums.loc[idx_s, 'Total_Tracks'] = int(tot_f)
                                        df_albums.loc[idx_s, 'Liked_Tracks'] = int(lik_f)
                                        df_albums.loc[idx_s, 'Colecao'] = str(nova_colecao)
                                        df_albums.loc[idx_s, 'Status'] = 'Avaliado'
                                        salvar_dados_online(df_albums)
                                        st.success("Salvo no Google Sheets!")
                                        del st.session_state.album_editando
                                        st.rerun()
                                        
                                if st.button("fechar editor", key=f"hist_close_{flat_idx}"):
                                    del st.session_state.album_editando
                                    st.rerun()
                        st.markdown("---")

# 3. ABA: MINHA COLEÇÃO
elif st.session_state.filtro_aba == "minha coleção":
    st.markdown("### 💽 minha coleção de vinis")
    df_base = df_albums[df_albums['Colecao'].str.strip().str.lower().isin(['sim', 's', 'yes', 'true', '1'])].copy()
    df_filtrado = aplicar_filtros_comuns(df_base)
    st.caption(f"exibindo {len(df_filtrado)} discos catalogados na sua coleção.")
    
    if df_filtrado.empty:
        st.info("💡 Nenhum disco na coleção com esses filtros.")
    else:
        lista_discos = df_filtrado.to_dict('records')
        for row_idx in range(0, len(lista_discos), 4):
            cols = st.columns(4)
            for col_idx in range(4):
                flat_idx = row_idx + col_idx
                if flat_idx < len(lista_discos):
                    r = lista_discos[flat_idx]
                    with cols[col_idx]:
                        pais_card = str(r.get('Country', 'Brasil')).strip()
                        ano_val = int(r['Released']) if pd.notna(r['Released']) else ''
                        c_val = int(float(r['Cover_Rating']))
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
                        
                        if st.button("editar / ver detalhes", key=f"btn_col_{flat_idx}"):
                            if st.session_state.get('album_editando') == r['Album']:
                                del st.session_state.album_editando
                            else:
                                st.session_state.album_editando = r['Album']
                            st.rerun()

            for col_idx in range(4):
                flat_idx = row_idx + col_idx
                if flat_idx < len(lista_discos):
                    r = lista_discos[flat_idx]
                    if st.session_state.get('album_editando') == r['Album']:
                        st.markdown("---")
                        with st.container():
                            st.markdown(f"✏️ **Editando: {r['Album']} ({r['Artist']})**")
                            match_idx = df_albums[(df_albums['Album'] == r['Album']) & (df_albums['Artist'] == r['Artist'])].index
                            row_sel = df_albums.loc[match_idx[0]] if len(match_idx) > 0 else r
                            
                            c_ed1, c_ed2 = st.columns(2)
                            with c_ed1:
                                cap = buscar_capa_album(str(row_sel['Artist']), str(row_sel['Album']))
                                if cap:
                                    st.image(cap, width=220)
                                url_sp = obter_link_spotify(row_sel)
                                st.markdown(f'<a href="{url_sp}" target="_blank" class="spotify-btn">🎧 ouvir no spotify</a>', unsafe_allow_html=True)
                            with c_ed2:
                                c_salva = int(float(row_sel.get('Cover_Rating', 0)))
                                st.markdown(f"**Nota atual da capa:** {render_estrelas(c_salva)}")
                                st.markdown("alterar nota da capa (1 a 5)")
                                fb_ed = st.feedback("stars", key=f"col_c_{flat_idx}")
                                
                                tot_val = int(float(row_sel.get('Total_Tracks', 10)))
                                tot_f = st.number_input("total de músicas", 1, 30, tot_val, key=f"col_tot_{flat_idx}")
                                
                                lik_val = int(float(row_sel.get('Liked_Tracks', 0)))
                                lik_f = st.number_input("músicas que gostou", 0, tot_f, lik_val, key=f"col_lik_{flat_idx}")
                                
                                colecao_atual = str(row_sel.get('Colecao', 'Não')).strip().capitalize()
                                idx_col = 0 if colecao_atual in ['Sim', 'S', 'True', 'Yes'] else 1
                                nova_colecao = st.selectbox("minha coleção", ["Sim", "Não"], index=idx_col, key=f"col_s_{flat_idx}")
                                
                                if st.button("salvar alterações", type="primary", key=f"col_save_{flat_idx}"):
                                    if len(match_idx) > 0:
                                        idx_s = match_idx[0]
                                        if fb_ed is not None:
                                            df_albums.loc[idx_s, 'Cover_Rating'] = int(fb_ed + 1)
                                            df_albums.loc[idx_s, 'Status'] = 'Avaliado'
                                        df_albums.loc[idx_s, 'Total_Tracks'] = int(tot_f)
                                        df_albums.loc[idx_s, 'Liked_Tracks'] = int(lik_f)
                                        df_albums.loc[idx_s, 'Colecao'] = str(nova_colecao)
                                        salvar_dados_online(df_albums)
                                        st.success("Salvo com sucesso!")
                                        del st.session_state.album_editando
                                        st.rerun()
                                        
                                if st.button("fechar editor", key=f"col_close_{flat_idx}"):
                                    del st.session_state.album_editando
                                    st.rerun()
                        st.markdown("---")

# 4. ABA: AVALIAR DEPOIS
elif st.session_state.filtro_aba == "avaliar depois":
    st.markdown("### ⏳ fila de espera (avaliar depois)")
    df_base = df_albums[df_albums['Status'].str.strip().str.lower() == 'avaliar depois'].copy()
    df_filtrado = aplicar_filtros_comuns(df_base)
    st.caption(f"exibindo {len(df_filtrado)} discos guardados.")
    
    if df_filtrado.empty:
        st.info("💡 Nenhum disco na fila 'Avaliar depois' com esses filtros.")
    else:
        for idx, r in df_filtrado.iterrows():
            st.markdown(f"""
                <div class="vinyl-card">
                    <b style="color: #ffffff; font-size: 16px;">{r['Album']}</b> — <span style="color: #a0a0a0; font-size: 14px;">{r['Artist']}</span><br>
                    <span style="color: #ccc; font-size: 13px;">📅 {int(r['Released']) if pd.notna(r['Released']) else ''} | {r.get('Country', 'Brasil')}</span>
                </div>
            """, unsafe_allow_html=True)
            
            col_ad1, col_ad2 = st.columns(2)
            with col_ad1:
                if st.button("🎵 Avaliar agora", key=f"btn_ev_dep_{idx}0"):
                    if st.session_state.get('album_avaliando_direto') == r['Album']:
                        del st.session_state.album_avaliando_direto
                    else:
                        st.session_state.album_avaliando_direto = r['Album']
                    st.rerun()
            with col_ad2:
                if st.button("❌ Não quero avaliar", key=f"btn_ev_dep_{idx}1"):
                    m_idx = df_albums[(df_albums['Album'] == str(r['Album'])) & (df_albums['Artist'] == str(r['Artist']))].index
                    if len(m_idx) > 0:
                        df_albums.loc[m_idx[0], 'Status'] = 'Não Avaliado'
                        salvar_dados_online(df_albums)
                    st.rerun()
                    
            if st.session_state.get('album_avaliando_direto') == r['Album']:
                st.markdown("---")
                with st.container():
                    st.markdown(f"✏️ **Avaliando diretamente: {r['Album']} ({r['Artist']})**")
                    match_idx = df_albums[(df_albums['Album'] == r['Album']) & (df_albums['Artist'] == r['Artist'])].index
                    row_sel = df_albums.loc[match_idx[0]] if len(match_idx) > 0 else r
                    
                    c_ed1, c_ed2 = st.columns(2)
                    with c_ed1:
                        cap = buscar_capa_album(str(row_sel['Artist']), str(row_sel['Album']))
                        if cap:
                            st.image(cap, width=220)
                        url_sp = obter_link_spotify(row_sel)
                        st.markdown(f'<a href="{url_sp}" target="_blank" class="spotify-btn">🎧 ouvir no spotify</a>', unsafe_allow_html=True)
                    with c_ed2:
                        c_salva = int(float(row_sel.get('Cover_Rating', 0)))
                        st.markdown(f"**Nota atual da capa:** {render_estrelas(c_salva)}")
                        st.markdown("alterar nota da capa (1 a 5)")
                        fb_ed = st.feedback("stars", key=f"direto_c_{idx}")
                        
                        tot_val = int(float(row_sel.get('Total_Tracks', 10)))
                        tot_f = st.number_input("total de músicas", 1, 30, tot_val, key=f"direto_tot_{idx}")
                        
                        lik_val = int(float(row_sel.get('Liked_Tracks', 0)))
                        lik_f = st.number_input("músicas que gostou", 0, tot_f, lik_val, key=f"direto_lik_{idx}")
                        
                        colecao_atual = str(row_sel.get('Colecao', 'Não')).strip().capitalize()
                        idx_col = 0 if colecao_atual in ['Sim', 'S', 'True', 'Yes'] else 1
                        nova_colecao = st.selectbox("minha coleção", ["Sim", "Não"], index=idx_col, key=f"direto_s_{idx}")
                        
                        if st.button("salvar audição", type="primary", key=f"direto_save_{idx}"):
                            if len(match_idx) > 0:
                                idx_s = match_idx[0]
                                if fb_ed is not None:
                                    df_albums.loc[idx_s, 'Cover_Rating'] = int(fb_ed + 1)
                                df_albums.loc[idx_s, 'Total_Tracks'] = int(tot_f)
                                df_albums.loc[idx_s, 'Liked_Tracks'] = int(lik_f)
                                df_albums.loc[idx_s, 'Colecao'] = str(nova_colecao)
                                df_albums.loc[idx_s, 'Status'] = 'Avaliado'
                                salvar_dados_online(df_albums)
                                st.success("Avaliação salva no Google Sheets!")
                                del st.session_state.album_avaliando_direto
                                st.rerun()
                                
                        if st.button("fechar", key=f"direto_close_{idx}"):
                            del st.session_state.album_avaliando_direto
                            st.rerun()
                st.markdown("---")

# 5. ABA: NÃO AVALIADOS
elif st.session_state.filtro_aba == "não avaliados":
    st.markdown("### ❌ discos não avaliados (descartados)")
    df_base = df_albums[df_albums['Status'].str.strip().str.lower() == 'não avaliado'].copy()
    df_filtrado = aplicar_filtros_comuns(df_base)
    st.caption(f"exibindo {len(df_filtrado)} discos descartados.")
    
    if df_filtrado.empty:
        st.info("💡 Nenhum disco descartado com esses filtros.")
    else:
        for idx, r in df_filtrado.iterrows():
            st.markdown(f"""
                <div class="vinyl-card">
                    <b style="color: #ffffff; font-size: 16px;">{r['Album']}</b> — <span style="color: #a0a0a0; font-size: 14px;">{r['Artist']}</span>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Voltar para Avaliar Depois", key=f"btn_nao_ev_{idx}"):
                m_idx = df_albums[(df_albums['Album'] == str(r['Album'])) & (df_albums['Artist'] == str(r['Artist']))].index
                if len(m_idx) > 0:
                    df_albums.loc[m_idx[0], 'Status'] = 'Avaliar Depois'
                    salvar_dados_online(df_albums)
                st.rerun()

# 6. ABA: ESTATÍSTICAS
elif st.session_state.filtro_aba == "estatísticas":
    st.subheader("📊 estatísticas da sua coleção")
    df_avaliados_est = df_albums[df_albums['Status'].str.strip().str.lower() == 'avaliado']
    
    media_discos = df_avaliados_est['Nota_Calculada'].mean() if not df_avaliados_est.empty else 0.0
    media_capas = df_avaliados_est['Cover_Rating'].astype(float).mean() if not df_avaliados_est.empty else 0.0
    
    c_s1, c_s2, c_s3 = st.columns(3)
    with c_s1:
        st.metric("total de discos catalogados", len(df_albums))
    with c_s2:
        st.metric("média de nota dos discos", f"{media_discos:.1f} / 5")
    with c_s3:
        st.metric("média de nota das capas", f"{media_capas:.1f} / 5")
            
    st.markdown("---")
    st.markdown("### 📚 acervo geral e histórico")
    df_filtrado_geral = aplicar_filtros_comuns(df_albums)
    st.caption(f"exibindo {len(df_filtrado_geral)} discos no acervo geral.")
    
    if df_filtrado_geral.empty:
        st.info("💡 Nenhum disco encontrado com esses filtros.")
    else:
        lista_discos_geral = df_filtrado_geral.head(24).to_dict('records')
        for row_idx in range(0, len(lista_discos_geral), 4):
            cols = st.columns(4)
            for col_idx in range(4):
                flat_idx = row_idx + col_idx
                if flat_idx < len(lista_discos_geral):
                    r = lista_discos_geral[flat_idx]
                    with cols[col_idx]:
                        pais_card = str(r.get('Country', 'Brasil')).strip()
                        ano_val = int(r['Released']) if pd.notna(r['Released']) else ''
                        c_val = int(float(r['Cover_Rating']))
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
                        
                        if st.button("editar / ver detalhes", key=f"btn_geral_{flat_idx}"):
                            if st.session_state.get('album_editando') == r['Album']:
                                del st.session_state.album_editando
                            else:
                                st.session_state.album_editando = r['Album']
                            st.rerun()

            for col_idx in range(4):
                flat_idx = row_idx + col_idx
                if flat_idx < len(lista_discos_geral):
                    r = lista_discos_geral[flat_idx]
                    if st.session_state.get('album_editando') == r['Album']:
                        st.markdown("---")
                        with st.container():
                            st.markdown(f"✏️ **Editando: {r['Album']} ({r['Artist']})**")
                            match_idx = df_albums[(df_albums['Album'] == r['Album']) & (df_albums['Artist'] == r['Artist'])].index
                            row_sel = df_albums.loc[match_idx[0]] if len(match_idx) > 0 else r
                            
                            c_ed1, c_ed2 = st.columns(2)
                            with c_ed1:
                                cap = buscar_capa_album(str(row_sel['Artist']), str(row_sel['Album']))
                                if cap:
                                    st.image(cap, width=220)
                                url_sp = obter_link_spotify(row_sel)
                                st.markdown(f'<a href="{url_sp}" target="_blank" class="spotify-btn">🎧 ouvir no spotify</a>', unsafe_allow_html=True)
                            with c_ed2:
                                c_salva = int(float(row_sel.get('Cover_Rating', 0)))
                                st.markdown(f"**Nota atual da capa:** {render_estrelas(c_salva)}")
                                st.markdown("alterar nota da capa (1 a 5)")
                                fb_ed = st.feedback("stars", key=f"geral_c_{flat_idx}")
                                
                                tot_val = int(float(row_sel.get('Total_Tracks', 10)))
                                tot_f = st.number_input("total de músicas", 1, 30, tot_val, key=f"geral_tot_{flat_idx}")
                                
                                lik_val = int(float(row_sel.get('Liked_Tracks', 0)))
                                lik_f = st.number_input("músicas que gostou", 0, tot_f, lik_val, key=f"geral_lik_{flat_idx}")
                                
                                colecao_atual = str(row_sel.get('Colecao', 'Não')).strip().capitalize()
                                idx_col = 0 if colecao_atual in ['Sim', 'S', 'True', 'Yes'] else 1
                                nova_colecao = st.selectbox("minha coleção", ["Sim", "Não"], index=idx_col, key=f"geral_s_{flat_idx}")
                                
                                if st.button("salvar alterações", type="primary", key=f"geral_save_{flat_idx}"):
                                    if len(match_idx) > 0:
                                        idx_s = match_idx[0]
                                        if fb_ed is not None:
                                            df_albums.loc[idx_s, 'Cover_Rating'] = int(fb_ed + 1)
                                            df_albums.loc[idx_s, 'Status'] = 'Avaliado'
                                        df_albums.loc[idx_s, 'Total_Tracks'] = int(tot_f)
                                        df_albums.loc[idx_s, 'Liked_Tracks'] = int(lik_f)
                                        df_albums.loc[idx_s, 'Colecao'] = str(nova_colecao)
                                        salvar_dados_online(df_albums)
                                        st.success("Salvo no Google Sheets!")
                                        del st.session_state.album_editando
                                        st.rerun()
                                        
                                if st.button("fechar editor", key=f"geral_close_{flat_idx}"):
                                    del st.session_state.album_editando
                                    st.rerun()
                        st.markdown("---")

# 7. ABA: INSERIR MANUALMENTE
elif st.session_state.filtro_aba == "inserir manualmente":
    st.subheader("➕ inserir novo disco manualmente")
    
    m_artista = st.text_input("artista", key="man_artist")
    m_pais = st.text_input("país", value="Brasil", key="man_pais")
    m_album = st.text_input("nome do álbum", key="man_album")
    m_ano = st.number_input("ano de lançamento", min_value=1900, max_value=2026, value=1975, key="man_ano")
    m_spotify = st.text_input("link do álbum no Spotify", value="Spotify", key="man_spotify")
    m_colecao = st.selectbox("minha coleção", ["Sim", "Não"], key="man_col")
    
    st.markdown("nota da capa (1 a 5)")
    fb_man = st.feedback("stars", key="manual_stars")
    m_capa = (fb_man + 1) if fb_man is not None else 0
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        m_tot = st.number_input("total de músicas", 1, 30, 10, key="man_tot")
    with c_m2:
        m_lik = st.number_input("músicas que gostou", 0, m_tot, 0, key="man_lik")
        
    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns(2)
    
    with c_btn1:
        if st.button("🎵 avaliar agora", type="primary", use_container_width=True):
            if not m_artista.strip() or not m_album.strip():
                st.error("Preencha ao menos o Artista e o Nome do Álbum.")
            else:
                novo_registro = pd.DataFrame([{
                    'Artist': str(m_artista),
                    'Country': str(m_pais),
                    'Album': str(m_album),
                    'Released': int(m_ano),
                    'Cover_Rating': int(m_capa),
                    'Total_Tracks': int(m_tot),
                    'Liked_Tracks': int(m_lik),
                    'Favorite_Track': '',
                    'My_Review': '',
                    'Spotify_Link': str(m_spotify),
                    'Status': 'Avaliado',
                    'Colecao': str(m_colecao),
                    'Ultima_Audicao': str(datetime.date.today())
                }])
                df_atualizado = pd.concat([df_albums, novo_registro], ignore_index=True)
                salvar_dados_online(df_atualizado)
                st.success(f"'{m_album}' adicionado e avaliado com sucesso!")
                st.rerun()
                
    with c_btn2:
        if st.button("⏳ avaliar depois", use_container_width=True):
            if not m_artista.strip() or not m_album.strip():
                st.error("Preencha ao menos o Artista e o Nome do Álbum.")
            else:
                novo_registro = pd.DataFrame([{
                    'Artist': str(m_artista),
                    'Country': str(m_pais),
                    'Album': str(m_album),
                    'Released': int(m_ano),
                    'Cover_Rating': int(m_capa),
                    'Total_Tracks': int(m_tot),
                    'Liked_Tracks': int(m_lik),
                    'Favorite_Track': '',
                    'My_Review': '',
                    'Spotify_Link': str(m_spotify),
                    'Status': 'Avaliar Depois',
                    'Colecao': str(m_colecao),
                    'Ultima_Audicao': ''
                }])
                df_atualizado = pd.concat([df_albums, novo_registro], ignore_index=True)
                salvar_dados_online(df_atualizado)
                st.success(f"'{m_album}' salvo na fila 'Avaliar depois'!")
                st.rerun()