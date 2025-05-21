import requests
from django.conf import settings

FIREBASE_API_KEY = settings.FIREBASE_WEB_API_KEY

def firebase_sign_in(email, password):
    """Sign in with Firebase and return the user data or None."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()  # includes idToken, localId, etc.
    else:
        return None

def firebase_user_exists(email):
    # This requires you to use the Firebase Admin SDK
    from firebase_admin import auth
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except auth.UserNotFoundError:
        return None
