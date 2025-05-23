from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from beer_sheva_backend.firebase import initialize_firebase

db = initialize_firebase()

@csrf_exempt
def admin_dashboard(request):
    # Handle form actions (delete, assign, update)
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

    # Get reports
    reports_ref = db.collection("Reports").stream()
    reports = []
    for doc in reports_ref:
        data = doc.to_dict()
        data["id"] = doc.id
        reports.append(data)

    # Sort reports by created_at (if exists, otherwise fallback)
    def get_created_at(report):
        v = report.get("created_at")
        if not v:
            return 0
        if hasattr(v, "timestamp"):
            return v.timestamp()
        # Try to parse string
        from datetime import datetime
        try:
            return datetime.fromisoformat(str(v)).timestamp()
        except Exception:
            return 0

    reports = sorted(reports, key=get_created_at, reverse=True)

    paginator = Paginator(reports, page_size)
    page_obj = paginator.get_page(page)

    return render(request, "admin_backend/admin_dashboard.html", {
        "reports": page_obj.object_list,
        "users": users,
        "page": page_obj.number,
        "page_range": paginator.page_range,
    })
