from django.shortcuts import render
from firebase_admin import firestore
from beer_sheva_backend.firebase import initialize_firebase, get_reports_from_firebase
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

import logging


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
                location = form.cleaned_data['place']  # Assuming place is the location field
                latitude = form.cleaned_data['latitude']
                longitude = form.cleaned_data['longitude']
                report_type = form.cleaned_data['type']  # Get the type of the report

                logger.info(f"Extracted data: title={title}, description={description}, "
                            f"location={location}, latitude={latitude}, longitude={longitude}, type={report_type}")

                # Save the report to Firebase
                try:
                    report_id = save_report_to_firebase(title, description, location, latitude, longitude, report_type)
                    logger.info(f"Report saved to Firebase with ID: {report_id}")
                except Exception as e:
                    logger.error(f"Error saving report to Firebase: {e}")
                    return render(request, 'reports/add_report.html', {'form': form, 'error': 'Error saving to Firebase'})

                # Optionally, save the Firebase ID to the report in the local database
                report.firebase_id = report_id  # Assuming you have added 'firebase_id' to the Report model
                report.save()
                logger.info(f"Firebase ID saved to report: {report.firebase_id}")

                return redirect('report_list')  # Redirect to the list of reports

            except Exception as e:
                logger.error(f"Error saving the report to local database: {e}")
                return render(request, 'reports/add_report.html', {'form': form, 'error': 'Error saving the report'})

        else:
            logger.warning("Form is not valid.")
            return render(request, 'reports/add_report.html', {'form': form, 'error': 'Form is invalid'})

    else:
        form = ReportForm()

    return render(request, 'reports/add_report.html', {'form': form})


def report_list(request):
    # Retrieve the report type from the query parameters
    report_type = request.GET.get('type', None)

    # Fetch reports from Firebase, potentially filtered by report type
    reports_list = get_reports_from_firebase(report_type=report_type)

    # Add a 'type_name' to each report based on the 'type_dict'
    for report in reports_list:
        report['type_name'] = type_dict.get(report.get('type'), 'לא ידוע')  # 'לא ידוע' for unknown types

    # Set up pagination (show 5 reports per page)
    paginator = Paginator(reports_list, 5)  # 5 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the reports to the template
    return render(request, 'reports/report_list.html', {
        'page_obj': page_obj,
        'reports_data': reports_list,  # Pass the report data for the map
        'type_dict': type_dict,  # Add the dictionary to the context (if needed for further use in the template)
    })