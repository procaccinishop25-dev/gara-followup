from supabase import Client


def get_mia_azienda_id(supabase: Client):

    response = supabase.rpc(
        "get_mia_azienda_id"
    ).execute()

    return {
        "data": response.data,
        "type": type(response.data).__name__
    }
