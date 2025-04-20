from django.shortcuts import render
from firebase_admin import firestore
from beer_sheva_backend.firebase import initialize_firebase, get_reports_from_firebase
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Report
from .serializers import ReportSerializer
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .forms import ReportForm, type_dict
from django.shortcuts import render, redirect
from .forms import ReportForm
from beer_sheva_backend.firebase import save_report_to_firebase

import logging


logger = logging.getLogger(__name__)

