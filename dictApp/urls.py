from django.urls import path

from . import views

urlpatterns = [
	path("", views.start_screen, name="start_screen"),
	path("lang/<int:lang_id>/dashboard/", views.dashboard, name="dashboard"),
	path("lang/form", views.language_form, name="lang_modal_form"),
	path("lang/<int:lang_id>/edit/", views.language_form, name="lang_edit_form"),
	path("lang/<int:lang_id>/delete/", views.delete_language, name="lang_delete"),
	path("languages", views.languages, name="languages"),
	path("generic/confirm-delete/", views.generic_confirm_delete, name="generic_confirm_delete"),
]