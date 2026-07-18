from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Language)
admin.site.register(Word)
admin.site.register(Definition)
admin.site.register(Example)
admin.site.register(Source)
admin.site.register(QuizAttempt)
admin.site.register(Deck)
admin.site.register(Image)
admin.site.register(PartOfSpeech)
admin.site.register(Country)
admin.site.register(CountryLanguage)
admin.site.register(WordRelation)
admin.site.register(Episode)