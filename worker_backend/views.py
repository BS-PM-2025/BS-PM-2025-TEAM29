from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from beer_sheva_backend.firebase import initialize_firebase
from datetime import datetime
from firebase_admin import firestore

db = initialize_firebase()

@csrf_exempt
def worker_dashboard(request):
    print("=== [worker_dashboard] Called ===")
    firestore_user_id = request.session.get('firebase_uid')
    print("firestore_user_id (from session):", firestore_user_id)
    if not firestore_user_id:
        print("[worker_dashboard] No firestore_user_id in session. Redirecting to login.")
        return redirect('login')

    # Always fetch the worker and jobs, since needed for leave_job and potentially other actions
    worker_doc = db.collection("Users").document(firestore_user_id).get()
    if worker_doc.exists:
        worker_dict = worker_doc.to_dict()
        print("worker_doc found:", worker_dict)
    else:
        worker_dict = {}
        print("worker_doc not found!")

    jobs = worker_dict.get("jobs", [])

    if request.method == "POST":
        print("[worker_dashboard] POST received:", request.POST.dict())
        action = request.POST.get("action")
        report_id = request.POST.get("report_id")
        print("POST action:", action)
        print("POST report_id:", report_id)
        now = datetime.utcnow()
#https://sce-ac.atlassian.net/browse/BSPM25T29-32
        if action == "mark_done":
            print(f"Updating report {report_id} status to 'done' in Firestore.")
            db.collection("Reports").document(report_id).update({"status": "done"})
#https://sce-ac.atlassian.net/browse/BSPM25T29-36
        elif action == "add_equipment_issue":
            text = request.POST.get("equipment_issue", "")
            print(f"Adding equipment issue to report {report_id}: {text}")
            if text.strip():
                db.collection("Reports").document(report_id).update({
                    "equipment_issues": firestore.ArrayUnion([
                        {"worker_id": firestore_user_id, "text": text, "timestamp": now}
                    ])
                })
#https://sce-ac.atlassian.net/browse/BSPM25T29-41
        elif action == "add_internal_note":
            note = request.POST.get("internal_note", "")
            print(f"Adding internal note to report {report_id}: {note}")
            if note.strip():
                db.collection("Reports").document(report_id).update({
                    "internal_notes": firestore.ArrayUnion([
                        {"worker_id": firestore_user_id, "note": note, "timestamp": now}
                    ])
                })

        elif action == "leave_job":
            print(f"Worker {firestore_user_id} leaving report {report_id}")
            # Remove job from worker's jobs list
            new_jobs = [job for job in jobs if job.get("report_id") != report_id]
            db.collection("Users").document(firestore_user_id).update({"jobs": new_jobs})
            # Optionally remove assignment from the report
            db.collection("Reports").document(report_id).update({"assigned_worker_id": firestore.DELETE_FIELD})

        return redirect("worker-dashboard")

    # Only assigned reports
    my_report_ids = [job.get("report_id") for job in jobs if job.get("role") == "worker"]
    print("my_report_ids:", my_report_ids)

    reports = []
    for report_id in my_report_ids:
        print(f"Fetching report with ID: {report_id}")
        doc = db.collection("Reports").document(report_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            data.setdefault("equipment_issues", [])
            data.setdefault("internal_notes", [])
            data["safety_instructions"] = "הנחיות בטיחות: לשמור מרחק, ללבוש ציוד מגן, וכו'."   #https://sce-ac.atlassian.net/browse/BSPM25T29-39
            lat, lng = data.get("latitude"), data.get("longitude")
            if lat and lng:
                data["google_maps_link"] = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"  #https://sce-ac.atlassian.net/browse/BSPM25T29-40
            else:
                data["google_maps_link"] = "#"
            print(f"Report data for {report_id}:", data)
            reports.append(data)
        else:
            print(f"Report {report_id} not found!")

    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = 15
    paginator = Paginator(reports, page_size)
    page_obj = paginator.get_page(page)

    # For the map, all paginated reports (on this page)
    map_reports = [
        {
            "title": r["title"],
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "description": r.get("description"),
            "id": r.get("id"),
        }
        for r in page_obj.object_list
        if r.get("latitude") and r.get("longitude")
    ]

    return render(request, "worker_backend/worker_dashboard.html", {
        "reports": page_obj.object_list,
        "page": page_obj.number,
        "page_range": paginator.page_range,
        "user_id": firestore_user_id,
        "map_reports": map_reports,
    })
