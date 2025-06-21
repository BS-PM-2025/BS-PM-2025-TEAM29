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
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        role = request.POST.get('role', 'user')  # <-- Default to user

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        try:
            # 1. Create Firebase user
            user = auth.create_user(email=email, password=password)
            uid = user.uid

            # 2. Save user info to Firestore with UID as doc ID
            db = firestore.client()
            db.collection('Users').document(uid).set({
                'username': username,
                'email': email,
                'role': role,         # <-- Save the selected role
                'id': uid,
            })

            messages.success(request, "User registered successfully.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Registration error: {e}")
            return redirect('register')

    return render(request, 'register.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from .firebase_auth import firebase_sign_in
from firebase_admin import firestore

def user_login(request):
    if request.method == 'POST':
        identifier = request.POST['identifier']  # can be email or username
        password = request.POST['password']

        db = firestore.client()

        # Determine if identifier is an email or username
        if '@' in identifier:
            email = identifier
        else:
            # Assume it's a username; find the corresponding email
            users_ref = db.collection('Users')
            query = users_ref.where('username', '==', identifier).limit(1).stream()
            user_doc = next(query, None)
            if user_doc is None:
                messages.error(request, "Username not found.")
                return redirect('login')
            user_info = user_doc.to_dict()
            email = user_info.get('email')

        user_data = firebase_sign_in(email, password)
        if user_data:
            firebase_uid = user_data['localId']
            request.session['firebase_uid'] = firebase_uid
            request.session['user_email'] = email

            # 🔐 Fetch user info from Firestore and save to session
            user_doc = db.collection('Users').document(firebase_uid).get()
            if user_doc.exists:
                user_info = user_doc.to_dict()
                role = user_info.get('role', 'user')
                username = user_info.get('username', email)
                request.session['user_role'] = role
                request.session['username'] = username

                # If user is a worker, save their jobs list in session for easy access
                if role == 'worker':
                    jobs = user_info.get('jobs', [])
                    request.session['jobs'] = jobs  # can be list of dicts, e.g. [{"report_id": "...", "role": "..."}]
                    print("Logged-in worker jobs:", jobs)

            print("Session after login:", dict(request.session))
            messages.success(request, f"Welcome {identifier}")
            return redirect('report_list')
        else:
            messages.error(request, "Invalid credentials.")
            return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()  # Clears all session data
    return redirect('login')
