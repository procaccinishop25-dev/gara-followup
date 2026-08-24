import streamlit as st

from services.supabase_client import get_supabase_client
from services.auth import login
from services.azienda import (
    get_mia_azienda
)
from services.gare import (
    get_gare,
    crea_gara,
    aggiorna_gara
)



# =====================================================
# CONFIGURAZIONE
# =====================================================

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

    email = st.text_input(
        "Email"
    )

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

    # -------------------------------------------------
    # NUOVA GARA
    # -------------------------------------------------

    st.subheader("Nuova gara")

    cig = st.text_input(
        "CIG"
    )

    oggetto = st.text_input(
        "Oggetto *"
    )

    stazione_appaltante = st.text_input(
        "Stazione appaltante *"
    )

    importo = st.number_input(
        "Importo",
        min_value=0.0,
        step=1000.0
    )

    link_portale = st.text_input(
        "Link portale"
    )

    data_apertura_prevista = st.date_input(
        "Data apertura prevista",
        value=None
    )

    data_apertura_effettiva = st.date_input(
        "Data apertura effettiva",
        value=None
    )

    if st.button("Salva gara"):

        if not oggetto or not stazione_appaltante:

            st.error(
                "Compila i campi obbligatori."
            )

        else:

            dati = {
                "cig": cig or None,
                "oggetto": oggetto,
                "stazione_appaltante": stazione_appaltante,
                "importo": importo,
                "link_portale": link_portale or None,
                "data_apertura_prevista": (
                    data_apertura_prevista
                ),
                "data_apertura_effettiva": (
                    data_apertura_effettiva
                )
            }

            try:

                crea_gara(
                    supabase,
                    azienda_id,
                    dati
                )

                st.success(
                    "✅ Gara salvata correttamente."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Errore nel salvataggio: {e}"
                )

    # -------------------------------------------------
    # ELENCO GARE
    # -------------------------------------------------

    st.divider()

    st.subheader("Gare esistenti")

    if not gare:

        st.info(
            "Non ci sono gare."
        )

    else:

        for gara in gare:

            with st.container(border=True):

                col1, col2 = st.columns(
                    [3, 1]
                )

                with col1:

                    st.write(
                        f"**{gara['oggetto']}**"
                    )

                    st.caption(
                        f"CIG: {gara.get('cig') or '-'}"
                    )

                    st.caption(
                        "Stazione appaltante: "
                        f"{gara['stazione_appaltante']}"
                    )

                with col2:

                    st.write(
                        f"**{gara['stato']}**"
                    )

                    if gara.get("importo") is not None:

                        st.write(
                            f"€ {gara['importo']:,.2f}"
                        )

                    if st.button(
                        "Apri gara",
                        key=f"apri_{gara['id']}"
                    ):

                        st.session_state[
                            "gara_selezionata"
                        ] = gara["id"]

                        st.rerun()

    # -------------------------------------------------
    # DETTAGLIO GARA
    # -------------------------------------------------

    gara_id = st.session_state.get(
        "gara_selezionata"
    )

    if gara_id:

        gara_selezionata = next(
            (
                gara
                for gara in gare
                if gara["id"] == gara_id
            ),
            None
        )

