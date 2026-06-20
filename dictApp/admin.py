from django.contrib import admin
from .models import Language, Word, Definition, Example, Source, QuizAttempt, Deck, Image, PartOfSpeech, Country

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