from supabase import Client


def get_mia_azienda_id(supabase: Client):

    response = supabase.rpc(
        "get_mia_azienda_id"
    ).execute()

    return response.data


def get_mia_azienda(supabase: Client):

    azienda_id = get_mia_azienda_id(
        supabase
    )

    response = (
        supabase
        .table("azienda")
        .select("id, nome")
        .eq("id", azienda_id)
        .single()
        .execute()
    )

    return response.data
