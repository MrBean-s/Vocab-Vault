from django.apps import AppConfig
from django.db.models.signals import post_migrate

class DictappConfig(AppConfig):
   default_auto_field = 'django.db.models.BigAutoField'
   name = 'dictApp'
   def ready(self):
      from .signals import seed_countries, seed_lang_and_parts_of_speech
      #runs after migrations are applied
      post_migrate.connect(seed_countries, sender=self)
      post_migrate.connect(seed_lang_and_parts_of_speech, sender=self)

      from . import signals

