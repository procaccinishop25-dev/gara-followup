import streamlit as st

from services.supabase_client import get_supabase_client
from services.auth import login
from services.azienda import get_mia_azienda_id


st.set_page_config(
    page_title="GARA FOLLOW-UP",
    page_icon="📋"
)


st.title("GARA FOLLOW-UP")
st.subheader("Accesso")


# -----------------------------------------------------
# SUPABASE
# -----------------------------------------------------

supabase = get_supabase_client()


# -----------------------------------------------------
# LOGIN
# -----------------------------------------------------

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

        st.success("Login riuscito.")

    except Exception as e:

        st.error(f"Login fallito: {e}")


# -----------------------------------------------------
# AREA AUTENTICATA
# -----------------------------------------------------

if "session" in st.session_state:

    st.success("Utente autenticato.")

    try:

        user = supabase.auth.get_user()

        st.write("### Utente")

        st.write(
            f"Auth UID: `{user.user.id}`"
        )

        azienda_id = get_mia_azienda_id(
            supabase
        )

        st.write("### Azienda")

        st.write(
            f"Azienda ID: `{azienda_id}`"
        )

    except Exception as e:

        st.error(
            f"Errore durante il caricamento: {e}"
        )
