import streamlit as st
from datetime import date

from services.supabase_client import get_supabase_client
from services.auth import login
from services.azienda import get_mia_azienda
from services.gare import (
    get_gare,
    crea_gara,
    aggiorna_gara,
)


# =====================================================
# CONFIGURAZIONE
# =====================================================

st.set_page_config(
    page_title="GARA FOLLOW-UP",
    page_icon="📋",
    layout="wide",
)


# =====================================================
# SUPABASE
# =====================================================

supabase = get_supabase_client()


# =====================================================
# SESSIONE
# =====================================================

if "session" in st.session_state:

    try:

        supabase.auth.set_session(
            st.session_state["session"].access_token,
            st.session_state["session"].refresh_token,
        )

    except Exception:

        del st.session_state["session"]
        st.rerun()


# =====================================================
# LOGIN
# =====================================================

if "session" not in st.session_state:

    st.title("📋 GARA FOLLOW-UP")

    st.subheader("Accedi")

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password",
    )

    if st.button(
        "Accedi",
        type="primary",
        use_container_width=True,
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
                    password,
                )

                st.session_state["session"] = (
                    response.session
                )

                supabase.auth.set_session(
                    response.session.access_token,
                    response.session.refresh_token,
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Login fallito: {e}"
                )

    st.stop()


# =====================================================
# MESSAGGIO SUCCESSO
# =====================================================

if "messaggio_successo" in st.session_state:

    st.success(
        st.session_state["messaggio_successo"]
    )

    del st.session_state[
        "messaggio_successo"
    ]


# =====================================================
# CARICAMENTO UTENTE / AZIENDA
# =====================================================

try:

    user_response = supabase.auth.get_user()

    user = user_response.user

    azienda = get_mia_azienda(
        supabase
    )

    if not azienda:

        st.error(
            "Nessuna azienda associata all'utente."
        )

        st.stop()

    azienda_id = azienda["id"]

    gare = get_gare(
        supabase,
        azienda_id,
    )

except Exception as e:

    st.error(
        f"Errore caricamento dati: {e}"
    )

    st.stop()


# =====================================================
# FUNZIONI DATI
# =====================================================

def get_attivita():

    if not gare:
        return []

    gara_ids = [
        gara["id"]
        for gara in gare
    ]

    response = (
        supabase
        .table("attivita")
        .select("*")
        .in_("gara_id", gara_ids)
        .order(
            "data_prevista",
            desc=False,
        )
        .execute()
    )

    return response.data or []


def get_reminder():

    attivita = get_attivita()

    if not attivita:
        return []

    attivita_ids = [
        attivita_item["id"]
        for attivita_item in attivita
    ]

    response = (
        supabase
        .table("reminder")
        .select("*")
        .in_(
            "attivita_id",
            attivita_ids,
        )
        .order(
            "data_prevista",
            desc=False,
        )
        .execute()
    )

    return response.data or []


