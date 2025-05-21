# reports/tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

class ReportListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('report_list')

        # Mocked sample data
        self.sample_reports = [
            {'title': 'Broken Light', 'description': 'Light is out', 'location': 'Street A', 'type': 'street_light', 'latitude': 0, 'longitude': 0},
            {'title': 'Pothole', 'description': 'Big hole', 'location': 'Street B', 'type': 'pothole', 'latitude': 0, 'longitude': 0},
            {'title': 'Accident', 'description': 'Two cars hit', 'location': 'Street C', 'type': 'accident', 'latitude': 0, 'longitude': 0},
        ]

    @patch('reports.views.get_reports_from_firebase')
    def test_filter_reports_by_type(self, mock_get_reports):
        mock_get_reports.return_value = self.sample_reports

        # Filter by pothole
        response = self.client.get(self.url, {'type': 'pothole'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'report_list.html')

        reports = response.context['page_obj'].object_list
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]['type'], 'pothole')
        self.assertEqual(reports[0]['title'], 'Pothole')

    @patch('reports.views.get_reports_from_firebase')
    def test_no_filter_returns_all(self, mock_get_reports):
        mock_get_reports.return_value = self.sample_reports

        response = self.client.get(self.url)  # no ?type=
        self.assertEqual(response.status_code, 200)

        reports = response.context['page_obj'].object_list
        self.assertEqual(len(reports), 3)
