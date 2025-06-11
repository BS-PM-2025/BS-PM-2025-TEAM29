from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from beer_sheva_backend.firebase import initialize_firebase
from django.urls import reverse

MOST_DANGEROUS_TYPES = [
    "Road", "Accident", "Flooding", "WaterLeak", "Electricity",
    "Pothole", "Infrastructure", "Vandalism"
]
TYPE_HEBREW_MAP = {
    "Road": "נזק לכביש",
    "Accident": "תאונות",
    "Waste": "ניהול פסולת",
    "TrafficSignal": "בעיות רמזורים",
    "Infrastructure": "תשתית ציבורית",
    "Streetlight": "תאורת רחוב",
    "Pothole": "בורות בכביש",
    "Parking": "בעיות חנייה",
    "Flooding": "הצפות",
    "Graffiti": "גרפיטי",
    "Animal": "בעיות עם בעלי חיים",
    "Noise": "רעש",
    "Vandalism": "ונדליזם",
    "WaterLeak": "דליפת מים",
    "Electricity": "בעיות חשמל",
    "Playground": "בעיות במגרש משחקים",
    "PublicRestroom": "שירותים ציבוריים",
    "tree branches": "ענפי עצים",
    "Garden care": "טיפול בגנים",
}

db = initialize_firebase()

@csrf_exempt
def admin_dashboard(request):
    if request.method == "POST":
        action = request.POST.get("action")
        report_id = request.POST.get("report_id")

        if action == "delete_report":
            db.collection("Reports").document(report_id).delete()

        if action == "assign_worker":
            worker_inner_id = request.POST.get("worker_id")
            if worker_inner_id:
                db.collection("Reports").document(report_id).update({"assigned_worker_id": worker_inner_id})
                users_ref = db.collection("Users").stream()
                for user in users_ref:
                    user_data = user.to_dict()
                    if user_data.get("role", "").lower() == "worker" and user.id == worker_inner_id:
                        user_ref = db.collection("Users").document(user.id)
                        jobs = user_data.get("jobs", [])
                        if not any(job.get("report_id") == report_id for job in jobs):
                            jobs.append({"report_id": report_id, "role": "worker"})
                            user_ref.update({"jobs": jobs})
                        break

        if action == "update_status":
            new_status = request.POST.get("status")
            if new_status:
                db.collection("Reports").document(report_id).update({"status": new_status})

        return redirect("admin-firebase-reports")

    # GET: Show dashboard with pagination
    page = int(request.GET.get('page', 1))
    page_size = 15

    # Get users
    users_ref = db.collection("Users").stream()
    users = []
    for user in users_ref:
        data = user.to_dict()
        if data.get("role", "").lower() == "worker":
            users.append({
                "username": data.get("username", ""),
                "id": user.id,
                "email": data.get("email", ""),
            })

    # Get reports, collect all (for preview), sort dangerous ones first
    reports_ref = db.collection("Reports").stream()
    reports = []
    for doc in reports_ref:
        data = doc.to_dict()
        data["id"] = doc.id
        # Add Hebrew type mapping for the template
        data["type_he"] = TYPE_HEBREW_MAP.get(data.get("type"), "-")
        reports.append(data)

    # Dangerous first, then others by date
    def is_dangerous(report):
        return report.get("type") in MOST_DANGEROUS_TYPES

    def get_created_at(report):
        v = report.get("created_at")
        if not v:
            return 0
        if hasattr(v, "timestamp"):
            return v.timestamp()
        from datetime import datetime
        try:
            return datetime.fromisoformat(str(v)).timestamp()
        except Exception:
            return 0

    reports = sorted(
        reports,
        key=lambda r: (
            0 if is_dangerous(r) else 1,  # dangerous first
            -get_created_at(r)
        )
    )

    paginator = Paginator(reports, page_size)
    page_obj = paginator.get_page(page)

    return render(request, "admin_backend/admin_dashboard.html", {
        "reports": page_obj.object_list,
        "users": users,
        "page": page_obj.number,
        "page_range": paginator.page_range,
        "type_hebrew_map": TYPE_HEBREW_MAP,
        "dangerous_types": [TYPE_HEBREW_MAP[t] for t in MOST_DANGEROUS_TYPES if t in TYPE_HEBREW_MAP],
    })


def admin_report_details(request, report_id):
    # Show all info for this report
    doc = db.collection("Reports").document(report_id).get()
    if not doc.exists:
        return render(request, "admin_backend/report_details.html", {"not_found": True})

    report = doc.to_dict()
    report["id"] = doc.id
    report["type_he"] = TYPE_HEBREW_MAP.get(report.get("type"), "-")

    return render(request, "admin_backend/report_details.html", {
        "report": report,
        "type_hebrew_map": TYPE_HEBREW_MAP,
    })


