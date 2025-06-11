# reports/tests/test_views.py

from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch, MagicMock

import reports.views as views

def add_session_to_request(request):
    """Attach a session to the request."""
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()

def add_messages_to_request(request):
    """Attach fallback message storage to the request."""
    setattr(request, '_messages', FallbackStorage(request))


@override_settings(
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    MESSAGE_STORAGE='django.contrib.messages.storage.fallback.FallbackStorage'
)
class AddReportTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # unwrap decorator
        self.view = views.add_report.__wrapped__

        # patch dependencies
        self.p_form = patch('reports.views.ReportForm')
        self.mock_form_class = self.p_form.start()

        self.p_save = patch('reports.views.save_report_to_firebase')
        self.mock_save = self.p_save.start()

        self.p_bucket = patch('reports.views.storage.bucket')
        self.mock_bucket = self.p_bucket.start()

        self.p_render = patch('reports.views.render')
        self.mock_render = self.p_render.start()

        self.p_redirect = patch('reports.views.redirect')
        self.mock_redirect = self.p_redirect.start()

    def tearDown(self):
        patch.stopall()

    def test_get_add_report(self):
        form_instance = MagicMock()
        self.mock_form_class.return_value = form_instance

        request = self.factory.get('/add/')
        add_session_to_request(request)
        add_messages_to_request(request)

        self.view(request)
        self.mock_render.assert_called_once_with(
            request, 'add_report.html', {'form': form_instance}
        )

    def test_post_invalid_form(self):
        form = MagicMock(is_valid=MagicMock(return_value=False))
        self.mock_form_class.return_value = form

        request = self.factory.post('/add/', {'foo': 'bar'})
        add_session_to_request(request)
        add_messages_to_request(request)

        self.view(request)
        self.mock_render.assert_called_once_with(
            request,
            'add_report.html',
            {'form': form, 'error': 'Form is invalid'}
        )

    def test_post_form_save_exception(self):
        form = MagicMock(is_valid=MagicMock(return_value=True))
        form.save.side_effect = Exception('oops')
        self.mock_form_class.return_value = form

        request = self.factory.post('/add/', {})
        add_session_to_request(request)
        add_messages_to_request(request)

        self.view(request)
        self.mock_render.assert_called_once_with(
            request,
            'add_report.html',
            {'form': form, 'error': 'Error saving the report'}
        )

    def test_post_firebase_error(self):
        form = MagicMock(is_valid=MagicMock(return_value=True))
        saved_report = MagicMock()
        form.save.return_value = saved_report
        form.cleaned_data = {
            'title':'t','description':'d','place':'loc',
            'latitude':1.0,'longitude':2.0,'type':'ty'
        }
        self.mock_form_class.return_value = form
        self.mock_save.side_effect = Exception('fb fail')

        request = self.factory.post('/add/', {})
        add_session_to_request(request)
        add_messages_to_request(request)

        self.view(request)
        self.mock_render.assert_called_once_with(
            request,
            'add_report.html',
            {'form': form, 'error': 'Error saving to Firebase'}
        )

    def test_post_success_no_image(self):
        form = MagicMock(is_valid=MagicMock(return_value=True))
        saved_report = MagicMock()
        form.save.return_value = saved_report
        form.cleaned_data = {
            'title':'t','description':'d','place':'loc',
            'latitude':1.0,'longitude':2.0,'type':'ty'
        }
        self.mock_form_class.return_value = form
        self.mock_save.return_value = 'RID123'

        request = self.factory.post('/add/', {})
        add_session_to_request(request)
        add_messages_to_request(request)

        self.view(request)
        self.assertEqual(saved_report.firebase_id, 'RID123')
        saved_report.save.assert_called_once()
        self.mock_redirect.assert_called_once_with(
            'report_confirmation', report_id='RID123'
        )


