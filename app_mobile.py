import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- SUPABASE POSTGRESQL CLOUD KONEKCIJA ---
SUPABASE_URL = "postgresql://postgres.ttwghfszzakdvjuxptcz:Moja27Pobeda%2B@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

def get_db_connection():
    return psycopg2.connect(SUPABASE_URL, cursor_factory=RealDictCursor)

st.set_page_config(
    page_title="MiloNet Mobile",
    page_icon="🔧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Stilovi i podesavanja
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🔧 MiloNet Electronics — Mobile")

# Navigacija preko radio dugmića
app_mode = st.radio("Režim rada:", ["Servisi", "Prodaja"], horizontal=True)
st.divider()

# Pretraga
search_query = st.text_input("🔍 Pretraga", placeholder="Unesi ime, telefon ili revers...")

if app_mode == "Servisi":
    st.subheader("📋 Pregled servisa")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search_query:
            q = f"%{search_query}%"
            cursor.execute("""
                SELECT * FROM servisi 
                WHERE broj_reversa ILIKE %s OR vlasnik ILIKE %s OR telefon ILIKE %s OR marka_model ILIKE %s
                ORDER BY id DESC
            """, (q, q, q, q))
        else:
            cursor.execute("SELECT * FROM servisi ORDER BY id DESC LIMIT 50")
            
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        st.text(f"Ukupno pronađeno servisa: {len(rows)}")

        for r in rows:
            status_emoji = "🟢" if r.get('status') == 'Završeno' else "🟡" if r.get('status') == 'Na servisu' else "⚪"
            title_text = f"{status_emoji} {r.get('broj_reversa')} — {r.get('vlasnik')} ({r.get('marka_model')})"
            
            with st.expander(title_text):
                st.write(f"**Datum prijema:** {r.get('datum_prijema')}")
                st.write(f"**Telefon:** {r.get('telefon')}")
                st.write(f"**Status:** {r.get('status')}")
                st.write(f"**Opis kvara:** {r.get('opis_kvara')}")
                st.write(f"**Windows šifra:** {r.get('win_password') or 'Nema'}")
                st.write(f"**Oprema:** {r.get('oprema') or 'Samo uređaj'}")
                st.write(f"**Urađeni radovi:** {r.get('opis_radova') or 'Nema unosa'}")
                st.write(f"**Cena:** {r.get('cena') or '0'} RSD")

    except Exception as e:
        st.error(f"Greška pri učitavanju baze servisa: {e}")

elif app_mode == "Prodaja":
    st.subheader("🛒 Pregled prodaje")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search_query:
            q = f"%{search_query}%"
            cursor.execute("""
                SELECT * FROM prodaja 
                WHERE broj_reversa ILIKE %s OR vlasnik ILIKE %s OR telefon ILIKE %s OR artikal ILIKE %s
                ORDER BY id DESC
            """, (q, q, q, q))
        else:
            cursor.execute("SELECT * FROM prodaja ORDER BY id DESC LIMIT 50")
            
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        st.text(f"Ukupno pronađeno prodaja: {len(rows)}")

        for r in rows:
            title_text = f"🛒 {r.get('broj_reversa')} — {r.get('vlasnik')} ({r.get('artikal')})"
            
            with st.expander(title_text):
                st.write(f"**Datum prodaje:** {r.get('datum_prodaje')}")
                st.write(f"**Kupac:** {r.get('vlasnik')}")
                st.write(f"**Telefon:** {r.get('telefon')}")
                st.write(f"**Artikal:** {r.get('artikal')}")
                st.write(f"**Količina:** {r.get('kolicina')}")
                st.write(f"**Cena:** {r.get('cena')} RSD")
                st.write(f"**Napomena:** {r.get('napomena') or 'Nema'}")

    except Exception as e:
        st.error(f"Greška pri učitavanju baze prodaje: {e}")
