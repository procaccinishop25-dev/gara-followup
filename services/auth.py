from supabase import Client


def login(
    supabase: Client,
    email: str,
    password: str
):
    return supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password
        }
    )


def logout(supabase: Client):
    supabase.auth.sign_out()
