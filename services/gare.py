from supabase import Client


def get_gare(
    supabase: Client,
    azienda_id: str
):

    response = (
        supabase
        .table("gare")
        .select("*")
        .eq("azienda_id", azienda_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


def crea_gara(
    supabase: Client,
    azienda_id: str,
    dati: dict
):

    cig = dati.get("cig")

    if cig:

        controllo = (
            supabase
            .table("gare")
            .select("id")
            .eq("azienda_id", azienda_id)
            .eq("cig", cig)
            .execute()
        )

        if controllo.data:

            raise ValueError(
                "Esiste già una gara con questo CIG."
            )

    dati_gara = {
        **dati,
        "azienda_id": azienda_id
    }

    response = (
        supabase
        .table("gare")
        .insert(dati_gara)
        .execute()
    )

def aggiorna_gara(
    supabase: Client,
    azienda_id: str,
    gara_id: str,
    dati: dict
):

    response = supabase.rpc(
        "aggiorna_dati_gara",
        {
            "p_gara_id": gara_id,
            "p_cig": dati.get("cig"),
            "p_oggetto": dati.get("oggetto"),
            "p_stazione_appaltante": dati.get(
                "stazione_appaltante"
            ),
            "p_importo": dati.get("importo"),
            "p_link_portale": dati.get(
                "link_portale"
            ),
            "p_data_apertura_prevista": dati.get(
                "data_apertura_prevista"
            ),
            "p_data_apertura_effettiva": dati.get(
                "data_apertura_effettiva"
            ),
            "p_ribasso_proprio": dati.get(
                "ribasso_proprio"
            ),
            "p_vincitore": dati.get(
                "vincitore"
            ),
            "p_ribasso_vincitore": dati.get(
                "ribasso_vincitore"
            ),
            "p_ultimo_aggiornamento": dati.get(
                "ultimo_aggiornamento"
            )
        }
    ).execute()

    return response.data

