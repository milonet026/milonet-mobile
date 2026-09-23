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
    st.subheader("📋 Pregled i izmena servisa")
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
            status = r.get('status', '')
            # Definisane boje prema zahtevu: Crvena za Na servisu, Zelena za Završeno, Bela za Otkazano/ostalo
            if status in ['Na servisu', 'U servisu']:
                status_emoji = "🔴"
            elif status in ['Završeno', 'Zavrseno', 'Preuzeto']:
                status_emoji = "🟢"
            else:
                status_emoji = "⚪"
                
            title_text = f"{status_emoji} {r.get('broj_reversa')} — {r.get('vlasnik')} ({r.get('marka_model')})"
            
            with st.expander(title_text):
                st.write(f"**Datum prijema:** {r.get('datum_prijema')}")
                st.write(f"**Trenutni status:** {status}")
                
                # Forma za izmenu unutar expandera
                with st.form(key=f"edit_form_{r.get('id')}"):
                    st.markdown("### ✏️ Izmena servisa")
                    
                    new_vlasnik = st.text_input("Vlasnik", value=r.get('vlasnik') or "")
                    new_telefon = st.text_input("Telefon", value=r.get('telefon') or "")
                    new_model = st.text_input("Marka i model", value=r.get('marka_model') or "")
                    new_win_pass = st.text_input("Windows šifra", value=r.get('win_password') or "")
                    new_oprema = st.text_input("Oprema", value=r.get('oprema') or "")
                    
                    status_options = ["Na servisu", "Završeno", "Preuzeto", "Otkazano"]
                    curr_status_idx = status_options.index(status) if status in status_options else 0
                    new_status = st.selectbox("Status", status_options, index=curr_status_idx)
                    
                    new_kvar = st.text_area("Opis kvara", value=r.get('opis_kvara') or "")
                    new_radovi = st.text_area("Urađeni radovi", value=r.get('opis_radova') or "")
                    new_cena = st.text_input("Cena (RSD)", value=r.get('cena') or "")
                    new_napomena = st.text_area("Napomena", value=r.get('napomena') or "")

                    submit_btn = st.form_submit_button("💾 Sačuvaj izmene")

                    if submit_btn:
                        try:
                            up_conn = get_db_connection()
                            up_cursor = up_conn.cursor()
                            up_cursor.execute("""
                                UPDATE servisi 
                                SET vlasnik=%s, telefon=%s, marka_model=%s, win_password=%s, 
                                    oprema=%s, status=%s, opis_kvara=%s, opis_radova=%s, cena=%s, napomena=%s
                                WHERE id=%s
                            """, (
                                new_vlasnik, new_telefon, new_model, new_win_pass, 
                                new_oprema, new_status, new_kvar, new_radovi, new_cena, new_napomena, r.get('id')
                            ))
                            up_conn.commit()
                            up_cursor.close()
                            up_conn.close()
                            st.success("Uspešno sačuvano! Osvežite stranicu za prikaz promena.")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Greška prilikom čuvanja: {ex}")

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
