# beer_sheva_backend/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
from django.conf import settings
from firebase_admin import firestore
import logging
import datetime


def initialize_firebase():
    # Check if Firebase has already been initialized
    if not firebase_admin._apps:  # No apps initialized
        try:
            # Initialize Firebase with credentials
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            logging.info("Firebase initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Firebase: {e}")
    else:
        logging.info("Firebase is already initialized.")

    # Firestore client (returned after initialization)
    return firestore.client()





def save_report_to_firebase(title, description, location, latitude, longitude, report_type):
    db = firestore.client()  # Firestore instance

    # Get the current timestamp
    created_at = datetime.datetime.utcnow()

    # Create a new document in the Reports collection
    report_ref = db.collection('Reports').add({
        'title': title,
        'description': description,
        'location': location,
        'latitude': latitude,
        'longitude': longitude,
        'created_at': created_at,  # Use current UTC time as the timestamp
        'type': report_type  # Add the report type to the Firestore document
    })

    # Get the report ID from the DocumentReference object
    report_id = report_ref[1].id  # The second item in the tuple is the DocumentReference

    # Optionally, create a subcollection based on report type
    db.collection('Reports').document(report_id).collection(report_type).add({
        'title': title,
        'description': description,
        'location': location,
        'latitude': latitude,
        'longitude': longitude,
        'created_at': created_at  # Use the same timestamp here
    })

    return report_id


def get_reports_from_firebase(report_type=None):
    """
    Fetch reports from Firebase Firestore, optionally filtered by report type.
    If report_type is None, all reports will be fetched.
    """
    db = firestore.client()  # Firestore instance

    # Retrieve reports from Firestore (optionally filtered by report type)
    if report_type:
        reports_ref = db.collection('Reports').where('type', '==', report_type)
    else:
        reports_ref = db.collection('Reports')

    # Fetch the documents from Firestore
    reports_docs = reports_ref.stream()

    # Process the documents and prepare a list of reports
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
            'type': report_data.get('type', 'general')  # Default to 'general' type if not available
        })

    return reports_list  # Return the list of reports from Firebase