import streamlit as st
from datetime import date, datetime, timezone

from services.supabase_client import get_supabase_client
from services.auth import login
from services.azienda import get_mia_azienda
from services.gare import (
    get_gare,
    crea_gara,
    aggiorna_gara,
)


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="GARA FOLLOW-UP",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# UI STYLE
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        background: #0f172a;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    .app-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        color: #64748b;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 750;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
    }

    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }

    .status-green {
        background: #dcfce7;
        color: #166534;
    }

    .status-red {
        background: #fee2e2;
        color: #991b1b;
    }

    .status-orange {
        background: #ffedd5;
        color: #9a3412;
    }

    .status-blue {
        background: #dbeafe;
        color: #1d4ed8;
    }

    .status-gray {
        background: #e5e7eb;
        color: #374151;
    }

    .card {
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        background: white;
        margin-bottom: 0.8rem;
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 750;
        color: #0f172a;
    }

    .card-muted {
        color: #64748b;
        font-size: 0.88rem;
    }

    .danger-text {
        color: #b91c1c;
        font-weight: 700;
    }

    .warning-text {
        color: #c2410c;
        font-weight: 700;
    }

    .success-text {
        color: #15803d;
        font-weight: 700;
    }

    .metric-card {
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem;
        background: #ffffff;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SUPABASE
# ============================================================

supabase = get_supabase_client()


# ============================================================
# SESSION
# ============================================================

if "session" in st.session_state:

    try:

        session = st.session_state["session"]

        supabase.auth.set_session(
            session.access_token,
            session.refresh_token,
        )

    except Exception:

        st.session_state.pop(
            "session",
            None,
        )

        st.rerun()


# ============================================================
# LOGIN
# ============================================================

if "session" not in st.session_state:

    st.markdown(
        '<div class="app-title">📋 GARA FOLLOW-UP</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-subtitle">'
        "Gestione gare, attività e follow-up operativo"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(
        [1, 1.5, 1]
    )

    with col2:

        st.subheader("Accedi")

        email = st.text_input(
            "Email",
            placeholder="nome@azienda.it",
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

            if (
                not email.strip()
                or not password
            ):

                st.error(
                    "Inserisci email e password."
                )

            else:

                try:

                    response = login(
                        supabase,
                        email.strip(),
                        password,
                    )

                    if not response.session:

                        raise Exception(
                            "Supabase non ha restituito una sessione."
                        )

                    st.session_state[
                        "session"
                    ] = response.session

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


# ============================================================
# HELPERS
# ============================================================

def invalidate_data():

    for key in [
        "cached_gare",
        "cached_attivita",
        "cached_reminder",
    ]:

        st.session_state.pop(
            key,
            None,
        )


def success(message):

    st.session_state[
        "messaggio_successo"
    ] = message


def show_success():

    message = st.session_state.pop(
        "messaggio_successo",
        None,
    )

    if message:

        st.success(message)


def stato_gara_ui(stato):

    mapping = {
        "CHIUSA": (
            "🔒",
            "status-gray",
        ),
        "VINTA": (
            "🏆",
            "status-green",
        ),
        "PERSA": (
            "❌",
            "status-red",
        ),
        "BUSTE_APERTE": (
            "📂",
            "status-blue",
        ),
        "IN_ATTESA_APERTURA": (
            "⏳",
            "status-orange",
        ),
    }

    return mapping.get(
        stato,
        ("•", "status-gray"),
    )


def stato_attivita_ui(stato):

    mapping = {
        "APERTA": (
            "🟠",
            "status-orange",
        ),
        "COMPLETATA": (
            "✅",
            "status-green",
        ),
        "ANNULLATA": (
            "🚫",
            "status-gray",
        ),
    }

    return mapping.get(
        stato,
        ("•", "status-gray"),
    )


def stato_reminder_ui(stato):

    mapping = {
        "PENDENTE": (
            "🔔",
            "status-orange",
        ),
        "INVIATO": (
            "✅",
            "status-green",
        ),
        "ANNULLATO": (
            "🚫",
            "status-gray",
        ),
    }

    return mapping.get(
        stato,
        ("•", "status-gray"),
    )


def data_scaduta(data_val):

    if not data_val:
        return False

    return str(data_val) < str(
        date.today()
    )


def data_oggi(data_val):

    if not data_val:
        return False

    return str(data_val) == str(
        date.today()
    )


def utc_now_iso():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# DATA ACCESS
# ============================================================

def load_gare():

    if "cached_gare" not in st.session_state:

        st.session_state[
            "cached_gare"
        ] = (
            get_gare(
                supabase,
                azienda_id,
            )
            or []
        )

    return st.session_state[
        "cached_gare"
    ]


def load_attivita(gare):

    if (
        "cached_attivita"
        not in st.session_state
    ):

        if not gare:

            st.session_state[
                "cached_attivita"
            ] = []

        else:

            gara_ids = [
                gara["id"]
                for gara in gare
            ]

            response = (
                supabase
                .table("attivita")
                .select("*")
                .in_(
                    "gara_id",
                    gara_ids,
                )
                .order(
                    "data_prevista",
                    desc=False,
                )
                .execute()
            )

            st.session_state[
                "cached_attivita"
            ] = (
                response.data or []
            )

    return st.session_state[
        "cached_attivita"
    ]


def load_reminder(attivita):

    if (
        "cached_reminder"
        not in st.session_state
    ):

        if not attivita:

            st.session_state[
                "cached_reminder"
            ] = []

        else:

            attivita_ids = [
                item["id"]
                for item in attivita
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

            st.session_state[
                "cached_reminder"
            ] = (
                response.data or []
            )

    return st.session_state[
        "cached_reminder"
    ]


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


# ============================================================
# MUTATIONS - ATTIVITÀ
# ============================================================

def aggiorna_attivita(
    attivita_id,
    stato_attivita,
):

    return (
        supabase
        .table("attivita")
        .update(
            {
                "stato_attivita":
                    stato_attivita,
                "updated_at":
                    utc_now_iso(),
            }
        )
        .eq(
            "id",
            attivita_id,
        )
        .execute()
    )


def aggiorna_reminder(
    attivita_id,
    stato,
):

    return (
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


# ============================================================
# MUTATIONS - WORKFLOW
# ============================================================

def chiudi_gara(gara_id):

    return (
        supabase
        .rpc(
            "chiudi_gara",
            {
                "p_gara_id": gara_id,
            },
        )
        .execute()
    )


def riapri_gara(gara_id):

    return (
        supabase
        .rpc(
            "riapri_gara",
            {
                "p_gara_id": gara_id,
            },
        )
        .execute()
    )


def rivaluta_workflow_gara(gara_id):

    return (
        supabase
        .rpc(
            "rivaluta_workflow_gara",
            {
                "p_gara_id": gara_id,
            },
        )
        .execute()
    )


def cambia_stato_gara(
    gara_id,
    stato,
    dati_extra=None,
):

    dati = {
        "stato": stato,
    }

    if dati_extra:
        dati.update(
            dati_extra
        )

    aggiorna_gara(
        supabase,
        azienda_id,
        gara_id,
        dati,
    )

    rivaluta_workflow_gara(
        gara_id
    )


# ============================================================
# USER / COMPANY
# ============================================================

try:

    user_response = (
        supabase.auth.get_user()
    )

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

except Exception as e:

    st.error(
        f"Errore caricamento utente: {e}"
    )

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

try:

    gare = load_gare()

except Exception as e:

    st.error(
        f"Errore caricamento gare: {e}"
    )

    st.stop()


try:

    attivita = load_attivita(
        gare
    )

except Exception as e:

    st.warning(
        f"Impossibile caricare le attività: {e}"
    )

    attivita = []


try:

    reminder = load_reminder(
        attivita
    )

except Exception as e:

    st.warning(
        f"Impossibile caricare i reminder: {e}"
    )

    reminder = []


# ============================================================
# MAPPE
# ============================================================

gare_map = {
    gara["id"]: gara
    for gara in gare
}

attivita_map = {
    item["id"]: item
    for item in attivita
}


# ============================================================
# STATISTICHE
# ============================================================

oggi = date.today()

attivita_aperte = [
    item
    for item in attivita
    if item.get("stato_attivita")
    == "APERTA"
]

attivita_scadute = [
    item
    for item in attivita_aperte
    if data_scaduta(
        item.get("data_prevista")
    )
]

reminder_pendenti = [
    item
    for item in reminder
    if item.get("stato")
    == "PENDENTE"
]

reminder_scaduti = [
    item
    for item in reminder_pendenti
    if data_scaduta(
        item.get("data_prevista")
    )
]


# ============================================================
# SUCCESS MESSAGE
# ============================================================

show_success()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 📋 GARA FOLLOW-UP"
    )

    st.caption(
        "Gestione gare e follow-up"
    )

    st.divider()

    st.caption("UTENTE")

    st.write(
        user.email
        if user
        else "-"
    )

    st.caption("AZIENDA")

    st.write(
        azienda.get(
            "nome",
            "-",
        )
    )

    st.divider()

    pagina = st.radio(
        "Navigazione",
        [
            "Dashboard",
            "Gare",
            "Attività",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.caption(
        f"{len(gare)} gare · "
        f"{len(attivita_aperte)} attività aperte"
    )

    if st.button(
        "🔄 Aggiorna dati",
        use_container_width=True,
    ):

        invalidate_data()

        st.rerun()

    if st.button(
        "🚪 Esci",
        use_container_width=True,
    ):

        try:

            supabase.auth.sign_out()

        except Exception:

            pass

        st.session_state.clear()

        st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if pagina == "Dashboard":

    st.markdown(
        '<div class="app-title">Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-subtitle">'
        "Panoramica operativa delle tue gare"
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Gare",
            len(gare),
        )

    with c2:

        st.metric(
            "Attività aperte",
            len(attivita_aperte),
            delta=(
                f"{len(attivita_scadute)} scadute"
                if attivita_scadute
                else None
            ),
            delta_color="inverse",
        )

    with c3:

        st.metric(
            "Reminder pendenti",
            len(reminder_pendenti),
        )

    with c4:

        st.metric(
            "Reminder scaduti",
            len(reminder_scaduti),
            delta=(
                f"{len(reminder_scaduti)}"
                if reminder_scaduti
                else None
            ),
            delta_color="inverse",
        )

    st.divider()

    # --------------------------------------------------------
    # PRIORITÀ
    # --------------------------------------------------------

    col1, col2 = st.columns(
        [1.5, 1]
    )

    with col1:

        st.subheader(
            "⚠️ Priorità"
        )

        priorita = sorted(
            attivita_aperte,
            key=lambda x: (
                x.get(
                    "data_prevista"
                )
                is None,
                x.get(
                    "data_prevista"
                )
                or "9999-12-31",
            ),
        )

        if not priorita:

            st.success(
                "🎉 Nessuna attività aperta."
            )

        else:

            for item in priorita[:8]:

                gara = gare_map.get(
                    item["gara_id"]
                )

                gara_nome = (
                    gara.get(
                        "oggetto",
                        "Gara",
                    )
                    if gara
                    else "Gara"
                )

                data_prevista = (
                    item.get(
                        "data_prevista"
                    )
                    or "-"
                )

                if data_scaduta(
                    data_prevista
                ):

                    icona = "🔴"

                elif data_oggi(
                    data_prevista
                ):

                    icona = "🟠"

                else:

                    icona = "🟢"

                with st.container(
                    border=True
                ):

                    st.write(
                        f"{icona} **"
                        f"{item.get('titolo', 'Attività')}"
                        "**"
                    )

                    st.caption(
                        f"{gara_nome} · "
                        f"Scadenza: {data_prevista}"
                    )

    with col2:

        st.subheader(
            "🔔 Reminder"
        )

        if not reminder_pendenti:

            st.success(
                "Nessun reminder pendente."
            )

        else:

            for rem in reminder_pendenti[:8]:

                att = attivita_map.get(
                    rem["attivita_id"]
                )

                titolo = (
                    att.get(
                        "titolo",
                        "Attività",
                    )
                    if att
                    else "Attività"
                )

                data_rem = (
                    rem.get(
                        "data_prevista"
                    )
                    or "-"
                )

                if data_scaduta(
                    data_rem
                ):

                    st.error(
                        f"🔴 {titolo} · {data_rem}"
                    )

                elif data_oggi(
                    data_rem
                ):

                    st.warning(
                        f"🟠 {titolo} · oggi"
                    )

                else:

                    st.info(
                        f"🔵 {titolo} · {data_rem}"
                    )

    st.divider()

    # --------------------------------------------------------
    # STATO GARE
    # --------------------------------------------------------

    st.subheader(
        "📊 Stato delle gare"
    )

    stati = {}

    for gara in gare:

        stato = gara.get(
            "stato",
            "SCONOSCIUTO",
        )

        stati[stato] = (
            stati.get(
                stato,
                0,
            )
            + 1
        )

    if stati:

        cols = st.columns(
            min(
                len(stati),
                5,
            )
        )

        for index, (
            stato,
            numero,
        ) in enumerate(
            sorted(
                stati.items()
            )
        ):

            icona, _ = stato_gara_ui(
                stato
            )

            with cols[
                index % len(cols)
            ]:

                st.metric(
                    f"{icona} {stato}",
                    numero,
                )

    else:

        st.info(
            "Nessuna gara presente."
        )


# ============================================================
# GARE
# ============================================================

elif pagina == "Gare":

    st.markdown(
        '<div class="app-title">Gare</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-subtitle">'
        "Gestisci gare, stati e workflow"
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # NUOVA GARA
    # --------------------------------------------------------

    with st.expander(
        "➕ Inserisci nuova gara"
    ):

        c1, c2 = st.columns(2)

        with c1:

            nuova_cig = st.text_input(
                "CIG",
                key="nuova_cig",
            )

            nuovo_oggetto = st.text_input(
                "Oggetto *",
                key="nuovo_oggetto",
            )

            nuova_stazione = st.text_input(
                "Stazione appaltante *",
                key="nuova_stazione",
            )

            nuovo_importo = st.number_input(
                "Importo",
                min_value=0.0,
                step=1000.0,
                key="nuovo_importo",
            )

        with c2:

            nuovo_link = st.text_input(
                "Link portale",
                key="nuovo_link",
            )

            nuova_data_prevista = st.date_input(
                "Apertura prevista",
                value=None,
                key="nuova_data_prevista",
            )

            nuova_data_effettiva = st.date_input(
                "Apertura effettiva",
                value=None,
                key="nuova_data_effettiva",
            )

        if st.button(
            "💾 Salva gara",
            type="primary",
            use_container_width=True,
        ):

            if (
                not nuovo_oggetto.strip()
                or not nuova_stazione.strip()
            ):

                st.error(
                    "Oggetto e stazione appaltante sono obbligatori."
                )

            else:

                dati = {
                    "cig":
                        nuova_cig.strip()
                        or None,

                    "oggetto":
                        nuovo_oggetto.strip(),

                    "stazione_appaltante":
                        nuova_stazione.strip(),

                    "importo":
                        nuovo_importo,

                    "link_portale":
                        nuovo_link.strip()
                        or None,

                    "data_apertura_prevista":
                        nuova_data_prevista,

                    "data_apertura_effettiva":
                        nuova_data_effettiva,
                }

                try:

                    crea_gara(
                        supabase,
                        azienda_id,
                        dati,
                    )

                    invalidate_data()

                    success(
                        "✅ Gara salvata correttamente."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Errore nel salvataggio: {e}"
                    )

    st.divider()

    # --------------------------------------------------------
    # FILTRI
    # --------------------------------------------------------

    f1, f2 = st.columns(
        [2, 1]
    )

    with f1:

        ricerca = st.text_input(
            "🔎 Cerca gara",
            placeholder=(
                "Oggetto, CIG o stazione appaltante..."
            ),
        )

    with f2:

        stati_disponibili = [
            "Tutti"
        ] + sorted(
            {
                gara.get(
                    "stato",
                    "-",
                )
                for gara in gare
            }
        )

        filtro_stato = st.selectbox(
            "Stato",
            stati_disponibili,
        )

    gare_filtrate = gare

    if ricerca.strip():

        q = (
            ricerca
            .lower()
            .strip()
        )

        gare_filtrate = [
            gara
            for gara in gare_filtrate
            if (
                q in str(
                    gara.get(
                        "oggetto",
                        "",
                    )
                ).lower()

                or q in str(
                    gara.get(
                        "cig",
                        "",
                    )
                ).lower()

                or q in str(
                    gara.get(
                        "stazione_appaltante",
                        "",
                    )
                ).lower()
            )
        ]

    if filtro_stato != "Tutti":

        gare_filtrate = [
            gara
            for gara in gare_filtrate
            if gara.get(
                "stato"
            )
            == filtro_stato
        ]

    st.caption(
        f"{len(gare_filtrate)} gare visualizzate"
    )

    # --------------------------------------------------------
    # ELENCO GARE
    # --------------------------------------------------------

    if not gare_filtrate:

        st.info(
            "Nessuna gara trovata."
        )

    else:

        for gara in gare_filtrate:

            gara_id = gara["id"]

            stato = gara.get(
                "stato",
                "-",
            )

            icona, classe = stato_gara_ui(
                stato
            )

            with st.container(
                border=True
            ):

                c1, c2, c3 = st.columns(
                    [4, 2, 1]
                )

                with c1:

                    st.write(
                        f"### {icona} "
                        f"{gara.get('oggetto', '-')}"
                    )

                    st.caption(
                        f"CIG: {gara.get('cig') or '-'}"
                        " · "
                        f"{gara.get('stazione_appaltante') or '-'}"
                    )

                with c2:

                    st.markdown(
                        f'<span class="status-badge {classe}">'
                        f"{stato}"
                        "</span>",
                        unsafe_allow_html=True,
                    )

                    if gara.get(
                        "importo"
                    ) is not None:

                        st.caption(
                            f"€ {float(gara['importo']):,.2f}"
                        )

                with c3:

                    if st.button(
                        "Apri",
                        key=f"apri_{gara_id}",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "gara_selezionata"
                        ] = gara_id

                        st.rerun()

    # --------------------------------------------------------
    # DETTAGLIO GARA
    # --------------------------------------------------------

    gara_id = st.session_state.get(
        "gara_selezionata"
    )

    gara_selezionata = gare_map.get(
        gara_id
    )

    if gara_selezionata:

        st.divider()

        st.markdown(
            f"## {gara_selezionata.get('oggetto', '-')}"
        )

        stato = gara_selezionata.get(
            "stato",
            "-",
        )

        icona, classe = stato_gara_ui(
            stato
        )

        st.markdown(
            f'<span class="status-badge {classe}">'
            f"{icona} {stato}"
            "</span>",
            unsafe_allow_html=True,
        )

        st.divider()

        # ----------------------------------------------------
        # DATI GARA
        # ----------------------------------------------------

        c1, c2, c3 = st.columns(3)

        with c1:

            st.caption("CIG")

            st.write(
                gara_selezionata.get(
                    "cig"
                )
                or "-"
            )

            st.caption(
                "Stazione appaltante"
            )

            st.write(
                gara_selezionata.get(
                    "stazione_appaltante"
                )
                or "-"
            )

        with c2:

            st.caption("Importo")

            importo = (
                gara_selezionata.get(
                    "importo"
                )
            )

            st.write(
                f"€ {float(importo):,.2f}"
                if importo is not None
                else "-"
            )

            st.caption(
                "Ribasso proprio"
            )

            st.write(
                gara_selezionata.get(
                    "ribasso_proprio"
                )
                or "-"
            )

        with c3:

            st.caption(
                "Apertura prevista"
            )

            st.write(
                gara_selezionata.get(
                    "data_apertura_prevista"
                )
                or "-"
            )

            st.caption(
                "Apertura effettiva"
            )

            st.write(
                gara_selezionata.get(
                    "data_apertura_effettiva"
                )
                or "-"
            )

        if gara_selezionata.get(
            "link_portale"
        ):

            st.link_button(
                "🌐 Apri portale",
                gara_selezionata[
                    "link_portale"
                ],
            )

        # ----------------------------------------------------
        # WORKFLOW
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "⚙️ Workflow operativo"
        )

        if stato == "CHIUSA":

            st.warning(
                "🔒 La gara è chiusa. "
                "Il workflow operativo è sospeso."
            )

            st.caption(
                "Le attività aperte e i reminder pendenti "
                "sono stati annullati dalla funzione di chiusura."
            )

            if st.button(
                "🔓 Riapri gara",
                type="primary",
                use_container_width=True,
            ):

                try:

                    riapri_gara(
                        gara_id
                    )

                    invalidate_data()

                    success(
                        "✅ Gara riaperta e workflow rivalutato."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Errore riapertura: {e}"
                    )

        elif stato == "IN_ATTESA_APERTURA":

            st.info(
                "⏳ La gara è in attesa dell'apertura delle buste."
            )

            if gara_selezionata.get(
                "data_apertura_prevista"
            ):

                st.caption(
                    "Apertura prevista: "
                    f"{gara_selezionata['data_apertura_prevista']}"
                )

            if st.button(
                "📂 Segna buste aperte",
                type="primary",
                use_container_width=True,
            ):

                try:

                    cambia_stato_gara(
                        gara_id,
                        "BUSTE_APERTE",
                        {
                            "data_apertura_effettiva":
                                date.today(),

                            "ultimo_aggiornamento":
                                "Buste aperte",
                        },
                    )

                    invalidate_data()

                    success(
                        "📂 Gara impostata come BUSTE APERTE."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Errore: {e}"
                    )

        elif stato == "BUSTE_APERTE":

            st.info(
                "📂 Le buste sono aperte. "
                "Inserisci l'esito quando disponibile."
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "🏆 Segna VINTA",
                    type="primary",
                    use_container_width=True,
                ):

                    try:

                        cambia_stato_gara(
                            gara_id,
                            "VINTA",
                            {
                                "ultimo_aggiornamento":
                                    "Gara vinta",
                            },
                        )

                        invalidate_data()

                        success(
                            "🏆 Gara impostata come VINTA."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Errore: {e}"
                        )

            with c2:

                if st.button(
                    "❌ Segna PERSA",
                    use_container_width=True,
                ):

                    try:

                        cambia_stato_gara(
                            gara_id,
                            "PERSA",
                            {
                                "ultimo_aggiornamento":
                                    "Gara persa",
                            },
                        )

                        invalidate_data()

                        success(
                            "❌ Gara impostata come PERSA."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Errore: {e}"
                        )

        elif stato == "VINTA":

            st.success(
                "🏆 Gara vinta."
            )

            if (
                not gara_selezionata.get(
                    "vincitore"
                )
                or not gara_selezionata.get(
                    "ribasso_vincitore"
                )
            ):

                st.warning(
                    "⚠️ Mancano i dati del vincitore. "
                    "Il workflow ha generato un'attività "
                    "per completarli."
                )

            else:

                st.success(
                    "Dati del vincitore presenti."
                )

        elif stato == "PERSA":

            st.error(
                "❌ Gara persa."
            )

            st.info(
                "Il workflow verifica che la comunicazione "
                "della perdita sia stata completata."
            )

        # ----------------------------------------------------
        # RIVALUTA WORKFLOW
        # ----------------------------------------------------

        st.divider()

        with st.expander(
            "🔄 Strumenti workflow"
        ):

            st.caption(
                "Usa questa funzione se hai modificato "
                "manualmente i dati della gara e vuoi "
                "ricostruire le attività operative."
            )

            if st.button(
                "🔄 Rivaluta workflow",
                use_container_width=True,
            ):

                try:

                    rivaluta_workflow_gara(
                        gara_id
                    )

                    invalidate_data()

                    success(
                        "🔄 Workflow rivalutato correttamente."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Errore rivalutazione workflow: {e}"
                    )

        # ----------------------------------------------------
        # CHIUSURA
        # ----------------------------------------------------

        if stato != "CHIUSA":

            st.divider()

            st.warning(
                "La chiusura sospende il workflow operativo "
                "e annulla le attività ancora aperte."
            )

            if st.button(
                "🔒 Chiudi gara",
                use_container_width=True,
            ):

                try:

                    chiudi_gara(
                        gara_id
                    )

                    invalidate_data()

                    success(
                        "🔒 Gara chiusa correttamente."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Errore chiusura: {e}"
                    )

        # ----------------------------------------------------
        # DATI AVANZATI
        # ----------------------------------------------------

        with st.expander(
            "✏️ Modifica dati gara"
        ):

            c1, c2 = st.columns(2)

            with c1:

                modifica_cig = st.text_input(
                    "CIG",
                    value=(
                        gara_selezionata.get(
                            "cig"
                        )
                        or ""
                    ),
                    key=f"mod_cig_{gara_id}",
                )

                modifica_oggetto = st.text_input(
                    "Oggetto",
                    value=(
                        gara_selezionata.get(
                            "oggetto"
                        )
                        or ""
                    ),
                    key=f"mod_oggetto_{gara_id}",
                )

                modifica_stazione = st.text_input(
                    "Stazione appaltante",
                    value=(
                        gara_selezionata.get(
                            "stazione_appaltante"
                        )
                        or ""
                    ),
                    key=f"mod_stazione_{gara_id}",
                )

                modifica_importo = st.number_input(
                    "Importo",
                    min_value=0.0,
                    value=float(
                        gara_selezionata.get(
                            "importo"
                        )
                        or 0
                    ),
                    step=1000.0,
                    key=f"mod_importo_{gara_id}",
                )

                modifica_link = st.text_input(
                    "Link portale",
                    value=(
                        gara_selezionata.get(
                            "link_portale"
                        )
                        or ""
                    ),
                    key=f"mod_link_{gara_id}",
                )

            with c2:

                modifica_data_prevista = st.date_input(
                    "Apertura prevista",
                    value=(
                        gara_selezionata.get(
                            "data_apertura_prevista"
                        )
                        if gara_selezionata.get(
                            "data_apertura_prevista"
                        )
                        else None
                    ),
                    key=f"mod_data_prevista_{gara_id}",
                )

                modifica_data_effettiva = st.date_input(
                    "Apertura effettiva",
                    value=(
                        gara_selezionata.get(
                            "data_apertura_effettiva"
                        )
                        if gara_selezionata.get(
                            "data_apertura_effettiva"
                        )
                        else None
                    ),
                    key=f"mod_data_effettiva_{gara_id}",
                )

                modifica_vincitore = st.text_input(
                    "Vincitore",
                    value=(
                        gara_selezionata.get(
                            "vincitore"
                        )
                        or ""
                    ),
                    key=f"mod_vincitore_{gara_id}",
                )

                modifica_ribasso_proprio = st.text_input(
                    "Ribasso proprio",
                    value=(
                        gara_selezionata.get(
                            "ribasso_proprio"
                        )
                        or ""
                    ),
                    key=f"mod_ribasso_proprio_{gara_id}",
                )

                modifica_ribasso_vincitore = st.text_input(
                    "Ribasso vincitore",
                    value=(
                        gara_selezionata.get(
                            "ribasso_vincitore"
                        )
                        or ""
                    ),
                    key=f"mod_ribasso_vincitore_{gara_id}",
                )

            modifica_ultimo_aggiornamento = st.text_area(
                "Ultimo aggiornamento",
                value=(
                    gara_selezionata.get(
                        "ultimo_aggiornamento"
                    )
                    or ""
                ),
                key=f"mod_ultimo_{gara_id}",
            )

            if st.button(
                "💾 Salva modifiche",
                type="primary",
                use_container_width=True,
            ):

                if (
                    not modifica_oggetto.strip()
                    or not modifica_stazione.strip()
                ):

                    st.error(
                        "Oggetto e stazione appaltante sono obbligatori."
                    )

                else:

                    dati = {
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

                        "data_apertura_prevista":
                            modifica_data_prevista,

                        "data_apertura_effettiva":
                            modifica_data_effettiva,

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
                            dati,
                        )

                        # Dopo ogni modifica ai dati
                        # rivalutiamo il workflow.
                        rivaluta_workflow_gara(
                            gara_id
                        )

                        invalidate_data()

                        success(
                            "✅ Gara aggiornata e workflow rivalutato."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Errore aggiornamento: {e}"
                        )

        # ----------------------------------------------------
        # ATTIVITÀ DELLA GARA
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "📋 Attività della gara"
        )

        gara_attivita = [
            item
            for item in attivita
            if item.get(
                "gara_id"
            )
            == gara_id
        ]

        if not gara_attivita:

            st.info(
                "Nessuna attività per questa gara."
            )

        else:

            for item in gara_attivita:

                stato_att = item.get(
                    "stato_attivita",
                    "-",
                )

                icona_att, classe_att = (
                    stato_attivita_ui(
                        stato_att
                    )
                )

                with st.container(
                    border=True
                ):

                    c1, c2 = st.columns(
                        [4, 1]
                    )

                    with c1:

                        st.write(
                            f"{icona_att} **"
                            f"{item.get('titolo', 'Attività')}"
                            "**"
                        )

                        st.caption(
                            f"Tipo: {item.get('tipo') or '-'}"
                            " · "
                            f"Scadenza: "
                            f"{item.get('data_prevista') or '-'}"
                        )

                    with c2:

                        st.markdown(
                            f'<span class="status-badge {classe_att}">'
                            f"{stato_att}"
                            "</span>",
                            unsafe_allow_html=True,
                        )

                    if item.get(
                        "descrizione"
                    ):

                        st.caption(
                            item["descrizione"]
                        )

        # ----------------------------------------------------
        # STORICO
        # ----------------------------------------------------

        with st.expander(
            "📜 Storico stati"
        ):

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


# ============================================================
# ATTIVITÀ
# ============================================================

elif pagina == "Attività":

    st.markdown(
        '<div class="app-title">Attività</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-subtitle">'
        "Segui le attività generate dal workflow"
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FILTRI
    # --------------------------------------------------------

    c1, c2 = st.columns(2)

    with c1:

        filtro = st.selectbox(
            "Stato attività",
            [
                "Tutte",
                "Aperte",
                "Completate",
                "Annullate",
            ],
        )

    with c2:

        filtro_urgenza = st.selectbox(
            "Priorità",
            [
                "Tutte",
                "Scadute",
                "Oggi",
                "Future",
            ],
        )

    attivita_filtrate = attivita

    if filtro == "Aperte":

        attivita_filtrate = [
            x
            for x in attivita_filtrate
            if x.get(
                "stato_attivita"
            )
            == "APERTA"
        ]

    elif filtro == "Completate":

        attivita_filtrate = [
            x
            for x in attivita_filtrate
            if x.get(
                "stato_attivita"
            )
            == "COMPLETATA"
        ]

    elif filtro == "Annullate":

        attivita_filtrate = [
            x
            for x in attivita_filtrate
            if x.get(
                "stato_attivita"
            )
            == "ANNULLATA"
        ]

    if filtro_urgenza == "Scadute":

        attivita_filtrate = [
            x
            for x in attivita_filtrate
            if data_scaduta(
                x.get(
                    "data_prevista"
                )
            )
        ]

    elif filtro_urgenza == "Oggi":

        attivita_filtrate = [
            x
            for x in attivita_filtrate
            if data_oggi(
                x.get(
                    "data_prevista"
                )
            )
        ]

    elif filtro_urgenza == "Future":

        attivita_filtrate = [
            x
            for x in attivita_filtrate
            if (
                x.get(
                    "data_prevista"
                )
                and str(
                    x["data_prevista"]
                )
                > str(oggi)
            )
        ]

    st.caption(
        f"{len(attivita_filtrate)} attività"
    )

    # --------------------------------------------------------
    # ATTIVITÀ
    # --------------------------------------------------------

    if not attivita_filtrate:

        st.success(
            "🎉 Nessuna attività corrisponde ai filtri."
        )

    else:

        for item in attivita_filtrate:

            attivita_id = item["id"]

            gara = gare_map.get(
                item["gara_id"]
            )

            gara_nome = (
                gara.get(
                    "oggetto",
                    "Gara",
                )
                if gara
                else "Gara non trovata"
            )

            stato_attivita = item.get(
                "stato_attivita",
                "-",
            )

            icona, classe = (
                stato_attivita_ui(
                    stato_attivita
                )
            )

            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [4, 1]
                )

                with c1:

                    st.write(
                        f"{icona} **"
                        f"{item.get('titolo', 'Attività')}"
                        "**"
                    )

                    st.caption(
                        f"🏢 {gara_nome}"
                    )

                with c2:

                    st.markdown(
                        f'<span class="status-badge {classe}">'
                        f"{stato_attivita}"
                        "</span>",
                        unsafe_allow_html=True,
                    )

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.caption("Tipo")

                    st.write(
                        item.get(
                            "tipo"
                        )
                        or "-"
                    )

                with c2:

                    st.caption("Scadenza")

                    st.write(
                        item.get(
                            "data_prevista"
                        )
                        or "-"
                    )

                with c3:

                    st.caption("Motivo")

                    st.write(
                        item.get(
                            "motivo"
                        )
                        or "-"
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
                        "Motivo workflow: "
                        f"{item['motivo']}"
                    )

                # ------------------------------------------------
                # AZIONI ATTIVITÀ
                # ------------------------------------------------

                if (
                    stato_attivita
                    == "APERTA"
                ):

                    c1, c2 = st.columns(
                        2
                    )

                    with c1:

                        if st.button(
                            "✅ Completa",
                            key=f"complete_{attivita_id}",
                            type="primary",
                            use_container_width=True,
                        ):

                            try:
                                aggiorna_attivita(
                                   attivita_id,
                                  "COMPLETATA",
                                )

                                aggiorna_reminder(
                                    attivita_id,
                                    "INVIATO",
                                )

                                gara_id = item["gara_id"]

                                rivaluta_workflow_gara(
                                    gara_id
                                )

                                invalidate_data()

                                success(
                                    "✅ Attività completata e workflow rivalutato."
                                )

                                st.rerun()

                            except Exception as e:

                                 st.error(
                                     f"Errore completamento attività: {e}"
                                 )

                    with c2:

                        if st.button(
                            "🚫 Annulla",
                            key=(
                                f"cancel_"
                                f"{attivita_id}"
                            ),
                            use_container_width=True,
                        ):

                            try:

                                aggiorna_attivita(
                                    attivita_id,
                                    "ANNULLATA",
                                )

                                aggiorna_reminder(
                                    attivita_id,
                                    "ANNULLATO",
                                )

                                invalidate_data()

                                success(
                                    "🚫 Attività annullata."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Errore: {e}"
                                )

    # --------------------------------------------------------
    # REMINDER
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🔔 Reminder pendenti"
    )

    if not reminder_pendenti:

        st.success(
            "Nessun reminder pendente."
        )

    else:

        for rem in reminder_pendenti:

            att = attivita_map.get(
                rem["attivita_id"]
            )

            titolo = (
                att.get(
                    "titolo",
                    "Attività",
                )
                if att
                else "Attività"
            )

            data_rem = (
                rem.get(
                    "data_prevista"
                )
                or "-"
            )

            if data_scaduta(
                data_rem
            ):

                st.error(
                    f"🔴 **{titolo}** · "
                    f"scaduto {data_rem}"
                )

            elif data_oggi(
                data_rem
            ):

                st.warning(
                    f"🟠 **{titolo}** · oggi"
                )

            else:

                st.info(
                    f"🔵 **{titolo}** · "
                    f"{data_rem}"
                )
