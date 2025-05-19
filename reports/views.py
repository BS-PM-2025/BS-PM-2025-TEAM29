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
logger = logging.getLogger(__name__)


# Firas BSPM25T29-16
def add_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            try:
                # Save the report to the local database
                report = form.save()
                logger.info(f"Report saved successfully: {report}")

                # Extract the data from the form
                title = form.cleaned_data['title']
                description = form.cleaned_data['description']
                location = form.cleaned_data['place']
                latitude = form.cleaned_data['latitude']
                longitude = form.cleaned_data['longitude']
                report_type = form.cleaned_data['type']

                logger.info(f"Extracted data: title={title}, description={description}, "
                            f"location={location}, latitude={latitude}, longitude={longitude}, type={report_type}")

                # Save the report to Firebase
                try:
                    report_id = save_report_to_firebase(title, description, location, latitude, longitude, report_type)
                    logger.info(f"Report saved to Firebase with ID: {report_id}")
                except Exception as e:
                    logger.error(f"Error saving report to Firebase: {e}")
                    return render(request, 'add_report.html', {'form': form, 'error': 'Error saving to Firebase'})

                # Save the Firebase ID to the report in the local database
                report.firebase_id = report_id
                report.save()

                # Add success message
                messages.success(request, 'Your report has been submitted successfully!')
                return redirect('report_confirmation', report_id=report_id)

            except Exception as e:
                logger.error(f"Error saving the report to local database: {e}")
                return render(request, 'add_report.html', {'form': form, 'error': 'Error saving the report'})
        else:
            logger.warning("Form is not valid.")
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


# Malik
@role_required(['admin', 'worker', 'user'])
def report_list(request):
    report_type = request.GET.get('type', None)
    reports_list = get_reports_from_firebase(report_type=report_type)

    for report in reports_list:
        report['type_name'] = type_dict.get(report.get('type'), 'לא ידוע')

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
@login_required
@role_required(['admin'])
def admin_dashboard(request):
    reports_list = get_reports_from_firebase()
    return render(request, 'admin_dashboard.html', {'reports': reports_list})


# Ibrahim BSPM25T29-151
@login_required
@role_required(['admin', 'worker'])
def worker_dashboard(request):
    reports_list = get_reports_from_firebase()
    return render(request, 'worker_dashboard.html', {'reports': reports_list})
