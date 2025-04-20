# beer_sheva_backend/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
from django.conf import settings
from firebase_admin import firestore
import logging
import datetime





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
            'status': report_data.get('status', 'pending') 
        })

    if user_location and radius:
        reports_list = [report for report in reports_list 
                       if report.get('latitude') and report.get('longitude')
                       and abs(report['latitude'] - user_location[0]) < radius/100
                       and abs(report['longitude'] - user_location[1]) < radius/100]

    return reports_list

