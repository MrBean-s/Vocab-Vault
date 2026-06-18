from django.urls import path

from . import views

urlpatterns = [
	path("", views.start_screen, name="start_screen"),
	path("lang/<int:lang_id>/dashboard/", views.dashboard, name="dashboard"),
	path("lang/add/", views.language_form, name="add_lang"),
	path("lang/<int:lang_id>/edit/", views.language_form, name="add_lang"),
]