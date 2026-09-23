import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta

# Postavke stranice za mobilni ekran
st.set_page_config(
    page_title="MiloNet Mobile",
    page_icon="🔧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def get_db_connection():
    db_url = st.secrets.get("SUPABASE_URL", "postgresql://postgres.ttwghfszzakdvjuxptcz:Moja27Pobeda%2B@aws-1-eu-west-1.pooler.supabase.com:6543/postgres")
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

def init_supabase_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Tabela za servise
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servisi (
            id SERIAL PRIMARY KEY,
            broj_reversa TEXT UNIQUE,
            datum_prijema TEXT,
            marka_model TEXT,
            vlasnik TEXT,
            telefon TEXT,
            opis_kvara TEXT,
            win_password TEXT DEFAULT '',
            oprema TEXT DEFAULT '',
            bitni_podaci TEXT DEFAULT '',
            napomena TEXT DEFAULT '',
            status TEXT DEFAULT 'Na servisu',
            opis_radova TEXT DEFAULT '',
            cena TEXT DEFAULT ''
        );
    """)
    # Nova tabela za prodaju
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prodaja (
            id SERIAL PRIMARY KEY,
            broj_racuna TEXT UNIQUE,
            datum_prodaje TEXT,
            stavke TEXT,
            kupac TEXT DEFAULT '',
            telefon TEXT DEFAULT '',
            ukupna_cena TEXT,
            nacin_placanja TEXT DEFAULT 'Gotovina',
            napomena TEXT DEFAULT ''
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def fix_id_sequences():
    """Popravlja PostgreSQL brojače (sequence) ako su ispali iz sinhronizacije"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT setval(pg_get_serial_sequence('servisi', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM servisi;")
        cursor.execute("SELECT setval(pg_get_serial_sequence('prodaja', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM prodaja;")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass

def get_local_now_str():
    """Vraća tačno lokalno vreme za Srbiju (UTC+2 za letnje računanje vremena)"""
    srbija_tz = timezone(timedelta(hours=2))
    return datetime.now(srbija_tz).strftime("%d.%m.%Y %H:%M")

def generate_broj_reversa():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        srbija_tz = timezone(timedelta(hours=2))
        year = datetime.now(srbija_tz).strftime("%Y")
        cursor.execute("SELECT COUNT(*) as count FROM servisi WHERE broj_reversa LIKE %s", (f"%/{year}",))
        row = cursor.fetchone()
        count = (row['count'] if row else 0) + 1
        cursor.close()
        conn.close()
        return f"{count:04d}/{year}"
    except Exception:
        srbija_tz = timezone(timedelta(hours=2))
        return "0001/" + datetime.now(srbija_tz).strftime("%Y")

def generate_broj_racuna():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        srbija_tz = timezone(timedelta(hours=2))
        year = datetime.now(srbija_tz).strftime("%Y")
        cursor.execute("SELECT COUNT(*) as count FROM prodaja WHERE broj_racuna LIKE %s", (f"%/{year}",))
        row = cursor.fetchone()
        count = (row['count'] if row else 0) + 1
        cursor.close()
        conn.close()
        return f"P-{count:04d}/{year}"
    except Exception:
        srbija_tz = timezone(timedelta(hours=2))
        return "P-0001/" + datetime.now(srbija_tz).strftime("%Y")

