import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from firebase_admin import firestore
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Report, Profile, Notification, REPORT_TO_JOBS
from .forms import ReportForm, type_dict
from .serializers import ReportSerializer
from beer_sheva_backend.firebase import (
    get_report_by_id,
    get_reports_from_firebase,
    initialize_firebase,
    save_report_to_firebase,
)
from .forms import REPORT_TYPES, REPORT_TYPE_LABELS, ReportForm

logger = logging.getLogger(__name__)


def add_report(request):
    if request.method == "POST":
        form = ReportForm(request.POST)
        # Debug: see exactly what came in
        logger.debug("add_report POST data: %s", request.POST)

        if not form.is_valid():
            # Surface field errors
            logger.debug("Form invalid: %s", form.errors)
            return render(request, "add_report.html", {
                "form": form,
                "error": form.errors.as_json()
            })

        # 1) Save to local DB
        try:
            report = form.save()
            logger.info("Report saved locally: %s", report)
        except Exception as e:
            logger.exception("Error saving report locally")
            return render(request, "add_report.html", {
                "form": form,
                "error": f"Database error: {e}"
            })

        # 2) Notify matching workers
        try:
            job_list = REPORT_TO_JOBS.get(report.type, [])
            workers = Profile.objects.filter(is_worker=True, job__in=job_list)
            for worker in workers:
                Notification.objects.create(
                    profile=worker,
                    report=report,
                    message=f"New {report.get_type_display()} report: {report.title}"
                )
            logger.info("Notifications created for jobs: %s", job_list)
        except Exception as e:
            logger.exception("Error creating notifications")
            # non-fatal; proceed

        # 3) Save to Firebase
        try:
            cleaned = form.cleaned_data
            report_id = save_report_to_firebase(
                cleaned["title"],
                cleaned["description"],
                cleaned["place"],
                cleaned["latitude"],
                cleaned["longitude"],
                cleaned["type"],
            )
            logger.info("Report saved to Firebase: %s", report_id)
        except Exception as e:
            logger.exception("Error saving to Firebase")
            return render(request, "add_report.html", {
                "form": form,
                "error": f"Firebase error: {e}"
            })

        # 4) Update local record with Firebase ID
        try:
            report.firebase_id = report_id
            report.save()
        except Exception as e:
            logger.exception("Error updating Firebase ID in local DB")
            return render(request, "add_report.html", {
                "form": form,
                "error": f"Update error: {e}"
            })

        # 5) All done!
        messages.success(request, "Your report has been submitted successfully!")
        return redirect("report_confirmation", report_id=report_id)

    # GET
    form = ReportForm()
    return render(request, "add_report.html", {"form": form})

def report_confirmation(request, report_id):
    report = get_report_by_id(report_id)
    if not report:
        return redirect("report_list")
    return render(request, "confirmation.html", {"report": report})


def report_list(request):
    report_type = request.GET.get("type", None)
    reports_list = get_reports_from_firebase(report_type=report_type)

    for report in reports_list:
        report["type_name"] = REPORT_TYPE_LABELS.get(report.get("type"), "לא ידוע")

    paginator = Paginator(reports_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "report_list.html",
        {
            "page_obj":    page_obj,
            "reports_data": reports_list,
            "type_dict":   type_dict,
        },
    )


def map_view(request):
    reports_list = get_reports_from_firebase()
    return render(request, "map.html", {"reports": reports_list})


@login_required
def admin_dashboard(request):
    # show pending local Reports for approval
    pending_reports = Report.objects.filter(approved=False).order_by("-report_time")
    approved_reports = Report.objects.filter(approved=True).order_by("-report_time")


    return render(request, "admin_dashboard.html", {
            "pending_reports": pending_reports,
            "approved_reports": approved_reports,
    })

@login_required
def worker_dashboard(request):
    profile = request.user.profile
    if not profile.is_worker:
        messages.error(request, "Access denied: you are not registered as a worker.")
        return redirect("report_list")

    job_code = profile.job

    # 1) Fetch all reports from Firebase
    all_reports = get_reports_from_firebase()

    # 2) Find which Firebase IDs have been approved locally
    approved_ids = set(
        Report.objects
              .filter(approved=True)
              .values_list("firebase_id", flat=True)
    )

    # 3) Filter to only those both approved *and* matching this job_code
    filtered = [
        rpt for rpt in all_reports
        if rpt.get("firebase_id") in approved_ids
           and job_code in REPORT_TO_JOBS.get(rpt.get("type"), [])
    ]

    # 4) Annotate each with the human-readable type label
    for rpt in filtered:
        rpt["type_name"] = REPORT_TYPE_LABELS.get(rpt.get("type"), rpt.get("type"))

    # 5) Paginate
    paginator   = Paginator(filtered, 5)
    page_number = request.GET.get("page")
    page_obj    = paginator.get_page(page_number)

    return render(request, "worker_dashboard.html", {
        "page_obj":  page_obj,
        "job_label": profile.get_job_display(),
    })

def user_login(request):
    if request.method == "POST":
        username  = request.POST["username"]
        password  = request.POST["password"]
        user_type = request.POST.get("user_type", "user")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 1) Log them in
            login(request, user)

            # 2) Admins go to admin_dashboard
            if user.is_staff or user.is_superuser:
                return redirect("admin_dashboard")

            # 3) Enforce matching user_type vs. profile flag
            if user_type == "worker" and not user.profile.is_worker:
                messages.error(request, "You are not registered as a worker.")
                logout(request)
                return redirect("login")
            if user_type == "user" and user.profile.is_worker:
                messages.error(request, "This account is registered as a worker. Please select Worker.")
                logout(request)
                return redirect("login")

            # 4) Workers go to worker_dashboard
            if user.profile.is_worker:
                return redirect("worker_dashboard")

            # 5) Everyone else goes to the regular report list
            return redirect("report_list")

        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")
@login_required

def register_view(request):
    if request.method == "POST":
        username  = request.POST["username"]
        password  = request.POST["password"]
        password2 = request.POST["confirm_password"]
        user_type = request.POST.get("user_type", "user")
        job_code  = request.POST.get("job", "")

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        user = User.objects.create_user(username=username, password=password)

        profile = user.profile
        if user_type == "worker" and job_code:
            profile.is_worker = True
            profile.job       = job_code
            profile.save()

        login(request, user)
        return redirect("report_list")

    return render(request, "register.html")


def user_logout(request):
    logout(request)
    return redirect("report_list")

@login_required
def mark_notifications_read(request):
    request.user.profile.notifications.filter(is_read=False).update(is_read=True)
    return redirect("worker_dashboard")
