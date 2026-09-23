import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- SUPABASE POSTGRESQL CLOUD KONEKCIJA ---
SUPABASE_URL = "postgresql://postgres.ttwghfszzakdvjuxptcz:Moja27Pobeda%2B@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

def get_db_connection():
    return psycopg2.connect(SUPABASE_URL, cursor_factory=RealDictCursor)

def generate_broj_reversa():
    conn = get_db_connection()
    cursor = conn.cursor()
    year = datetime.now().strftime("%Y")
    
    cursor.execute("SELECT COUNT(*) as count FROM servisi WHERE broj_reversa LIKE %s", (f"%/{year}",))
    count_servisi = cursor.fetchone()['count'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM prodaja WHERE broj_reversa LIKE %s", (f"%/{year}",))
    count_prodaja = cursor.fetchone()['count'] or 0

    count = count_servisi + count_prodaja + 1
    cursor.close()
    conn.close()
    return f"{count:04d}/{year}"

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

# Navigacija preko radio dugmića (dodat režim za Novi Unos)
app_mode = st.radio("Režim rada:", ["➕ Novi Unos", "📋 Servisi", "🛒 Prodaja"], horizontal=True)
st.divider()

if app_mode == "➕ Novi Unos":
    st.subheader("📝 Unos novog uređaja ili prodaje")
    
    tip_unosa = st.selectbox("Izaberite tip unosa:", ["Servis", "Prodaja"])
    
    autofilled_revers = generate_broj_reversa()
    current_time_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    if tip_unosa == "Servis":
        with st.form(key="novi_servis_form"):
            st.markdown("### Podaci o prijemu uređaja")
            broj_reversa = st.text_input("Broj reversa", value=autofilled_revers)
            datum_prijema = st.text_input("Datum prijema", value=current_time_str)
            vlasnik = st.text_input("Vlasnik uređaja *")
            telefon = st.text_input("Broj telefona *")
            marka_model = st.text_input("Marka i model uređaja *")
            win_password = st.text_input("Windows šifra", placeholder="npr. 1234, Nema...")
            oprema = st.text_input("Prateća oprema", placeholder="npr. Punjač, Torba, Miš...")
            bitni_podaci = st.text_input("Bitni podaci", placeholder="npr. Slike, Desktop...")
            opis_kvara = st.text_area("Opis kvara *")
            napomena = st.text_area("Napomena")

            submitted_servis = st.form_submit_button("💾 Sačuvaj i unesi servis")

            if submitted_servis:
                if not vlasnik or not telefon or not marka_model or not opis_kvara:
                    st.warning("Molimo popunite sva obavezna polja (Vlasnik, Telefon, Model, Opis kvara)!")
                else:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO servisi (broj_reversa, datum_prijema, marka_model, vlasnik, telefon, opis_kvara, win_password, oprema, bitni_podaci, napomena)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (broj_reversa, datum_prijema, marka_model, vlasnik, telefon, opis_kvara, win_password, oprema, bitni_podaci, napomena))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"Uspešno unet servis sa brojem reversa: {broj_reversa}")
                    except Exception as e:
                        st.error(f"Greška prilikom upisa u bazu: {e}")

    else: # Prodaja
        with st.form(key="nova_prodaja_form"):
            st.markdown("### Podaci o prodaji opreme")
            broj_racuna = st.text_input("Broj računa/reversa", value=autofilled_revers)
            datum_prodaje = st.text_input("Datum prodaje", value=current_time_str)
            kupac = st.text_input("Kupac / Vlasnik *")
            telefon_kupca = st.text_input("Broj telefona")
            artikal = st.text_input("Artikal / Oprema *")
            kolicina = st.text_input("Količina", value="1")
            cena = st.text_input("Ukupna cena (RSD) *")
            napomena_prodaja = st.text_area("Napomena / Garancija")

            submitted_prodaja = st.form_submit_button("💾 Sačuvaj i unesi prodaju")

            if submitted_prodaja:
                if not kupac or not artikal or not cena:
                    st.warning("Molimo popunite obavezna polja (Kupac, Artikal, Cena)!")
                else:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO prodaja (broj_reversa, datum_prodaje, vlasnik, telefon, artikal, kolicina, cena, napomena)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (broj_racuna, datum_prodaje, kupac, telefon_kupca, artikal, kolicina, cena, napomena_prodaja))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"Uspešno uneta prodaja sa brojem: {broj_racuna}")
                    except Exception as e:
                        st.error(f"Greška prilikom upisa prodaje: {e}")

