from django.shortcuts import render
from firebase_admin import firestore
from beer_sheva_backend.firebase import initialize_firebase, get_reports_from_firebase, get_report_by_id
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Report
from .serializers import ReportSerializer
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .forms import ReportForm, type_dict
from django.shortcuts import render, redirect
from .forms import ReportForm
from beer_sheva_backend.firebase import save_report_to_firebase
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import logging
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from user.decorators import role_required
from user.decorators import firebase_login_required
logger = logging.getLogger(__name__)
from .forms import REPORT_TYPES

type_dict = dict(REPORT_TYPES)

# Firas BSPM25T29-16
from firebase_admin import storage
import uuid

@firebase_login_required
def add_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                report = form.save()
                title = form.cleaned_data['title']
                description = form.cleaned_data['description']
                location = form.cleaned_data['place']
                latitude = form.cleaned_data['latitude']
                longitude = form.cleaned_data['longitude']
                report_type = form.cleaned_data['type']
                reporter_email = request.session.get('user_email', 'anonymous')

                # Upload image to Firebase Storage
                image_url = None
                if 'image' in request.FILES:
                    image_file = request.FILES['image']
                    file_extension = image_file.name.split('.')[-1]
                    image_name = f"reports/{uuid.uuid4()}.{file_extension}"
                    bucket = storage.bucket()
                    blob = bucket.blob(image_name)
                    blob.upload_from_file(image_file, content_type=image_file.content_type)
                    blob.make_public()
                    image_url = blob.public_url

                # Save to Firebase with image URL
                try:
                    report_id = save_report_to_firebase(
                        title, description, location, latitude, longitude, report_type,
                        reporter_email, image_url=image_url
                    )
                except Exception as e:
                    return render(request, 'add_report.html', {'form': form, 'error': 'Error saving to Firebase'})

                report.firebase_id = report_id
                report.save()
                messages.success(request, 'Your report has been submitted successfully!')
                return redirect('report_confirmation', report_id=report_id)
            except Exception as e:
                return render(request, 'add_report.html', {'form': form, 'error': 'Error saving the report'})
        else:
            return render(request, 'add_report.html', {'form': form, 'error': 'Form is invalid'})
    else:
        form = ReportForm()
    return render(request, 'add_report.html', {'form': form})


# Ibrahim BSPM25T29-3
def report_confirmation(request, report_id):
    report = get_report_by_id(report_id)
    if not report:
        return redirect('report_list')
    return render(request, 'confirmation.html', {'report': report})




from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

@csrf_exempt
def report_detail(request, report_id):
    report = get_report_by_id(report_id)
    if not report:
        return redirect('report_list')

    # Simple: Keep upvotes and comments in Firebase as lists/fields
    if request.method == 'POST':
        action = request.POST.get('action')
        db = initialize_firebase()
        report_ref = db.collection("Reports").document(report_id)
        if action == 'upvote':
            # Store upvotes as a count
            upvotes = report.get('upvotes', 0)
            report_ref.update({"upvotes": upvotes + 1})
            report['upvotes'] = upvotes + 1  # for immediate feedback
        elif action == 'add_comment':
            comment = request.POST.get('comment', '').strip()
            user = request.user if request.user.is_authenticated else None
            comments = report.get('comments', [])
            comments.append({
                "text": comment,
                "user": str(user) if user else "אנונימי",
                "timestamp": timezone.now().isoformat()
            })
            report_ref.update({"comments": comments})
            report['comments'] = comments

    return render(request, 'report_detail.html', {'report': report})

# Malik
@role_required(['admin', 'worker', 'user'])
def report_list(request):
    report_type = request.GET.get('type', None)
    reports_list = get_reports_from_firebase(report_type=report_type)

    for report in reports_list:
        report_type_key = report.get('type', '')
        report['type_name'] = type_dict.get(report_type_key, 'לא ידוע')

    paginator = Paginator(reports_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    return render(request, 'report_list.html', {
        'page_obj': page_obj,
        'reports_data': reports_list,
        'type_dict': type_dict,
    })


# Malik
def map_view(request):
    reports_list = get_reports_from_firebase()
    return render(request, 'map.html', {'reports': reports_list})


# Abed BSPM25T29-17
@role_required(['admin'])
def admin_dashboard(request):
    reports_list = get_reports_from_firebase()
    return render(request, 'admin_dashboard.html', {'reports': reports_list})


from django.shortcuts import render
from django.conf import settings
import smtplib
from email.mime.text import MIMEText


def contact_us(request):
    sent = False
    error = None

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()

        if not (name and email and phone and message):
            error = "נא למלא את כל השדות."
        else:
            # Just fake a send for demo—do not actually send email.
            subject = f"פנייה חדשה מאת {name} דרך צור קשר"
            body = f"""
            שם: {name}
            אימייל: {email}
            טלפון: {phone}
            ------------------
            הודעה:
            {message}
            """
            # Print/log for demonstration
            print(f"--- Demo Contact Form Submission ---\nSubject: {subject}\n{body}\n--------------------")
            sent = True

    return render(request, "contact_us.html", {
        "sent": sent,
        "error": error,
    })
