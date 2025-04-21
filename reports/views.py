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
logger = logging.getLogger(__name__)



logger = logging.getLogger(__name__)
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

#Ibrahim BSPM25T29-3
def report_confirmation(request, report_id):
    report = get_report_by_id(report_id)
    if not report:
        return redirect('report_list')
    return render(request, 'confirmation.html', {'report': report})

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

#Ibrahim BSPM25T29-151
@login_required
def worker_dashboard(request):
    reports_list = get_reports_from_firebase()
    return render(request, 'worker_dashboard.html', {'reports': reports_list})





def map_view(request):
    reports_list = get_reports_from_firebase()
    return render(request, 'map.html', {'reports': reports_list})



def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('report_list')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['confirm_password']

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        user = User.objects.create_user(username=username, password=password)
        login(request, user)  # auto-login after register
        return redirect('report_list')

    return render(request, 'register.html')


def user_logout(request):
    logout(request)
    return redirect('report_list')
