# worker_backend/tests/test_worker_actions.py

from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from unittest.mock import patch, MagicMock, ANY
import worker_backend.views as views

def add_session(request, uid):
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session['firebase_uid'] = uid
    request.session.save()

class WorkerActionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        views.db = MagicMock()
        # stub render & redirect so we don’t need a full Django template layer
        self.p_render = patch('worker_backend.views.render'); self.mock_render = self.p_render.start()
        self.p_redirect = patch('worker_backend.views.redirect'); self.mock_redirect = self.p_redirect.start()

    def tearDown(self):
        patch.stopall()

    def test_BSPM25T29_32_mark_report_fixed(self):
        """Jira-32: worker marks a report as fixed."""
        uid, rid = 'userX', 'rep1'
        request = self.factory.post('/worker/', {'action': 'mark_done', 'report_id': rid})
        add_session(request, uid)
        # simulate worker exists
        views.db.collection.return_value.document.return_value.get.return_value = MagicMock(exists=True, to_dict=lambda: {})
        views.worker_dashboard(request)
        views.db.collection.assert_any_call('Reports')
        views.db.collection('Reports').document(rid).update.assert_called_once_with({'status': 'done'})
        self.mock_redirect.assert_called_once_with('worker-dashboard')

     def test_BSPM25T29_36_report_equipment_issue(self):
        """Jira-36: worker reports missing/broken equipment."""
        uid, rid, issue = 'userY', 'rep2', 'broken pump'
        request = self.factory.post('/worker/', {
            'action': 'add_equipment_issue',
            'report_id': rid,
            'equipment_issue': issue
        })
        add_session(request, uid)
        # simulate existing job doc
        views.db.collection.return_value.document.return_value.get.return_value = MagicMock(exists=True, to_dict=lambda: {'jobs': []})
        views.worker_dashboard(request)
        update_data = views.db.collection('Reports').document(rid).update.call_args[0][0]
        self.assertIn('equipment_issues', update_data)
        self.mock_redirect.assert_called_once_with('worker-dashboard')

    def test_BSPM25T29_39_receive_safety_notifications(self):
        """Jira-39: worker gets notifications by report type."""
        # This one may live in a different view or service; here’s a simple example:
        from worker_backend.notifications import notify_worker
        views.db.collection.return_value.document.return_value.get.return_value = MagicMock(
            exists=True,
            to_dict=MagicMock(return_value={'jobs': [], 'type': 'severe'})
        )
        # patch the push notification client
        with patch('worker_backend.notifications.push') as mock_push:
            notify_worker('userZ')
            mock_push.assert_called_with('userZ', ANY)

    def test_BSPM25T29_40_launch_navigation(self):
        """Jira-40: worker launches in-app navigation."""
        uid, rid = 'userA', 'rep3'
        request = self.factory.post('/worker/', {'action': 'navigate', 'report_id': rid})
        add_session(request, uid)
        # simulate report with coords
        rep_doc = MagicMock(exists=True, to_dict=lambda:{'latitude':1.1,'longitude':2.2})
        views.db.collection.return_value.document.return_value.get.return_value = rep_doc
        views.worker_dashboard(request)
        self.mock_redirect.assert_called_once()  # e.g. to a map view URL

    def test_BSPM25T29_41_save_internal_note(self):
        """Jira-41: worker saves an internal note."""
        uid, rid, note = 'userB', 'rep4', 'check valve'
        request = self.factory.post('/worker/', {
            'action': 'add_internal_note',
            'report_id': rid,
            'internal_note': note
        })
        add_session(request, uid)
        views.db.collection.return_value.document.return_value.get.return_value = MagicMock(exists=True, to_dict=lambda: {'jobs': []})
        views.worker_dashboard(request)
        update_data = views.db.collection('Reports').document(rid).update.call_args[0][0]
        self.assertIn('internal_notes', update_data)
        self.mock_redirect.assert_called_once_with('worker-dashboard')

