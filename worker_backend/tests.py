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

