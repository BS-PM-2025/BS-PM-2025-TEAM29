# //Malik - Sprint 2 - Admin - BSPM25T29-7
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
        return redirect("admin-firebase-reports")

    reports_ref = db.collection("Reports").stream()
    reports = [{**doc.to_dict(), "id": doc.id} for doc in reports_ref]
    return render(request, "admin_backend/admin_dashboard.html", {
        "reports": reports,
    })
