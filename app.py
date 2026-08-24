import streamlit as st
from supabase import create_client


st.set_page_config(
    page_title="GARA FOLLOW-UP - Test RLS",
    page_icon="🔐"
)

st.title("GARA FOLLOW-UP")
st.subheader("Test autenticazione e RLS")


# -----------------------------------------------------
# CONFIGURAZIONE SUPABASE
# -----------------------------------------------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


# -----------------------------------------------------
# CLIENT SUPABASE
# -----------------------------------------------------

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# -----------------------------------------------------
# LOGIN
# -----------------------------------------------------

st.write("### Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")


if st.button("Accedi"):

    try:

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        st.session_state["session"] = response.session

        st.success("Login riuscito.")

    except Exception as e:

        st.error(f"Login fallito: {e}")


# -----------------------------------------------------
# TEST AUTENTICATO
# -----------------------------------------------------

if "session" in st.session_state:

    session = st.session_state["session"]

    st.write("### Sessione autenticata")

    st.success("Utente autenticato.")

    try:

        user = supabase.auth.get_user()

        st.write("**Auth UID:**")
        st.code(user.user.id)

        # ---------------------------------------------
        # TEST get_mia_azienda_id()
        # ---------------------------------------------

        result = supabase.rpc(
            "get_mia_azienda_id"
        ).execute()

        st.write("**Azienda dell'utente:**")

        st.code(str(result.data))

        # ---------------------------------------------
        # TEST RLS - AZIENDA
        # ---------------------------------------------

        aziende = (
            supabase
            .table("azienda")
            .select("id, nome")
            .execute()
        )

        st.write("### Test RLS - azienda")

        st.write(aziende.data)

        # ---------------------------------------------
        # TEST RLS - UTENTI
        # ---------------------------------------------

        utenti = (
            supabase
            .table("utenti")
            .select("id, azienda_id, nome, ruolo")
            .execute()
        )

        st.write("### Test RLS - utenti")

        st.write(utenti.data)

    except Exception as e:

        st.error(f"Errore durante il test: {e}")