else:
    # Pretraga za postojeće zapise
    search_query = st.text_input("🔍 Pretraga", placeholder="Unesi ime, telefon ili revers...")

    if app_mode == "📋 Servisi":
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
                    
                    with st.form(key=f"edit_form_servis_{r.get('id')}"):
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

                        submit_btn = st.form_submit_button("💾 Sačuvaj izmene servisa")

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
                                st.success("Uspešno sačuvano! Osvežite stranicu.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Greška prilikom čuvanja: {ex}")

        except Exception as e:
            st.error(f"Greška pri učitavanju baze servisa: {e}")

    elif app_mode == "🛒 Prodaja":
        st.subheader("🛒 Pregled i izmena prodaje")
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
                status = r.get('status', 'Završeno')
                if status in ['Otkazano', 'Stornirano']:
                    status_emoji = "🔴"
                elif status in ['Završeno', 'Zavrseno', 'Plaćeno']:
                    status_emoji = "🟢"
                else:
                    status_emoji = "⚪"

                title_text = f"{status_emoji} {r.get('broj_reversa')} — {r.get('vlasnik')} ({r.get('artikal')})"
                
                with st.expander(title_text):
                    st.write(f"**Datum prodaje:** {r.get('datum_prodaje')}")
                    st.write(f"**Trenutni status:** {status if 'status' in r and r.get('status') else 'Završeno'}")
                    
                    with st.form(key=f"edit_form_prodaja_{r.get('id')}"):
                        st.markdown("### ✏️ Izmena prodaje")
                        
                        p_vlasnik = st.text_input("Kupac", value=r.get('vlasnik') or "")
                        p_telefon = st.text_input("Telefon", value=r.get('telefon') or "")
                        p_artikal = st.text_input("Artikal / Oprema", value=r.get('artikal') or "")
                        p_kolicina = st.text_input("Količina", value=r.get('kolicina') or "1")
                        p_cena = st.text_input("Ukupna cena (RSD)", value=r.get('cena') or "")
                        
                        prod_status_options = ["Završeno", "Otkazano", "Rezervisano"]
                        current_p_status = r.get('status') if 'status' in r and r.get('status') in prod_status_options else "Završeno"
                        p_status = st.selectbox("Status prodaje", prod_status_options, index=prod_status_options.index(current_p_status))
                        
                        p_napomena = st.text_area("Napomena / Garancija", value=r.get('napomena') or "")

                        submit_p_btn = st.form_submit_button("💾 Sačuvaj izmene prodaje")

                        if submit_p_btn:
                            try:
                                up_conn = get_db_connection()
                                up_cursor = up_conn.cursor()
                                up_cursor.execute("""
                                    UPDATE prodaja 
                                    SET vlasnik=%s, telefon=%s, artikal=%s, kolicina=%s, cena=%s, napomena=%s
                                    WHERE id=%s
                                """, (
                                    p_vlasnik, p_telefon, p_artikal, p_kolicina, p_cena, p_napomena, r.get('id')
                                ))
                                up_conn.commit()
                                up_cursor.close()
                                up_conn.close()
                                st.success("Uspešno sačuvano! Osvežite stranicu.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Greška prilikom čuvanja prodaje: {ex}")

        except Exception as e:
            st.error(f"Greška pri učitavanju baze prodaje: {e}")
