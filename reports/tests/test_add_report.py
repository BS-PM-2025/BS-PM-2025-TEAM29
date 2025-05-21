from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from reports.models import Report
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
import io

class AddReportWithImageTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('add_report')  # Ensure your URL name matches
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x89\x61',  # Minimal valid binary for a GIF/JPG
            content_type='image/jpeg'
        )

    def _attach_session(self, request):
        """Helper to attach session manually to a request (for mocking user session)"""
        middleware = SessionMiddleware(get_response=lambda r: None)
        middleware.process_request(request)
        request.session.save()

    @patch('beer_sheva_backend.firebase.save_report_to_firebase')
    @patch('firebase_admin.storage.bucket')
    def test_add_report_with_image(self, mock_bucket, mock_save_to_firebase):
        # Set up Firebase mock
        mock_blob = mock_bucket.return_value.blob.return_value
        mock_blob.public_url = 'https://fakeurl.com/test_image.jpg'
        mock_save_to_firebase.return_value = 'fake_report_id'

        # Simulate logged-in user
        session = self.client.session
        session['user_email'] = 'test@example.com'
        session.save()

        data = {
            'title': 'Test Report',
            'description': 'This is a test',
            'place': 'Beer Sheva',
            'latitude': 31.25,
            'longitude': 34.79,
            'type': 'pothole',  # assuming "pothole" is a valid choice
        }

        with open('media/test_image.jpg', 'wb') as f:  # Create a dummy file
            f.write(b'\x47\x49\x46\x38\x89\x61')

        with open('media/test_image.jpg', 'rb') as img:
            response = self.client.post(self.url, data={**data, 'image': img}, follow=True)

        self.assertEqual(response.status_code, 200)
        mock_bucket.assert_called_once()
        mock_blob.upload_from_file.assert_called_once()
        mock_save_to_firebase.assert_called_once()
        self.assertIn('report_confirmation', response.redirect_chain[-1][0])  # Final redirect

    def tearDown(self):
        import os
        try:
            os.remove('media/test_image.jpg')
        except FileNotFoundError:
            pass
