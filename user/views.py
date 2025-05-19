# BS-PM-2025-TEAM29/user/views.py

from firebase_admin import auth,firestore
import firebase_admin
from django.conf import settings
from firebase_admin import credentials
from django.views.decorators.csrf import csrf_exempt

# Firebase initialization (if not done in a shared file)
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

FIREBASE_WEB_API_KEY = settings.FIREBASE_WEB_API_KEY  # Add this to settings

@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        confirm = request.POST['confirm_password']

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        try:
            # 1. Create Firebase Auth user
            user = auth.create_user(email=email, password=password)
            uid = user.uid

            # 2. Store additional data in Firestore (e.g., role = 'user')
            db = firestore.client()
            db.collection('Users').document(uid).set({
                'email': email,
                'role': 'user',
            })

            messages.success(request, "User created successfully.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Registration error: {e}")
            return redirect('register')

    return render(request, 'register.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from .firebase_auth import firebase_sign_in

def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user_data = firebase_sign_in(email, password)
        if user_data:
            firebase_uid = user_data['localId']
            request.session['firebase_uid'] = firebase_uid

            # 🔐 Fetch user role from Firestore
            db = firestore.client()
            role_doc = db.collection('Users').document(firebase_uid).get()
            if role_doc.exists:
                role = role_doc.to_dict().get('role', 'user')
                request.session['user_role'] = role

            messages.success(request, f"Welcome {email}")
            return redirect('report_list')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'login.html')
def logout_view(request):
    request.session.flush()  # Clears all session data
    return redirect('login')