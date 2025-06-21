# beer_sheva_backend/firebase.py
import firebase_admin
from django.http import JsonResponse
from firebase_admin import credentials, firestore
from django.conf import settings
from firebase_admin import firestore
import logging
import datetime


def initialize_firebase():
    if not firebase_admin._apps: 
        try:

            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            logging.info("Firebase initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Firebase: {e}")
    else:
        logging.info("Firebase is already initialized.")

    return firestore.client()



def save_report_to_firebase(title, description, location, latitude, longitude, report_type,reporter_email):
    db = firestore.client()

    created_at = datetime.datetime.utcnow()

    report_ref = db.collection('Reports').add({
        'title': title,
        'description': description,
        'location': location,
        'latitude': latitude,
        'longitude': longitude,
        'created_at': created_at,
        'type': report_type,
        'reporter_email': reporter_email,
        'status': 'pending',
        'supporters': []
    })

    report_id = report_ref[1].id

    return report_id


#Malik BSPM25T29-18
def get_reports_from_firebase(report_type=None, user_location=None, radius=None):
    """
    Fetch reports from Firebase Firestore, optionally filtered by report type or location.
    If report_type is None, all reports will be fetched.
    If user_location and radius are provided, returns reports within the radius.
    """
    db = firestore.client()  

    if report_type:
        reports_ref = db.collection('Reports').where('type', '==', report_type)
    else:
        reports_ref = db.collection('Reports')

    reports_docs = reports_ref.stream()

    reports_list = []
    for doc in reports_docs:
        report_data = doc.to_dict()
        reports_list.append({
            'id': doc.id,
            'title': report_data.get('title'),
            'description': report_data.get('description'),
            'location': report_data.get('location'),
            'latitude': report_data.get('latitude'),
            'longitude': report_data.get('longitude'),
            'created_at': report_data.get('created_at'),
            'type': report_data.get('type', 'general'),
            'image_url': report_data.get('image_url'),
            'status': report_data.get('status', 'pending') 
        })

    if user_location and radius:
        reports_list = [report for report in reports_list 
                       if report.get('latitude') and report.get('longitude')
                       and abs(report['latitude'] - user_location[0]) < radius/100
                       and abs(report['longitude'] - user_location[1]) < radius/100]

    return reports_list


#Ibrahim BSPM25T29-3
def get_report_by_id(report_id):
    db = firestore.client()
    doc = db.collection('Reports').document(report_id).get()
    if doc.exists:
        report = doc.to_dict()
        report['id'] = doc.id  # <- Add this line!
        return report
    return None

#BSPM25T29-58
def join_report(request, report_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User must be logged in'}, status=401)

    user_email = request.user.email

    try:
        db = firestore.client()
        doc_ref = db.collection('Reports').document(report_id)

        doc = doc_ref.get()
        if not doc.exists:
            return JsonResponse({'error': 'Report not found'}, status=404)

        doc_ref.update({
            'supporters': firestore.ArrayUnion([user_email])
        })

        return JsonResponse({'success': 'You joined the report successfully!'})
    except Exception as e:  # ❗ This was missing
        logging.error(f"Error joining report: {e}")
        return JsonResponse({'error': 'An error occurred while joining the report'}, status=500)
