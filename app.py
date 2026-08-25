import streamlit as st

from services.supabase_client import get_supabase_client
from services.auth import login
from services.azienda import get_mia_azienda
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

    try:

        supabase.auth.set_session(
            st.session_state["session"].access_token,
            st.session_state["session"].refresh_token
        )

    except Exception:

        del st.session_state["session"]

        st.rerun()


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

    if st.button(
        "Accedi",
        type="primary"
    ):

        if not email or not password:

            st.error(
                "Inserisci email e password."
            )

        else:

            try:

                response = login(
                    supabase,
                    email,
                    password
                )

                st.session_state[
                    "session"
                ] = response.session

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
# MESSAGGI
# =====================================================

if "messaggio_successo" in st.session_state:

    st.success(
        st.session_state["messaggio_successo"]
    )

    del st.session_state[
        "messaggio_successo"
    ]


# =====================================================
# UTENTE AUTENTICATO
# =====================================================

try:

    user_response = supabase.auth.get_user()

    if not user_response or not user_response.user:

        del st.session_state["session"]

        st.rerun()

    azienda = get_mia_azienda(
        supabase
    )

    if not azienda:

        st.error(
            "Azienda dell'utente non trovata."
        )

        st.stop()

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
        user_response.user.email
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

    st.divider()

    if st.button(
        "Esci",
        use_container_width=True
    ):

        try:

            supabase.auth.sign_out()

        except Exception:

            pass

        st.session_state.clear()

        st.rerun()


# =====================================================
# DASHBOARD
# =====================================================

if pagina == "Dashboard":

    st.title("Dashboard")

    st.subheader(
        "Benvenuto in GARA FOLLOW-UP"
    )

    gare_totali = len(gare)

    gare_in_attesa = sum(
        1
        for gara in gare
        if gara.get("stato") == "IN_ATTESA_APERTURA"
    )

    gare_buste_aperte = sum(
        1
        for gara in gare
        if gara.get("stato") == "BUSTE_APERTE"
    )

    gare_vinte = sum(
        1
        for gara in gare
        if gara.get("stato") == "VINTA"
    )

    gare_chiuse = sum(
        1
        for gara in gare
        if gara.get("stato") == "CHIUSA"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Gare",
            gare_totali
        )

    with col2:

        st.metric(
            "In attesa",
            gare_in_attesa
        )

    with col3:

        st.metric(
            "Vinte",
            gare_vinte
        )

    with col4:

        st.metric(
            "Chiuse",
            gare_chiuse
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Buste aperte",
            gare_buste_aperte
        )

    with col2:

        st.metric(
            "Attività aperte",
            "—"
        )

    st.info(
        "La gestione completa di attività e reminder "
        "verrà collegata nelle prossime fasi."
    )


# =====================================================
# GARE
# =====================================================

