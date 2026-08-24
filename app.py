import streamlit as st

from services.supabase_client import get_supabase_client
from services.auth import login
from services.azienda import (
    get_mia_azienda_id,
    get_mia_azienda
)
from services.gare import get_gare

st.set_page_config(
    page_title="GARA FOLLOW-UP",
    page_icon="📋",
    layout="wide"
)


# =====================================================
# SUPABASE
# =====================================================

supabase = get_supabase_client()

if "session" in st.session_state:

    supabase.auth.set_session(
        st.session_state["session"].access_token,
        st.session_state["session"].refresh_token
    )

# =====================================================
# LOGIN
# =====================================================

if "session" not in st.session_state:

    st.title("GARA FOLLOW-UP")

    st.subheader("Accedi")

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Accedi"):

        try:

            response = login(
                supabase,
                email,
                password
            )

            st.session_state["session"] = response.session

            supabase.auth.set_session(
                response.session.access_token,
                response.session.refresh_token
            )   

            st.rerun()

        except Exception as e:

            st.error(
                f"Login fallito: {e}"
            )

    st.stop()


# =====================================================
# UTENTE AUTENTICATO
# =====================================================

try:

    user = supabase.auth.get_user()

    azienda = get_mia_azienda(
        supabase
    )

    azienda_id = azienda["id"]
    
    gare = get_gare(
        supabase,
        azienda_id
    )
    
except Exception as e:
    
    st.error(
        f"Errore autenticazione: {e}"
    )

    st.stop()


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("GARA FOLLOW-UP")

    st.divider()

    st.write("👤 Utente")

    st.caption(
        st.session_state["session"].user.email
    )

    st.write("🏢 Azienda")

    st.caption(
        azienda["nome"]
    )

    st.divider()

    pagina = st.radio(
        "Navigazione",
        [
            "Dashboard",
            "Gare",
            "Attività"
        ]
    )


# =====================================================
# DASHBOARD
# =====================================================

# =====================================================
# DASHBOARD
# =====================================================

if pagina == "Dashboard":

    st.title("Dashboard")

    st.subheader(
        "Benvenuto in GARA FOLLOW-UP"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Gare",
            len(gare)
        )

    with col2:

        st.metric(
            "Attività aperte",
            "0"
        )

    with col3:

        st.metric(
            "Reminder",
            "0"
        )

    st.divider()

    st.info(
        "La dashboard verrà collegata ai dati reali nelle prossime fasi."
    )

# =====================================================
# GARE
# =====================================================

elif pagina == "Gare":

    st.title("Gare")

    st.info(
        "Gestione gare in costruzione."
    )


# =====================================================
# ATTIVITÀ
# =====================================================

elif pagina == "Attività":

    st.title("Attività")

    st.info(
        "Gestione attività in costruzione."
    )
