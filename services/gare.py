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
