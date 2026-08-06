from django.urls import path

from . import views

urlpatterns = [
   path("", views.start_screen, name="start_screen"),
   path("lang/<int:lang_id>/dashboard/", views.dashboard, name="dashboard"),
   path("lang/form/", views.language_form, name="lang_modal_form"),
   path("lang/<int:lang_id>/edit/", views.language_form, name="lang_edit_form"),
   path("lang/<int:lang_id>/delete/", views.delete_language, name="lang_delete"),
   path("lang/add-to-set/", views.add_lang_to_set, name="lang_add_set"),
   path("lang/<int:lang_id>/add-to-set/", views.add_lang_to_set_with_id, name="lang_add_set_with_id"),
   path("lang/<int:lang_id>/remove-from-set/", views.remove_lang_from_set, name="lang_remove_set"),
   path("lang/<int:lang_id>/get-sources/", views.get_sources, name="get_sources"),
   path("languages/", views.languages, name="languages"),

   path("generic/confirm-delete/", views.generic_confirm_delete, name="generic_confirm_delete"),

   path("lang/<int:lang_id>/word/", views.word, name="add_word"),
   path("lang/<int:lang_id>/word/<int:word_id>/edit/", views.word, name="word_edit"),
   path("lang/<int:lang_id>/word/<int:word_id>/", views.word_details, name="word_details"),
   path("lang/<int:lang_id>/word/<int:word_id>/link/", views.link_word, name="link_word"),
   path("lang/<int:lang_id>/word/<int:word_id>/delete/", views.word_delete, name="word_delete"),
   path("lang/<int:lang_id>/word/<int:word_id>/link-edit/<int:rel_word_id>", views.link_word_edit, name="link_word_edit"),
   path("lang/<int:lang_id>/word/<int:word_id>/relation/<int:rel_word_id>/unlink/", views.unlink_word, name="unlink_word"),
   path("lang/<int:lang_id>/words/", views.word_list, name="word_list"),
   
   path("lang/<int:lang_id>/import/", views.import_words_from_old_json, name="import"),
   path("lang/<int:lang_id>/search/", views.search, name="search"),
   path("lang/<int:lang_id>/search_word/", views.word_only_search, name="search_word"),
   path("search/definitions/", views.get_definitions, name="get_definitions"),
   path("source/<int:source_id>/search_episodes_or_segments/", views.search_episodes_or_segments, name="search_episodes_or_segments"),

   path("countries/", views.countries, name="countries"),
   path("country/<int:cty_id>/delete/", views.delete_country, name="country_delete"),

   path("image/<int:img_id>/", views.show_image, name="show_image"),

   path("lang/<int:lang_id>/sources/", views.sources, name="sources"),
   path("lang/<int:lang_id>/search_source/", views.search_source, name="search_source"),
   path("lang/<int:lang_id>/source/add/", views.sources_add_edit, name="source_add"),
   path("lang/<int:lang_id>/source/<int:source_id>/edit/", views.sources_add_edit, name="source_edit"), 
   path("lang/<int:lang_id>/source/<int:source_id>/delete/", views.source_delete, name="source_delete"),
   # path("lang/<int:lang_id>/source/<int:source_id>/", views.sources_add_edit, name="source_add"), #???

   path("lang/<int:lang_id>/source/<int:source_id>/episodes/", views.episodes, name="episodes"),
   path("source/<int:source_id>/episode/add/", views.episode_add_edit, name="episode_add"),
   path("source/<int:source_id>/episode/<int:episode_id>/edit/ ", views.episode_add_edit, name="episode_edit"),
   path("source/<int:source_id>/episode/<int:episode_id>/delete/", views.episode_delete, name="episode_delete"),
   path("lang/<int:lang_id>/source/<int:source_id>/play-session/", views.play_session, name="play_session_source"),
   path("lang/<int:lang_id>/episode/<int:episode_id>/play-session/", views.play_session, name="play_session_episode"),

   path("lang/<int:lang_id>/sources/<int:source_id>/segments/", views.segments, name="segments"),
   path("sources/<int:source_id>/segment/add/", views.segment_add_edit, name="segment_add"),
   path("sources/<int:source_id>/segment/<int:segment_id>/edit/", views.segment_add_edit, name="segment_edit"),
   path("sources/<int:source_id>/segment/<int:segment_id>/delete/", views.segment_delete, name="segment_delete"),
   path("lang/<int:lang_id>/segment/<int:segment_id>/play-session/", views.play_session, name="play_session_segment"),

   path("lang/<int:lang_id>/example/<int:example_id>/cite/", views.example_cite, name="example_cite"),
   path("lang/<int:lang_id>/citation/<int:citation_id>/remove/", views.citation_delete, name="citation_delete"),

   path("lang/<int:lang_id>/source/<int:source_id>/session/cite/", views.play_session_cite,   name="session_source_cite"),
   path("lang/<int:lang_id>/episode/<int:episode_id>/session/cite/", views.play_session_cite, name="session_episode_cite"),
   path("lang/<int:lang_id>/segment/<int:segment_id>/session/cite/", views.play_session_cite, name="session_segment_cite"),

   path("lang/<int:lang_id>/source/<int:source_id>/session/citation/<int:citation_id>/edit/", views.play_session_cite,  name="session_source_cite_edit"),
   path("lang/<int:lang_id>/episode/<int:episode_id>/session/citation/<int:citation_id>/edit/", views.play_session_cite, name="session_episode_cite_edit"),
   path("lang/<int:lang_id>/segment/<int:segment_id>/session/citation/<int:citation_id>/edit/", views.play_session_cite, name="session_segment_cite_edit"),

]