def fetch_servisi(search_query=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    if search_query:
        query = """
            SELECT * FROM servisi 
            WHERE broj_reversa ILIKE %s 
               OR vlasnik ILIKE %s 
               OR telefon ILIKE %s 
               OR marka_model ILIKE %s
            ORDER BY id DESC
        """
        wildcard = f"%{search_query}%"
        cursor.execute(query, (wildcard, wildcard, wildcard, wildcard))
    else:
        cursor.execute("SELECT * FROM servisi ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_prodaja(search_query=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    if search_query:
        query = """
            SELECT * FROM prodaja 
            WHERE broj_racuna ILIKE %s 
               OR kupac ILIKE %s 
               OR telefon ILIKE %s 
               OR stavke ILIKE %s
            ORDER BY id DESC
        """
        wildcard = f"%{search_query}%"
        cursor.execute(query, (wildcard, wildcard, wildcard, wildcard))
    else:
        cursor.execute("SELECT * FROM prodaja ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def update_servis_in_db(servis_id, status, radovi, cena):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE servisi 
        SET status = %s, opis_radova = %s, cena = %s 
        WHERE id = %s
    """, (status, radovi, cena, servis_id))
    conn.commit()
    cursor.close()
    conn.close()

# Inicijalizacija baze i sinhronizacija brojača pri pokretanju
try:
    init_supabase_db()
    fix_id_sequences()
except Exception as e:
    st.error(f"Greška pri povezivanju sa bazom: {e}")

st.title("🔧 MiloNet Mobile")
st.caption("Cloud baza servisa i maloprodaje")

# Navigacija preko Tab-ova na telefonu (3 taba)
tab_prijem, tab_prodaja, tab_pretraga = st.tabs(["➕ Nov Prijem", "🛒 Nova Prodaja", "🔍 Pretraga & Baza"])

# --- TAB 1: UNOS NOVOG PRIJEMA ---
with tab_prijem:
    st.subheader("Prijem uređaja sa telefona")
    
    automatski_revers = generate_broj_reversa()
    trenutno_vreme = get_local_now_str()

    with st.form("form_novi_prijem", clear_on_submit=True):
        st.info(f"📋 **Broj reversa:** `{automatski_revers}` | 📅 **Datum:** `{trenutno_vreme}`")
        
        vlasnik = st.text_input("Vlasnik uređaja *", placeholder="Ime i prezime")
        telefon = st.text_input("Broj telefona *", placeholder="06x/xxx-xxx")
        model = st.text_input("Marka i model *", placeholder="npr. Laptop Asus K53S")
        kvar = st.text_area("Opis kvara *", placeholder="Šta je problem sa uređajem?")
        
        st.markdown("---")
        win_pass = st.text_input("Windows Šifra", placeholder="npr. 1234 ili nema")
        oprema = st.text_input("Prateća oprema", placeholder="Punjač, torba, miš...")
        podaci = st.text_input("Bitni podaci za čuvanje", placeholder="Desktop, Slike, Dokumenta...")
        napomena = st.text_input("Napomena", placeholder="Interna napomena...")

        submitted = st.form_submit_button("💾 Sačuvaj prijem u bazu", use_container_width=True)

        if submitted:
            if not vlasnik or not telefon or not model or not kvar:
                st.error("⚠️ Molimo vas popunite obavezna polja (Vlasnik, Telefon, Model, Kvar).")
            else:
                try:
                    fix_id_sequences()
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO servisi (broj_reversa, datum_prijema, marka_model, vlasnik, telefon, opis_kvara, win_password, oprema, bitni_podaci, napomena)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (automatski_revers, trenutno_vreme, model, vlasnik, telefon, kvar, win_pass, oprema, podaci, napomena))
                    conn.commit()
                    cursor.close()
                    conn.close()

                    st.success(f"✅ Uspešno sačuvan prijem pod brojem **{automatski_revers}**!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Greška prilikom upisa u bazu: {e}")

# --- TAB 2: NOVA PRODAJA ---
with tab_prodaja:
    st.subheader("Evidencija prodaje sa telefona")
    
    automatski_racun = generate_broj_racuna()
    trenutno_vreme_prodaje = get_local_now_str()

    with st.form("form_nova_prodaja", clear_on_submit=True):
        st.info(f"🧾 **Broj računa:** `{automatski_racun}` | 📅 **Datum:** `{trenutno_vreme_prodaje}`")
        
        stavke = st.text_area("Stavke / Proizvodi / Usluge *", placeholder="npr. HDMI kabl 2m, Miš wireless...")
        ukupna_cena = st.text_input("Ukupna cena (RSD) *", placeholder="npr. 1500")
        
        st.markdown("---")
        kupac = st.text_input("Kupac (opciono)", placeholder="Ime kupca ili ostaje prazno")
        tel_kupca = st.text_input("Telefon kupca (opciono)", placeholder="06x/xxx-xxx")
        nacin_placanja = st.selectbox("Način plaćanja", ["Gotovina", "Kartica", "Virman / Račun"])
        napomena_prodaja = st.text_input("Napomena za prodaju", placeholder="Dodatne napomene...")

        submitted_prodaja = st.form_submit_button("🛒 Evidentiraj prodaju", use_container_width=True)

        if submitted_prodaja:
            if not stavke or not ukupna_cena:
                st.error("⚠️ Molimo vas popunite obavezna polja (Stavke i Ukupna cena).")
            else:
                try:
                    fix_id_sequences()
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO prodaja (broj_racuna, datum_prodaje, stavke, kupac, telefon, ukupna_cena, nacin_placanja, napomena)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (automatski_racun, trenutno_vreme_prodaje, stavke, kupac, tel_kupca, ukupna_cena, nacin_placanja, napomena_prodaja))
                    conn.commit()
                    cursor.close()
                    conn.close()

                    st.success(f"✅ Uspešno evidentirana prodaja pod brojem **{automatski_racun}**!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Greška prilikom upisa prodaje u bazu: {e}")

# --- TAB 3: PRETRAGA I BAZA (SERVISI I PRODAJA) ---
with tab_pretraga:
    st.subheader("Baza podataka i pretraga")
    
    izbor_baze = st.radio("Izaberi bazu za pregled:", ["Servisi", "Prodaja"], horizontal=True)
    
    if izbor_baze == "Servisi":
        search_input = st.text_input("🔍 Pretraga servisa (Revers, Vlasnik, Telefon, Model):", placeholder="Ukucaj ime, telefon ili revers...")
        servisi = fetch_servisi(search_input)
        st.caption(f"Ukupno pronađeno servisa: **{len(servisi)}**")

        for s in servisi:
            status_val = str(s['status']).strip().lower()
            if status_val == "na servisu":
                status_color = "🔴"
            elif status_val in ["završeno", "zavrseno", "izdato", "preuzeto"]:
                status_color = "🟢"
            else:
                status_color = "⚪"
            
            with st.expander(f"{status_color} **{s['broj_reversa']}** — {s['vlasnik']} ({s['marka_model']})"):
                st.markdown(f"**📞 Telefon:** {s['telefon']}")
                st.markdown(f"**📅 Datum prijema:** {s['datum_prijema']}")
                st.markdown(f"**🔐 Win Pass:** `{s['win_password'] or 'Nema'}`")
                st.markdown(f"**🔌 Oprema:** {s['oprema'] or 'Samo uređaj'}")
                st.markdown(f"**⚠️ Opis kvara:** {s['opis_kvara']}")
                
                if s['bitni_podaci']:
                    st.warning(f"💾 Bitni podaci: {s['bitni_podaci']}")
                    
                st.divider()
                
                with st.form(key=f"form_servis_{s['id']}"):
                    st.subheader("Ažuriranje servisa")
                    statuses = ["Na servisu", "Završeno", "Izdato", "Preuzeto", "Otkazano"]
                    try:
                        curr_idx = [st_item.lower() for st_item in statuses].index(status_val)
                    except ValueError:
                        curr_idx = 0
                    
                    new_status = st.selectbox("Status:", statuses, index=curr_idx, key=f"status_{s['id']}")
                    new_radovi = st.text_area("Urađeni radovi / zamenjeni delovi:", value=s['opis_radova'] or "", key=f"radovi_{s['id']}")
                    new_cena = st.text_input("Cena (RSD):", value=s['cena'] or "", key=f"cena_{s['id']}")
                    
                    submit_btn = st.form_submit_button("💾 Sačuvaj izmene")
                    if submit_btn:
                        update_servis_in_db(s['id'], new_status, new_radovi, new_cena)
                        st.success("Uspešno sačuvano u Cloud bazi!")
                        st.rerun()
    else:
        search_input_p = st.text_input("🔍 Pretraga prodaje (Račun, Kupac, Telefon, Stavke):", placeholder="Ukucaj račun, kupca ili artikal...")
        prodaje = fetch_prodaja(search_input_p)
        st.caption(f"Ukupno pronađeno prodaja: **{len(prodaje)}**")

        for p in prodaje:
            with st.expander(f"🛒 **{p['broj_racuna']}** — {p['ukupna_cena']} RSD ({p['vlasnik'] or 'Nepoznat vlasnik'})"):
                st.markdown(f"**📅 Datum prodaje:** {p['datum_prodaje']}")
                st.markdown(f"**📦 Stavke:** {p['stavke']}")
                st.markdown(f"**👤 Kupac:** {p['kupac'] or 'N/A'} ({p['telefon'] or 'N/A'})")
                st.markdown(f"**💳 Način plaćanja:** {p['nacin_placanja']}")
                if p['napomena']:
                    st.markdown(f"**📝 Napomena:** {p['napomena']}")