@override_settings(
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    MESSAGE_STORAGE='django.contrib.messages.storage.fallback.FallbackStorage'
)
class ReportConfirmationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.report_confirmation

        self.p_get = patch('reports.views.get_report_by_id')
        self.mock_get = self.p_get.start()

        self.p_render = patch('reports.views.render')
        self.mock_render = self.p_render.start()

        self.p_redirect = patch('reports.views.redirect')
        self.mock_redirect = self.p_redirect.start()

    def tearDown(self):
        patch.stopall()

    def test_confirmation_not_found(self):
        self.mock_get.return_value = None
        request = self.factory.get('/confirm/FOO/')
        self.view(request, 'FOO')
        self.mock_redirect.assert_called_once_with('report_list')

    def test_confirmation_found(self):
        rpt = {'a': 1}
        self.mock_get.return_value = rpt
        request = self.factory.get('/confirm/123/')
        self.view(request, '123')
        self.mock_render.assert_called_once_with(
            request, 'confirmation.html', {'report': rpt}
        )


@override_settings(
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    MESSAGE_STORAGE='django.contrib.messages.storage.fallback.FallbackStorage'
)
class ReportDetailTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.report_detail

        self.p_get = patch('reports.views.get_report_by_id')
        self.mock_get = self.p_get.start()

        self.p_init = patch('reports.views.initialize_firebase')
        self.mock_init = self.p_init.start()
        self.mock_db = MagicMock()
        self.mock_init.return_value = self.mock_db

        self.p_render = patch('reports.views.render')
        self.mock_render = self.p_render.start()

        self.p_redirect = patch('reports.views.redirect')
        self.mock_redirect = self.p_redirect.start()

    def tearDown(self):
        patch.stopall()

    def test_detail_not_found(self):
        self.mock_get.return_value = None
        request = self.factory.get('/detail/XYZ/')
        self.view(request, 'XYZ')
        self.mock_redirect.assert_called_once_with('report_list')

    def test_upvote(self):
        rpt = {'upvotes': 5}
        self.mock_get.return_value = rpt
        request = self.factory.post('/detail/1/', {'action': 'upvote'})
        request.user = AnonymousUser()
        self.view(request, '1')
        self.mock_db.collection().document('1').update.assert_called_once_with({'upvotes': 6})
        self.mock_render.assert_called_once_with(request, 'report_detail.html', {'report': rpt})

    def test_add_comment(self):
        rpt = {'comments': []}
        self.mock_get.return_value = rpt
        request = self.factory.post('/detail/1/', {'action': 'add_comment', 'comment': 'hi'})
        request.user = AnonymousUser()
        self.view(request, '1')
        self.assertEqual(len(rpt['comments']), 1)
        self.mock_db.collection().document('1').update.assert_called_once()
        self.mock_render.assert_called_once_with(request, 'report_detail.html', {'report': rpt})


@override_settings(
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    MESSAGE_STORAGE='django.contrib.messages.storage.fallback.FallbackStorage'
)
class ReportListTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = getattr(views.report_list, '__wrapped__', views.report_list)

        self.p_get = patch('reports.views.get_reports_from_firebase')
        self.mock_get = self.p_get.start()

        self.p_render = patch('reports.views.render')
        self.mock_render = self.p_render.start()

    def tearDown(self):
        patch.stopall()



@override_settings(
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    MESSAGE_STORAGE='django.contrib.messages.storage.fallback.FallbackStorage'
)
class MapViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views.map_view

        self.p_get = patch('reports.views.get_reports_from_firebase')
        self.mock_get = self.p_get.start()

        self.p_render = patch('reports.views.render')
        self.mock_render = self.p_render.start()

    def tearDown(self):
        patch.stopall()

    def test_map(self):
        self.mock_get.return_value = [{'id': '1'}]
        request = self.factory.get('/map/')
        self.view(request)
        self.mock_render.assert_called_once_with(request, 'map.html', {'reports': [{'id': '1'}]})


@override_settings(
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    MESSAGE_STORAGE='django.contrib.messages.storage.fallback.FallbackStorage'
)
class AdminDashboardTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = getattr(views.admin_dashboard, '__wrapped__', views.admin_dashboard)

        self.p_get = patch('reports.views.get_reports_from_firebase')
        self.mock_get = self.p_get.start()

        self.p_render = patch('reports.views.render')
        self.mock_render = self.p_render.start()

    def tearDown(self):
        patch.stopall()

    def test_admin_dashboard(self):
        self.mock_get.return_value = ['r1', 'r2']
        request = self.factory.get('/admin/')
        add_session_to_request(request)
        add_messages_to_request(request)
        request.session['user_role'] = 'admin'

        self.view(request)
        self.mock_render.assert_called_once_with(
            request, 'admin_dashboard.html', {'reports': ['r1', 'r2']}
        )
