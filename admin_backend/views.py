from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from beer_sheva_backend.firebase import initialize_firebase

db = initialize_firebase()

REPORTS_PER_PAGE = 10

@csrf_exempt
def admin_dashboard(request):
    # --- POST logic unchanged ---
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

    # --- GET Logic (Pagination) ---
    undone_page = int(request.GET.get("undone_page", 1))
    done_page = int(request.GET.get("done_page", 1))

    reports_ref = db.collection("Reports").stream()
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

    reports = []
    for doc in reports_ref:
        data = doc.to_dict()
        data["id"] = doc.id
        reports.append(data)

    def parse_created_at(r):
        v = r.get("created_at")
        if not v:
            return 0
        if hasattr(v, "timestamp"):
            return v.timestamp()
        from datetime import datetime
        try:
            return datetime.fromisoformat(str(v)).timestamp()
        except Exception:
            return 0

    undone_reports = [r for r in reports if r.get("status") not in ["הושלם", "done", "completed"]]
    completed_reports = [r for r in reports if r.get("status") in ["הושלם", "done", "completed"]]

    undone_reports = sorted(undone_reports, key=parse_created_at, reverse=True)
    completed_reports = sorted(completed_reports, key=parse_created_at, reverse=True)

    # --- Pagination logic ---
    def paginate(items, page, per_page):
        total = len(items)
        pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, pages))
        start = (page - 1) * per_page
        end = start + per_page
        return items[start:end], page, pages

    undone_page_reports, undone_current, undone_total_pages = paginate(undone_reports, undone_page, REPORTS_PER_PAGE)
    done_page_reports, done_current, done_total_pages = paginate(completed_reports, done_page, REPORTS_PER_PAGE)
    return render(request, "admin_backend/admin_dashboard.html", {
        "undone_reports": undone_page_reports,
        "undone_page": undone_current,
        "undone_pages": undone_total_pages,
        "undone_page_range": range(1, undone_total_pages + 1),

        "completed_reports": done_page_reports,
        "done_page": done_current,
        "done_pages": done_total_pages,
        "done_page_range": range(1, done_total_pages + 1),

        "users": users,
    })