elif pagina == "Gare":

    st.title("Gare")

    # =================================================
    # NUOVA GARA
    # =================================================

    st.subheader("Nuova gara")

    with st.form(
        "nuova_gara_form",
        clear_on_submit=True
    ):

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

        salva_nuova_gara = st.form_submit_button(
            "Salva gara",
            type="primary"
        )

    if salva_nuova_gara:

        if (
            not oggetto.strip()
            or not stazione_appaltante.strip()
        ):

            st.error(
                "Compila i campi obbligatori."
            )

        else:

            dati = {
                "cig": cig.strip() or None,
                "oggetto": oggetto.strip(),
                "stazione_appaltante": (
                    stazione_appaltante.strip()
                ),
                "importo": importo,
                "link_portale": (
                    link_portale.strip() or None
                ),
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

                st.session_state[
                    "messaggio_successo"
                ] = (
                    "✅ Gara salvata correttamente."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Errore nel salvataggio: {e}"
                )


    # =================================================
    # ELENCO GARE
    # =================================================

    st.divider()

    st.subheader("Gare esistenti")

    if not gare:

        st.info(
            "Non ci sono gare."
        )

    else:

        for gara in gare:

            with st.container(
                border=True
            ):

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

                    stato = gara.get(
                        "stato"
                    ) or "-"

                    st.write(
                        f"**{stato}**"
                    )

                    if gara.get("importo") is not None:

                        st.write(
                            f"€ {float(gara['importo']):,.2f}"
                        )

                    if st.button(
                        "Apri gara",
                        key=f"apri_{gara['id']}"
                    ):

                        st.session_state[
                            "gara_selezionata"
                        ] = gara["id"]

                        st.rerun()


    # =================================================
    # DETTAGLIO GARA
    # =================================================

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


            # -----------------------------------------
            # DATI GARA
            # -----------------------------------------

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
                    f"{gara_selezionata.get('stato') or '-'}"
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
                        f"€ {float(importo_gara):,.2f}"
                    )

                else:

                    st.write(
                        "**Importo:** -"
                    )

                link_portale_gara = (
                    gara_selezionata.get(
                        "link_portale"
                    )
                )

                if link_portale_gara:

                    st.write(
                        "**Link portale:**"
                    )

                    st.link_button(
                        "Apri portale",
                        link_portale_gara
                    )

                else:

                    st.write(
                        "**Link portale:** -"
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


            # -----------------------------------------
            # MODIFICA DATI GARA
            # -----------------------------------------

            st.divider()

            st.subheader(
                "Modifica dati gara"
            )

            modifica_cig = st.text_input(
                "CIG",
                value=(
                    gara_selezionata.get(
                        "cig"
                    ) or ""
                ),
                key=f"modifica_cig_{gara_id}"
            )

            modifica_oggetto = st.text_input(
                "Oggetto",
                value=(
                    gara_selezionata.get(
                        "oggetto"
                    ) or ""
                ),
                key=f"modifica_oggetto_{gara_id}"
            )

            modifica_stazione = st.text_input(
                "Stazione appaltante",
                value=(
                    gara_selezionata.get(
                        "stazione_appaltante"
                    ) or ""
                ),
                key=f"modifica_stazione_{gara_id}"
            )

            modifica_importo = st.number_input(
                "Importo",
                min_value=0.0,
                value=float(
                    gara_selezionata.get(
                        "importo"
                    ) or 0
                ),
                step=1000.0,
                key=f"modifica_importo_{gara_id}"
            )

            modifica_link = st.text_input(
                "Link portale",
                value=(
                    gara_selezionata.get(
                        "link_portale"
                    ) or ""
                ),
                key=f"modifica_link_{gara_id}"
            )

            modifica_data_apertura_prevista = st.date_input(
                "Data apertura prevista",
                value=(
                    gara_selezionata.get(
                        "data_apertura_prevista"
                    )
                ),
                key=f"modifica_data_prevista_{gara_id}"
            )

            modifica_data_apertura_effettiva = st.date_input(
                "Data apertura effettiva",
                value=(
                    gara_selezionata.get(
                        "data_apertura_effettiva"
                    )
                ),
                key=f"modifica_data_effettiva_{gara_id}"
            )

            modifica_vincitore = st.text_input(
                "Vincitore",
                value=(
                    gara_selezionata.get(
                        "vincitore"
                    ) or ""
                ),
                key=f"modifica_vincitore_{gara_id}"
            )

            modifica_ribasso_proprio = st.text_input(
                "Ribasso proprio",
                value=(
                    gara_selezionata.get(
                        "ribasso_proprio"
                    ) or ""
                ),
                key=f"modifica_ribasso_proprio_{gara_id}"
            )

            modifica_ribasso_vincitore = st.text_input(
                "Ribasso vincitore",
                value=(
                    gara_selezionata.get(
                        "ribasso_vincitore"
                    ) or ""
                ),
                key=f"modifica_ribasso_vincitore_{gara_id}"
            )

            modifica_ultimo_aggiornamento = st.text_area(
                "Ultimo aggiornamento",
                value=(
                    gara_selezionata.get(
                        "ultimo_aggiornamento"
                    ) or ""
                ),
                key=f"modifica_ultimo_aggiornamento_{gara_id}"
            )


            # -----------------------------------------
            # SALVATAGGIO DATI
            # -----------------------------------------

            if st.button(
                "Salva modifiche",
                key=f"salva_modifiche_gara_{gara_id}",
                type="primary"
            ):

                if (
                    not modifica_oggetto.strip()
                    or not modifica_stazione.strip()
                ):

                    st.error(
                        "Oggetto e stazione appaltante sono obbligatori."
                    )

                else:

                    dati_modifica = {
                        "cig": (
                            modifica_cig.strip()
                            or None
                        ),

                        "oggetto": (
                            modifica_oggetto.strip()
                        ),

                        "stazione_appaltante": (
                            modifica_stazione.strip()
                        ),

                        "importo": (
                            modifica_importo
                        ),

                        "link_portale": (
                            modifica_link.strip()
                            or None
                        ),

                        "data_apertura_prevista": (
                            modifica_data_apertura_prevista
                        ),

                        "data_apertura_effettiva": (
                            modifica_data_apertura_effettiva
                        ),

                        "vincitore": (
                            modifica_vincitore.strip()
                            or None
                        ),

                        "ribasso_proprio": (
                            modifica_ribasso_proprio.strip()
                            or None
                        ),

                        "ribasso_vincitore": (
                            modifica_ribasso_vincitore.strip()
                            or None
                        ),

                        "ultimo_aggiornamento": (
                            modifica_ultimo_aggiornamento.strip()
                            or None
                        )
                    }

                    try:

                        aggiorna_gara(
                            supabase,
                            azienda_id,
                            gara_id,
                            dati_modifica
                        )

                        st.session_state[
                            "messaggio_successo"
                        ] = (
                            "✅ Gara aggiornata correttamente."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Errore aggiornamento gara: {e}"
                        )


            # -----------------------------------------
            # AZIONI WORKFLOW
            # -----------------------------------------

            st.divider()

            st.subheader(
                "Azioni workflow"
            )

            stato_gara = gara_selezionata.get(
                "stato"
            )

            col1, col2 = st.columns(2)

            with col1:

                if stato_gara != "CHIUSA":

                    if st.button(
                        "🔒 Chiudi gara",
                        key=f"chiudi_{gara_id}"
                    ):

                        try:

                            supabase.rpc(
                                "chiudi_gara",
                                {
                                    "p_gara_id": gara_id
                                }
                            ).execute()

                            st.session_state[
                                "messaggio_successo"
                            ] = (
                                "✅ Gara chiusa correttamente."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Errore chiusura gara: {e}"
                            )

            with col2:

                if stato_gara == "CHIUSA":

                    if st.button(
                        "🔓 Riapri gara",
                        key=f"riapri_{gara_id}"
                    ):

                        try:

                            supabase.rpc(
                                "riapri_gara",
                                {
                                    "p_gara_id": gara_id
                                }
                            ).execute()

                            st.session_state[
                                "messaggio_successo"
                            ] = (
                                "✅ Gara riaperta correttamente."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Errore riapertura gara: {e}"
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
