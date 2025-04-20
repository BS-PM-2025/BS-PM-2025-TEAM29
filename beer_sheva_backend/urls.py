from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

from beer_sheva_backend.firebase import initialize_firebase
from reports import views

initialize_firebase()


urlpatterns = [

]
