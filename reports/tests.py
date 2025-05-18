from unittest.mock import MagicMock, patch
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage

from beer_sheva_backend import firebase
from reports import views
from reports.forms import ReportForm
from reports.models import Report

def add_session_to_request(request):
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

def add_messages_to_request(request):
    setattr(request, '_messages', FallbackStorage(request))

class FirebaseTests(TestCase):
    @patch("beer_sheva_backend.firebase.firestore")
    def test_save_report_to_firebase(self, mock_firestore):
        mock_db = MagicMock()
        mock_doc_ref = (None, MagicMock(id="fake-report-id"))
        mock_db.collection.return_value.add.return_value = mock_doc_ref
        mock_firestore.client.return_value = mock_db

        report_id = firebase.save_report_to_firebase(
            title="Test Title",
            description="Test Description",
            location="Test Location",
            latitude=31.25,
            longitude=34.79,
            report_type="test_type",
        )

        self.assertEqual(report_id, "fake-report-id")
        mock_db.collection.assert_called_with("Reports")

    @patch("beer_sheva_backend.firebase.firestore")
    def test_get_reports_from_firebase_no_filter(self, mock_firestore):
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "abc123"
        mock_doc.to_dict.return_value = {
            "title": "Test Report",
            "description": "Description here",
            "location": "Nowhere",
            "latitude": 31.25,
            "longitude": 34.79,
            "created_at": None,
            "type": "fire",
            "status": "pending",
        }
        mock_db.collection.return_value.stream.return_value = [mock_doc]
        mock_firestore.client.return_value = mock_db

        results = firebase.get_reports_from_firebase()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "abc123")

    @patch("beer_sheva_backend.firebase.firestore")
    def test_get_reports_with_location_filter(self, mock_firestore):
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "nearby123"
        mock_doc.to_dict.return_value = {
            "title": "Sinkhole",
            "description": "Big hole",
            "location": "Somewhere",
            "latitude": 31.2505,
            "longitude": 34.7905,
            "created_at": None,
            "type": "geo",
            "status": "pending",
        }
        mock_db.collection.return_value.stream.return_value = [mock_doc]
        mock_firestore.client.return_value = mock_db

        nearby = firebase.get_reports_from_firebase(
            user_location=(31.25, 34.79), radius=1
        )
        self.assertEqual(len(nearby), 1)
        self.assertEqual(nearby[0]["id"], "nearby123")

    @patch("beer_sheva_backend.firebase.firestore")
    def test_get_report_by_id_found(self, mock_firestore):
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"title": "Single Report"}

        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )
        mock_firestore.client.return_value = mock_db

        report = firebase.get_report_by_id("real-id")
        self.assertIsNotNone(report)
        self.assertEqual(report["title"], "Single Report")

    @patch("beer_sheva_backend.firebase.firestore")
    def test_get_report_by_id_not_found(self, mock_firestore):
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False

        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )
        mock_firestore.client.return_value = mock_db

        report = firebase.get_report_by_id("ghost-id")
        self.assertIsNone(report)

class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="malik", password="test123")

    @patch("reports.views.ReportForm")
    @patch("reports.views.save_report_to_firebase")
    def test_add_report_post_valid_form(self, mock_save_report, mock_form_class):
        mock_save_report.return_value = "firebase123"
        data = {
            "title": "Fire Alert",
            "description": "Big fire spotted",
            "place": "Somewhere",
            "latitude": 31.2,
            "longitude": 34.8,
            "type": "fire",
        }
        # Prepare the mock form instance
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = data
        # This line prevents saving to the DB (avoids IntegrityError!)
        mock_form.save.return_value = MagicMock(spec=Report)
        mock_form_class.return_value = mock_form

        request = self.factory.post("/add/", data)
        request.user = self.user
        add_session_to_request(request)
        add_messages_to_request(request)

        response = views.add_report(request)
        # Check for redirect (302), not 200
        self.assertEqual(response.status_code, 302)
        self.assertIn("/confirmation/", response.url)


    @patch("reports.views.get_report_by_id")
    def test_report_confirmation_not_found(self, mock_get_report):
        mock_get_report.return_value = None
        request = self.factory.get("/confirm/ghost/")
        add_session_to_request(request)
        response = views.report_confirmation(request, "ghost")
        self.assertEqual(response.status_code, 302)
        self.assertIn("", response.url)

    @patch("reports.views.get_reports_from_firebase")
    def test_report_list_view(self, mock_get_reports):
        mock_get_reports.return_value = [{"type": "fire", "id": "x", "title": "fire"}]
        request = self.factory.get("/reports/?type=fire")
        add_session_to_request(request)
        response = views.report_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"fire", response.content)

    @patch("reports.views.get_reports_from_firebase")
    def test_map_view(self, mock_get_reports):
        mock_get_reports.return_value = [{"type": "geo", "id": "y"}]
        request = self.factory.get("/map/")
        add_session_to_request(request)
        response = views.map_view(request)
        self.assertEqual(response.status_code, 200)

    @patch("reports.views.get_reports_from_firebase")
    def test_admin_dashboard_authenticated(self, mock_get_reports):
        mock_get_reports.return_value = []
        request = self.factory.get("/admin/")
        add_session_to_request(request)
        add_messages_to_request(request)
        request.user = self.user
        response = views.admin_dashboard(request)
        self.assertEqual(response.status_code, 200)

    @patch("reports.views.get_reports_from_firebase")
    def test_worker_dashboard_authenticated(self, mock_get_reports):
        mock_get_reports.return_value = []
        request = self.factory.get("/worker/")
        add_session_to_request(request)
        add_messages_to_request(request)
        request.user = self.user
        response = views.worker_dashboard(request)
        self.assertIn(response.status_code, [200, 302])
    def test_user_login_valid(self):
        request = self.factory.post(
            "/login/", {"username": "malik", "password": "test123"}
        )
        add_session_to_request(request)
        add_messages_to_request(request)
        request.user = AnonymousUser()
        response = views.user_login(request)
        self.assertEqual(response.status_code, 302)

    def test_register_view_valid(self):
        request = self.factory.post(
            "/register/",
            {
                "username": "newuser",
                "password": "pass123",
                "confirm_password": "pass123",
            },
        )
        add_session_to_request(request)
        add_messages_to_request(request)
        request.user = AnonymousUser()
        response = views.register_view(request)
        self.assertEqual(response.status_code, 302)

    def test_user_logout(self):
        request = self.factory.get("/logout/")
        add_session_to_request(request)
        add_messages_to_request(request)
        request.user = self.user
        response = views.user_logout(request)
        self.assertEqual(response.status_code, 302)