if gara_selezionata:

    st.divider()

    st.subheader(
        "Dettaglio gara"
    )

    st.write(
        f"### {gara_selezionata['oggetto']}"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "**CIG:** "
            f"{gara_selezionata.get('cig') or '-'}"
        )

        st.write(
            "**Stazione appaltante:** "
            f"{gara_selezionata['stazione_appaltante']}"
        )

        st.write(
            "**Stato:** "
            f"{gara_selezionata['stato']}"
        )

        st.write(
            "**Ribasso proprio:** "
            f"{gara_selezionata.get('ribasso_proprio') or '-'}"
        )

    with col2:

        importo_gara = gara_selezionata.get(
            "importo"
        )

        if importo_gara is not None:

            st.write(
                "**Importo:** "
                f"€ {importo_gara:,.2f}"
            )

        else:

            st.write(
                "**Importo:** -"
            )

        st.write(
            "**Link portale:** "
            f"{gara_selezionata.get('link_portale') or '-'}"
        )

        st.write(
            "**Apertura prevista:** "
            f"{gara_selezionata.get('data_apertura_prevista') or '-'}"
        )

        st.write(
            "**Apertura effettiva:** "
            f"{gara_selezionata.get('data_apertura_effettiva') or '-'}"
        )

        st.write(
            "**Vincitore:** "
            f"{gara_selezionata.get('vincitore') or '-'}"
        )

        st.write(
            "**Ribasso vincitore:** "
            f"{gara_selezionata.get('ribasso_vincitore') or '-'}"
        )

    st.write(
        "**Ultimo aggiornamento:** "
        f"{gara_selezionata.get('ultimo_aggiornamento') or '-'}"
    )

    st.divider()

    st.subheader(
        "Modifica gara"
    )

    modifica_cig = st.text_input(
        "CIG",
        value=gara_selezionata.get("cig") or "",
        key="modifica_cig"
    )

    modifica_oggetto = st.text_input(
        "Oggetto",
        value=gara_selezionata.get("oggetto") or "",
        key="modifica_oggetto"
    )

    modifica_stazione = st.text_input(
        "Stazione appaltante",
        value=gara_selezionata.get(
            "stazione_appaltante"
        ) or "",
        key="modifica_stazione"
    )

    modifica_importo = st.number_input(
        "Importo",
        min_value=0.0,
        value=float(
            gara_selezionata.get("importo") or 0
        ),
        step=1000.0,
        key="modifica_importo"
    )

    modifica_link = st.text_input(
        "Link portale",
        value=gara_selezionata.get(
            "link_portale"
        ) or "",
        key="modifica_link"
    )

    modifica_vincitore = st.text_input(
        "Vincitore",
        value=gara_selezionata.get(
            "vincitore"
        ) or "",
        key="modifica_vincitore"
    )

    modifica_ribasso_proprio = st.text_input(
        "Ribasso proprio",
        value=gara_selezionata.get(
            "ribasso_proprio"
        ) or "",
        key="modifica_ribasso_proprio"
    )

    modifica_ribasso_vincitore = st.text_input(
        "Ribasso vincitore",
        value=gara_selezionata.get(
            "ribasso_vincitore"
        ) or "",
        key="modifica_ribasso_vincitore"
    )

    modifica_ultimo_aggiornamento = st.text_area(
        "Ultimo aggiornamento",
        value=gara_selezionata.get(
            "ultimo_aggiornamento"
        ) or "",
        key="modifica_ultimo_aggiornamento"
    )

    if st.button(
        "Salva modifiche",
        key="salva_modifiche_gara"
    ):

        if not modifica_oggetto or not modifica_stazione:

            st.error(
                "Oggetto e stazione appaltante sono obbligatori."
            )

        else:

            dati_modifica = {
                "cig": modifica_cig or None,
                "oggetto": modifica_oggetto,
                "stazione_appaltante": modifica_stazione,
                "importo": modifica_importo,
                "link_portale": modifica_link or None,
                "vincitore": modifica_vincitore or None,
                "ribasso_proprio": (
                    modifica_ribasso_proprio or None
                ),
                "ribasso_vincitore": (
                    modifica_ribasso_vincitore or None
                ),
                "ultimo_aggiornamento": (
                    modifica_ultimo_aggiornamento or None
                )
            }

            try:

                aggiorna_gara(
                    supabase,
                    azienda_id,
                    gara_id,
                    dati_modifica
                )

                st.success(
                    "✅ Gara aggiornata correttamente."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Errore aggiornamento gara: {e}"
                )

else:

    st.warning(
        "La gara selezionata non è più disponibile."
    )

    del st.session_state[
        "gara_selezionata"
    ]


                else:

                    st.write(
                        "**Importo:** -"
                    )

                st.write(
                    "**Link portale:** "
                    f"{gara_selezionata.get('link_portale') or '-'}"
                )

                st.write(
                    "**Apertura prevista:** "
                    f"{gara_selezionata.get('data_apertura_prevista') or '-'}"
                )

                st.write(
                    "**Apertura effettiva:** "
                    f"{gara_selezionata.get('data_apertura_effettiva') or '-'}"
                )

                st.write(
                    "**Vincitore:** "
                    f"{gara_selezionata.get('vincitore') or '-'}"
                )

                st.write(
                    "**Ribasso vincitore:** "
                    f"{gara_selezionata.get('ribasso_vincitore') or '-'}"
                )

            st.write(
                "**Ultimo aggiornamento:** "
                f"{gara_selezionata.get('ultimo_aggiornamento') or '-'}"
            )

        else:

            st.warning(
                "La gara selezionata non è più disponibile."
            )

            del st.session_state[
                "gara_selezionata"
            ]


# =====================================================
# ATTIVITÀ
# =====================================================

elif pagina == "Attività":

    st.title("Attività")

    st.info(
        "Gestione attività in costruzione."
    )
