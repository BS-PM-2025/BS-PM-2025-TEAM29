# admin_backend/tests/test_admin_actions.py

import datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from admin_backend import views

class AdminDashboardTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # 1) Inject a MagicMock Firestore client into views.db
        self.p_init = patch('admin_backend.views.initialize_firebase')
        self.mock_init = self.p_init.start()
        self.mock_db = MagicMock()
        self.mock_init.return_value = self.mock_db
        views.db = self.mock_db

        # 2) Split Reports vs Users collections
        self.mock_reports = MagicMock()
        self.mock_users = MagicMock()
        def coll(name):
            return self.mock_reports if name == 'Reports' else self.mock_users
        self.mock_db.collection.side_effect = coll

        # 3) Patch render & redirect so we can inspect calls
        self.p_render = patch('admin_backend.views.render')
        self.mock_render = self.p_render.start()
        self.p_redirect = patch('admin_backend.views.redirect')
        self.mock_redirect = self.p_redirect.start()

    def tearDown(self):
        patch.stopall()

    def test_BSPM25T29_29_get_dashboard_empty(self):
        """BSPM25T29-29: manager sees no users/reports → empty dashboard."""
        self.mock_users.stream.return_value = []
        self.mock_reports.stream.return_value = []

        request = self.factory.get('/admin/', {'page': '1'})
        views.admin_dashboard(request)

        self.mock_render.assert_called_once()
        _, template, ctx = self.mock_render.call_args[0]
        self.assertEqual(template, 'admin_backend/admin_dashboard.html')
        self.assertEqual(ctx['users'], [])
        self.assertEqual(ctx['reports'], [])
        self.assertEqual(ctx['page'], 1)
        self.assertEqual(ctx['type_hebrew_map'], views.TYPE_HEBREW_MAP)

        expected_danger = [
            views.TYPE_HEBREW_MAP[t]
            for t in views.MOST_DANGEROUS_TYPES
            if t in views.TYPE_HEBREW_MAP
        ]
        self.assertEqual(ctx['dangerous_types'], expected_danger)

    def test_BSPM25T29_27_get_dashboard_sorting(self):
        """BSPM25T29-27: manager dashboard sorts dangerous reports first."""
        self.mock_users.stream.return_value = []

        # two reports: r2 (Other), r1 (Road)
        doc1 = MagicMock(id='r1', to_dict=MagicMock(return_value={'type': 'Road'}))
        doc2 = MagicMock(id='r2', to_dict=MagicMock(return_value={'type': 'Other'}))
        self.mock_reports.stream.return_value = [doc2, doc1]

        request = self.factory.get('/admin/', {'page': '1'})
        views.admin_dashboard(request)

        _, _, ctx = self.mock_render.call_args[0]
        ids = [r['id'] for r in ctx['reports']]
        self.assertEqual(ids, ['r1', 'r2'])
        self.assertEqual(ctx['reports'][0]['type_he'], views.TYPE_HEBREW_MAP['Road'])
        self.assertEqual(ctx['reports'][1]['type_he'], '-')

    def test_post_delete_report(self):
        """BSPM25T29-42: manager deletes a report."""
        request = self.factory.post('/admin/', {
            'action': 'delete_report',
            'report_id': 'rid'
        })
        views.admin_dashboard(request)

        self.mock_reports.document.assert_called_once_with('rid')
        self.mock_reports.document('rid').delete.assert_called_once()
        self.mock_redirect.assert_called_once_with('admin-firebase-reports')

    def test_post_update_status(self):
        """BSPM25T29-42: manager updates report status."""
        request = self.factory.post('/admin/', {
            'action': 'update_status',
            'report_id': 'rid',
            'status': 'done'
        })
        views.admin_dashboard(request)

        self.mock_reports.document.assert_called_with('rid')
        self.mock_reports.document('rid').update.assert_called_once_with({'status': 'done'})
        self.mock_redirect.assert_called_once_with('admin-firebase-reports')

    def test_post_assign_worker(self):
        """BSPM25T29-42: manager assigns a worker to a report."""
        user_doc = MagicMock(id='w1')
        user_doc.to_dict.return_value = {'role': 'worker', 'jobs': []}
        self.mock_users.stream.return_value = [user_doc]

        request = self.factory.post('/admin/', {
            'action': 'assign_worker',
            'report_id': 'rid',
            'worker_id': 'w1'
        })
        views.admin_dashboard(request)

        # Reports/rid update
        self.mock_reports.document.assert_any_call('rid')
        self.mock_reports.document('rid').update.assert_called_once_with({'assigned_worker_id': 'w1'})

        # Users/w1 update
        self.mock_users.stream.assert_called_once()
        updated_jobs = [{'report_id': 'rid', 'role': 'worker'}]
        self.mock_users.document('w1').update.assert_called_once_with({'jobs': updated_jobs})

        self.mock_redirect.assert_called_once_with('admin-firebase-reports')


class AdminReportDetailsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # inject fake db
        self.p_init = patch('admin_backend.views.initialize_firebase')
        self.mock_init = self.p_init.start()
        self.mock_db = MagicMock()
        self.mock_init.return_value = self.mock_db
        views.db = self.mock_db

        # patch render
        self.p_render = patch('admin_backend.views.render')
        self.mock_render = self.p_render.start()

    def tearDown(self):
        patch.stopall()

    def test_BSPM25T29_42_report_details_not_found(self):
        """BSPM25T29-42: manager views details → report not found."""
        doc = MagicMock(exists=False)
        self.mock_db.collection.return_value.document.return_value.get.return_value = doc

        request = self.factory.get('/admin/details/foo/')
        views.admin_report_details(request, 'foo')

        self.mock_render.assert_called_once_with(
            request,
            'admin_backend/report_details.html',
            {'not_found': True}
        )

    def test_BSPM25T29_42_report_details_found(self):
        """BSPM25T29-42: manager views details → report found."""
        doc = MagicMock(exists=True)
        doc.id = 'rid'
        doc.to_dict.return_value = {'type': 'Flooding', 'foo': 'bar'}
        self.mock_db.collection.return_value.document.return_value.get.return_value = doc

        request = self.factory.get('/admin/details/rid/')
        views.admin_report_details(request, 'rid')

        expected = {
            'id': 'rid',
            'type': 'Flooding',
            'foo': 'bar',
            'type_he': views.TYPE_HEBREW_MAP.get('Flooding', '-')
        }
        self.mock_render.assert_called_once_with(
            request,
            'admin_backend/report_details.html',
            {'report': expected, 'type_hebrew_map': views.TYPE_HEBREW_MAP}
        )
