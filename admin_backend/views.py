# //Malik - Sprint 2 - Admin - BSPM25T29-XX
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from beer_sheva_backend.firebase import initialize_firebase

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

        # New: Update status
        if action == "update_status":
            new_status = request.POST.get("status")
            if new_status:
                db.collection("Reports").document(report_id).update({"status": new_status})

        return redirect("admin-firebase-reports")

    # GET request logic
    reports_ref = db.collection("Reports").stream()
    users_ref = db.collection("Users").stream()
    users = []
    for user in users_ref:
        data = user.to_dict()
        # Debug print
        print(user.id, data)
        if data.get("role", "").lower() == "worker":
            users.append({
                "username": data.get("username", ""),
                "id": user.id,  # Use Firestore document ID
            })

    reports = [{**doc.to_dict(), "id": doc.id} for doc in reports_ref]

    return render(request, "admin_backend/admin_dashboard.html", {
        "reports": reports,
        "users": users,  # Lowercase for context and template
    })
