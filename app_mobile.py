import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz

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
    conn.commit()
    cursor.close()
    conn.close()

def fix_id_sequence():
    """Popravlja PostgreSQL brojač (sequence) ako je ispao iz sinhronizacije"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT setval(pg_get_serial_sequence('servisi', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM servisi;")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass

def get_local_now_str():
    """Vraća tačno lokalno vreme za Srbiju (Europe/Belgrade)"""
    try:
        tz = pytz.timezone("Europe/Belgrade")
        return datetime.now(tz).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d.%m.%Y %H:%M")

def generate_broj_reversa():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        year = datetime.now().strftime("%Y")
        cursor.execute("SELECT COUNT(*) as count FROM servisi WHERE broj_reversa LIKE %s", (f"%/{year}",))
        row = cursor.fetchone()
        count = (row['count'] if row else 0) + 1
        cursor.close()
        conn.close()
        return f"{count:04d}/{year}"
    except Exception:
        return "0001/" + datetime.now().strftime("%Y")

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

# Inicijalizacija baze i sinhronizacija brojača ID-eva pri pokretanju
try:
    init_supabase_db()
    fix_id_sequence()
except Exception as e:
    st.error(f"Greška pri povezivanju sa bazom: {e}")

st.title("🔧 MiloNet Mobile")
st.caption("Cloud baza radnih naloga i klijenata")

# Navigacija preko Tab-ova na telefonu
tab_prijem, tab_pretraga = st.tabs(["➕ Nov Prijem", "🔍 Pretraga & Baza"])

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
        napomena = st.text_area("Napomena", placeholder="Interna napomena...")

        submitted = st.form_submit_button("💾 Sačuvaj prijem u bazu", use_container_width=True)

        if submitted:
            if not vlasnik or not telefon or not model or not kvar:
                st.error("⚠️ Molimo vas popunite obavezna polja (Vlasnik, Telefon, Model, Kvar).")
            else:
                try:
                    fix_id_sequence()
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

# --- TAB 2: PRETRAGA I STATUSI ---
with tab_pretraga:
    search_input = st.text_input("🔍 Pretraga (Revers, Vlasnik, Telefon, Model):", placeholder="Ukucaj ime, telefon ili revers...")

    servisi = fetch_servisi(search_input)
    st.caption(f"Ukupno pronađeno: **{len(servisi)}**")

    for s in servisi:
        # Prikaz statusa u boji (Crveno = Na servisu, Zeleno = Završeno/Izdato/Preuzeto)
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
            
            with st.form(key=f"form_{s['id']}"):
                st.subheader("Ažuriranje servisa")
                
                statuses = ["Na servisu", "Završeno", "Izdato", "Preuzeto", "Otkazano"]
                
                # Provera trenutnog indeksa iz liste statusa
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