def get_storico(gara_id):

    response = (
        supabase
        .table("storico_stati")
        .select(
            "id, gara_id, stato_precedente, "
            "nuovo_stato, created_at"
        )
        .eq(
            "gara_id",
            gara_id,
        )
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def aggiorna_attivita(
    attivita_id,
    stato_attivita,
):

    response = (
        supabase
        .table("attivita")
        .update(
            {
                "stato_attivita": stato_attivita,
                "updated_at": "now()",
            }
        )
        .eq(
            "id",
            attivita_id,
        )
        .execute()
    )

    return response.data


def aggiorna_reminder(
    attivita_id,
    stato,
):

    response = (
        supabase
        .table("reminder")
        .update(
            {
                "stato": stato,
            }
        )
        .eq(
            "attivita_id",
            attivita_id,
        )
        .eq(
            "stato",
            "PENDENTE",
        )
        .execute()
    )

    return response.data


def chiudi_gara(
    gara_id,
):

    response = supabase.rpc(
        "chiudi_gara",
        {
            "p_gara_id": gara_id,
        },
    ).execute()

    return response.data


def riapri_gara(
    gara_id,
):

    response = supabase.rpc(
        "riapri_gara",
        {
            "p_gara_id": gara_id,
        },
    ).execute()

    return response.data


# =====================================================
# DATI WORKFLOW
# =====================================================

try:

    attivita = get_attivita()

except Exception as e:

    attivita = []

    st.warning(
        f"Impossibile caricare le attività: {e}"
    )


try:

    reminder = get_reminder()

except Exception as e:

    reminder = []

    st.warning(
        f"Impossibile caricare i reminder: {e}"
    )


# =====================================================
# STATISTICHE
# =====================================================

attivita_aperte = [
    item
    for item in attivita
    if item.get("stato_attivita") == "APERTA"
]

reminder_pendenti = [
    item
    for item in reminder
    if item.get("stato") == "PENDENTE"
]

oggi = date.today()

attivita_scadute = [
    item
    for item in attivita_aperte
    if item.get("data_prevista")
    and str(item["data_prevista"]) < str(oggi)
]

reminder_scaduti = [
    item
    for item in reminder_pendenti
    if item.get("data_prevista")
    and str(item["data_prevista"]) < str(oggi)
]


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title(
        "📋 GARA FOLLOW-UP"
    )

    st.divider()

    st.write(
        "👤 Utente"
    )

    st.caption(
        user.email
        if user
        else "-"
    )

    st.write(
        "🏢 Azienda"
    )

    st.caption(
        azienda.get("nome", "-")
    )

    st.divider()

    pagina = st.radio(
        "Navigazione",
        [
            "Dashboard",
            "Gare",
            "Attività",
        ],
    )

    st.divider()

    if st.button(
        "Esci",
        use_container_width=True,
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

    st.title(
        "Dashboard"
    )

    st.subheader(
        "Panoramica"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Gare",
            len(gare),
        )

    with col2:

        st.metric(
            "Attività aperte",
            len(attivita_aperte),
        )

    with col3:

        st.metric(
            "Reminder pendenti",
            len(reminder_pendenti),
        )

    with col4:

        st.metric(
            "Scadute",
            len(attivita_scadute),
        )

    st.divider()

    # -----------------------------------------------
    # ATTIVITÀ URGENTI
    # -----------------------------------------------

    st.subheader(
        "⚠️ Da fare"
    )

    if not attivita_aperte:

        st.success(
            "Non ci sono attività aperte."
        )

    else:

        for item in attivita_aperte:

            gara = next(
                (
                    gara
                    for gara in gare
                    if gara["id"] == item["gara_id"]
                ),
                None,
            )

            gara_nome = (
                gara["oggetto"]
                if gara
                else "Gara"
            )

            data_prevista = (
                item.get("data_prevista")
                or "-"
            )

            if (
                item.get("data_prevista")
                and str(item["data_prevista"])
                < str(oggi)
            ):

                icona = "🔴"

            elif (
                item.get("data_prevista")
                and str(item["data_prevista"])
                == str(oggi)
            ):

                icona = "🟠"

            else:

                icona = "🟢"

            with st.container(
                border=True
            ):

                st.write(
                    f"{icona} **{item.get('titolo', 'Attività')}**"
                )

                st.caption(
                    f"Gara: {gara_nome}"
                )

                st.caption(
                    f"Scadenza: {data_prevista}"
                )

    st.divider()

    # -----------------------------------------------
    # GARE PER STATO
    # -----------------------------------------------

    st.subheader(
        "Stato delle gare"
    )

    stati = {}

    for gara in gare:

        stato = gara.get(
            "stato",
            "SCONOSCIUTO",
        )

        stati[stato] = (
            stati.get(stato, 0) + 1
        )

    if stati:

        for stato, numero in sorted(
            stati.items()
        ):

            st.write(
                f"**{stato}**: {numero}"
            )

    else:

        st.info(
            "Nessuna gara presente."
        )


# =====================================================
# GARE
# =====================================================

elif pagina == "Gare":

    st.title(
        "Gare"
    )

    # =================================================
    # NUOVA GARA
    # =================================================

    with st.expander(
        "➕ Nuova gara",
        expanded=False,
    ):

        cig = st.text_input(
            "CIG",
            key="nuova_cig",
        )

        oggetto = st.text_input(
            "Oggetto *",
            key="nuovo_oggetto",
        )

        stazione_appaltante = st.text_input(
            "Stazione appaltante *",
            key="nuova_stazione",
        )

        importo = st.number_input(
            "Importo",
            min_value=0.0,
            step=1000.0,
            key="nuovo_importo",
        )

        link_portale = st.text_input(
            "Link portale",
            key="nuovo_link",
        )

        data_apertura_prevista = st.date_input(
            "Data apertura prevista",
            value=None,
            key="nuova_data_prevista",
        )

        data_apertura_effettiva = st.date_input(
            "Data apertura effettiva",
            value=None,
            key="nuova_data_effettiva",
        )

        if st.button(
            "Salva gara",
            type="primary",
            key="crea_gara",
        ):

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
                    "stazione_appaltante":
                        stazione_appaltante.strip(),
                    "importo": importo,
                    "link_portale":
                        link_portale.strip() or None,
                    "data_apertura_prevista":
                        data_apertura_prevista,
                    "data_apertura_effettiva":
                        data_apertura_effettiva,
                }

                try:

                    crea_gara(
                        supabase,
                        azienda_id,
                        dati,
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
    # ELENCO
    # =================================================

    st.divider()

    st.subheader(
        f"Gare esistenti ({len(gare)})"
    )

    if not gare:

        st.info(
            "Non ci sono gare."
        )

    else:

        for gara in gare:

            stato = gara.get(
                "stato",
                "-",
            )

            if stato == "CHIUSA":

                colore = "🔒"

            elif stato == "VINTA":

                colore = "🏆"

            elif stato == "PERSA":

                colore = "❌"

            elif stato == "BUSTE_APERTE":

                colore = "📂"

            else:

                colore = "⏳"

            with st.container(
                border=True
            ):

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    st.write(
                        f"### {gara['oggetto']}"
                    )

                    st.caption(
                        f"CIG: {gara.get('cig') or '-'}"
                    )

                    st.caption(
                        "Stazione appaltante: "
                        f"{gara.get('stazione_appaltante', '-')}"
                    )

                    st.caption(
                        f"Stato: {colore} {stato}"
                    )

                with col2:

                    if gara.get(
                        "importo"
                    ) is not None:

                        st.write(
                            f"€ {float(gara['importo']):,.2f}"
                        )

                    if st.button(
                        "Apri gara",
                        key=f"apri_{gara['id']}",
                        use_container_width=True,
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
            None,
        )

        if not gara_selezionata:

            st.warning(
                "La gara selezionata non è più disponibile."
            )

            del st.session_state[
                "gara_selezionata"
            ]

        else:

            st.divider()

            st.subheader(
                "Dettaglio gara"
            )

            st.write(
                f"## {gara_selezionata['oggetto']}"
            )

            stato = gara_selezionata.get(
                "stato",
                "-",
            )

            if stato == "CHIUSA":

                st.warning(
                    "🔒 Gara chiusa"
                )

            elif stato == "VINTA":

                st.success(
                    "🏆 Gara vinta"
                )

            elif stato == "PERSA":

                st.error(
                    "❌ Gara persa"
                )

            elif stato == "BUSTE_APERTE":

                st.info(
                    "📂 Buste aperte"
                )

            else:

                st.info(
                    f"⏳ {stato}"
                )

            # -----------------------------------------
            # DATI
            # -----------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**CIG:** "
                    f"{gara_selezionata.get('cig') or '-'}"
                )

                st.write(
                    "**Stazione appaltante:** "
                    f"{gara_selezionata.get('stazione_appaltante') or '-'}"
                )

                st.write(
                    "**Importo:** "
                    + (
                        f"€ {float(gara_selezionata['importo']):,.2f}"
                        if gara_selezionata.get(
                            "importo"
                        ) is not None
                        else "-"
                    )
                )

                st.write(
                    "**Ribasso proprio:** "
                    f"{gara_selezionata.get('ribasso_proprio') or '-'}"
                )

            with col2:

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

            link = gara_selezionata.get(
                "link_portale"
            )

            if link:

                st.link_button(
                    "🌐 Apri portale",
                    link,
                )

            st.write(
                "**Ultimo aggiornamento:** "
                f"{gara_selezionata.get('ultimo_aggiornamento') or '-'}"
            )

            # -----------------------------------------
            # AZIONI WORKFLOW
            # -----------------------------------------

            st.divider()

            st.subheader(
                "Workflow"
            )

            if stato == "CHIUSA":

                if st.button(
                    "🔓 Riapri gara",
                    type="primary",
                    key=f"riapri_{gara_id}",
                ):

                    try:

                        riapri_gara(
                            gara_id
                        )

                        st.session_state[
                            "messaggio_successo"
                        ] = (
                            "✅ Gara riaperta. "
                            "Il workflow è stato rivalutato."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Errore riapertura gara: {e}"
                        )

            else:

                if st.button(
                    "🔒 Chiudi gara",
                    key=f"chiudi_{gara_id}",
                ):

                    try:

                        chiudi_gara(
                            gara_id
                        )

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

            # -----------------------------------------
            # MODIFICA DATI
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
                key=f"modifica_cig_{gara_id}",
            )

            modifica_oggetto = st.text_input(
                "Oggetto",
                value=(
                    gara_selezionata.get(
                        "oggetto"
                    ) or ""
                ),
                key=f"modifica_oggetto_{gara_id}",
            )

            modifica_stazione = st.text_input(
                "Stazione appaltante",
                value=(
                    gara_selezionata.get(
                        "stazione_appaltante"
                    ) or ""
                ),
                key=f"modifica_stazione_{gara_id}",
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
                key=f"modifica_importo_{gara_id}",
            )

            modifica_link = st.text_input(
                "Link portale",
                value=(
                    gara_selezionata.get(
                        "link_portale"
                    ) or ""
                ),
                key=f"modifica_link_{gara_id}",
            )

            modifica_vincitore = st.text_input(
                "Vincitore",
                value=(
                    gara_selezionata.get(
                        "vincitore"
                    ) or ""
                ),
                key=f"modifica_vincitore_{gara_id}",
            )

            modifica_ribasso_proprio = st.text_input(
                "Ribasso proprio",
                value=(
                    gara_selezionata.get(
                        "ribasso_proprio"
                    ) or ""
                ),
                key=f"modifica_ribasso_proprio_{gara_id}",
            )

            modifica_ribasso_vincitore = st.text_input(
                "Ribasso vincitore",
                value=(
                    gara_selezionata.get(
                        "ribasso_vincitore"
                    ) or ""
                ),
                key=f"modifica_ribasso_vincitore_{gara_id}",
            )

            modifica_ultimo_aggiornamento = st.text_area(
                "Ultimo aggiornamento",
                value=(
                    gara_selezionata.get(
                        "ultimo_aggiornamento"
                    ) or ""
                ),
                key=f"modifica_ultimo_aggiornamento_{gara_id}",
            )

            if st.button(
                "💾 Salva modifiche",
                type="primary",
                key=f"salva_modifiche_{gara_id}",
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
                        "cig":
                            modifica_cig.strip()
                            or None,

                        "oggetto":
                            modifica_oggetto.strip(),

                        "stazione_appaltante":
                            modifica_stazione.strip(),

                        "importo":
                            modifica_importo,

                        "link_portale":
                            modifica_link.strip()
                            or None,

                        "vincitore":
                            modifica_vincitore.strip()
                            or None,

                        "ribasso_proprio":
                            modifica_ribasso_proprio.strip()
                            or None,

                        "ribasso_vincitore":
                            modifica_ribasso_vincitore.strip()
                            or None,

                        "ultimo_aggiornamento":
                            modifica_ultimo_aggiornamento.strip()
                            or None,
                    }

                    try:

                        aggiorna_gara(
                            supabase,
                            azienda_id,
                            gara_id,
                            dati_modifica,
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
            # STORICO
            # -----------------------------------------

            st.divider()

            st.subheader(
                "Storico stati"
            )

            try:

                storico = get_storico(
                    gara_id
                )

                if not storico:

                    st.info(
                        "Nessuna transizione registrata."
                    )

                else:

                    for evento in storico:

                        precedente = (
                            evento.get(
                                "stato_precedente"
                            )
                            or "-"
                        )

                        nuovo = (
                            evento.get(
                                "nuovo_stato"
                            )
                            or "-"
                        )

                        created_at = (
                            evento.get(
                                "created_at"
                            )
                            or "-"
                        )

                        st.write(
                            f"**{precedente} → {nuovo}**"
                        )

                        st.caption(
                            str(created_at)
                        )

            except Exception as e:

                st.warning(
                    f"Errore caricamento storico: {e}"
                )


# =====================================================
# ATTIVITÀ
# =====================================================

elif pagina == "Attività":

    st.title(
        "Attività"
    )

    st.subheader(
        "Workflow operativo"
    )

    # -----------------------------------------------
    # FILTRI
    # -----------------------------------------------

    filtro = st.selectbox(
        "Mostra",
        [
            "Tutte",
            "Aperte",
            "Completate",
            "Annullate",
        ],
    )

    attivita_filtrate = attivita

    if filtro == "Aperte":

        attivita_filtrate = [
            item
            for item in attivita
            if item.get(
                "stato_attivita"
            ) == "APERTA"
        ]

    elif filtro == "Completate":

        attivita_filtrate = [
            item
            for item in attivita
            if item.get(
                "stato_attivita"
            ) == "COMPLETATA"
        ]

    elif filtro == "Annullate":

        attivita_filtrate = [
            item
            for item in attivita
            if item.get(
                "stato_attivita"
            ) == "ANNULLATA"
        ]

    # -----------------------------------------------
    # ELENCO
    # -----------------------------------------------

    if not attivita_filtrate:

        st.info(
            "Nessuna attività trovata."
        )

    else:

        for item in attivita_filtrate:

            gara = next(
                (
                    gara
                    for gara in gare
                    if gara["id"]
                    == item["gara_id"]
                ),
                None,
            )

            gara_nome = (
                gara["oggetto"]
                if gara
                else "Gara non trovata"
            )

            stato_attivita = item.get(
                "stato_attivita",
                "-",
            )

            if stato_attivita == "APERTA":

                icona = "🟠"

            elif stato_attivita == "COMPLETATA":

                icona = "✅"

            else:

                icona = "⚪"

            with st.container(
                border=True
            ):

                st.write(
                    f"{icona} **{item.get('titolo', 'Attività')}**"
                )

                st.caption(
                    f"Gara: {gara_nome}"
                )

                col1, col2, col3 = st.columns(
                    3
                )

                with col1:

                    st.write(
                        f"**Tipo:** "
                        f"{item.get('tipo', '-')}"
                    )

                with col2:

                    st.write(
                        f"**Stato:** "
                        f"{stato_attivita}"
                    )

                with col3:

                    st.write(
                        f"**Data prevista:** "
                        f"{item.get('data_prevista') or '-'}"
                    )

                if item.get(
                    "descrizione"
                ):

                    st.write(
                        item["descrizione"]
                    )

                if item.get(
                    "motivo"
                ):

                    st.caption(
                        f"Motivo: {item['motivo']}"
                    )

                # -----------------------------------
                # AZIONI
                # -----------------------------------

                if stato_attivita == "APERTA":

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "✅ Completa",
                            key=f"completa_{item['id']}",
                            use_container_width=True,
                        ):

                            try:

                                aggiorna_attivita(
                                    item["id"],
                                    "COMPLETATA",
                                )

                                aggiorna_reminder(
                                    item["id"],
                                    "COMPLETATO",
                                )

                                st.session_state[
                                    "messaggio_successo"
                                ] = (
                                    "✅ Attività completata."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Errore: {e}"
                                )

                    with col2:

                        if st.button(
                            "🚫 Annulla",
                            key=f"annulla_{item['id']}",
                            use_container_width=True,
                        ):

                            try:

                                aggiorna_attivita(
                                    item["id"],
                                    "ANNULLATA",
                                )

                                aggiorna_reminder(
                                    item["id"],
                                    "ANNULLATO",
                                )

                                st.session_state[
                                    "messaggio_successo"
                                ] = (
                                    "Attività annullata."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Errore: {e}"
                                )

    # -----------------------------------------------
    # REMINDER
    # -----------------------------------------------

    st.divider()

    st.subheader(
        "🔔 Reminder"
    )

    if not reminder_pendenti:

        st.success(
            "Nessun reminder pendente."
        )

    else:

        for rem in reminder_pendenti:

            attivita_reminder = next(
                (
                    item
                    for item in attivita
                    if item["id"]
                    == rem["attivita_id"]
                ),
                None,
            )

            titolo = (
                attivita_reminder.get(
                    "titolo"
                )
                if attivita_reminder
                else "Attività"
            )

            data_reminder = (
                rem.get(
                    "data_prevista"
                )
                or "-"
            )

            if (
                rem.get("data_prevista")
                and str(rem["data_prevista"])
                < str(oggi)
            ):

                st.error(
                    f"🔴 **{titolo}** — scaduto: {data_reminder}"
                )

            elif (
                rem.get("data_prevista")
                and str(rem["data_prevista"])
                == str(oggi)
            ):

                st.warning(
                    f"🟠 **{titolo}** — oggi"
                )

            else:

                st.info(
                    f"🔵 **{titolo}** — {data_reminder}"
                )
