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

    return response.data
