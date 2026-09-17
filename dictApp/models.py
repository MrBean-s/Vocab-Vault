from django.db import models
from django.db.models import Q
import json


class Language(models.Model):
   name = models.CharField(max_length=200)
   image = models.OneToOneField('Image', on_delete=models.SET_NULL, null=True)
   in_user_set = models.BooleanField(default=False)
   added_manually = models.BooleanField(default=False)
   iso_code = models.CharField(max_length=2, blank=True)

   def __str__(self):
      return self.name


class Word(models.Model):
   name = models.CharField(max_length=200)
   added_at = models.DateTimeField(auto_now_add=True)
   is_idiom = models.BooleanField(default=False)
   is_draft = models.BooleanField(default=False)

   language = models.ForeignKey(Language, on_delete=models.PROTECT)
   related_words = models.ManyToManyField(
      'Word',
      through='WordRelation',
      through_fields=('word_1', 'word_2'),
      symmetrical=False,
      related_name='+',
      blank=True
   )

   class Meta:
      unique_together = ('name', 'language')
   
   def delete(self, *args, **kwargs):
      for definition in self.definitions.all():
         definition.delete() #to fire definition post_delete signals (chain: defintion > example > citation)
      super().delete(*args, **kwargs)

   def __str__(self):
      return self.name



class Definition(models.Model):
   description = models.TextField(null=True, blank=True, db_index=True)
   origin = models.TextField(default = '', null=True, blank=True)

   word = models.ForeignKey(Word, related_name="definitions", on_delete=models.CASCADE, null=False)
   image = models.OneToOneField('Image', on_delete=models.SET_NULL, null=True, blank=True)
   country_tags = models.ManyToManyField('Country', related_name='definitions', blank=True)

   class ForgettingFrequency(models.TextChoices):
      FREQUENT = 'FRQ', 'FREQUENT'
      RARE = 'RAR', 'RARE'
      NEVER = 'NVR', 'NEVER'

   class TopicCategory(models.TextChoices):
      SPORTS         = 'SPT', 'Sports'
      MONEY          = 'MNY', 'Money & Finance'
      MEDICINE       = 'MED', 'Medicine & Health'
      FOOD           = 'FOD', 'Food & Cooking'
      TECHNOLOGY     = 'TEC', 'Technology'
      SCIENCE        = 'SCI', 'Science'
      ART            = 'ART', 'Art & Literature'
      MUSIC          = 'MUS', 'Music'
      POLITICS       = 'POL', 'Politics & Government'
      LAW            = 'LAW', 'Law & Legal'
      RELIGION       = 'REL', 'Religion & Philosophy'
      EDUCATION      = 'EDU', 'Education'
      NATURE         = 'NAT', 'Nature & Animals'
      TRAVEL         = 'TRV', 'Travel & Geography'
      FASHION        = 'FAS', 'Fashion & Beauty'
      MILITARY       = 'MIL', 'Military & War'
      SLANG          = 'SLG', 'Slang & Informal'
      TABOO          = 'TAB', 'Taboo / Swear Words'
      WORK           = 'WRK', 'Work & Business'
      FAMILY         = 'FAM', 'Family & Relationships'
   
   forgetting_frequency = models.CharField(
      max_length=3,
      choices = ForgettingFrequency.choices,
      null=True,
      blank=True
   )

   topic_category = models.CharField(
      max_length=3,
      choices=TopicCategory.choices,
      null=True, blank=True,
      help_text='Topic domain of this relation'
   )

   class Status(models.TextChoices):
      PENDING = 'P', 'Pending'
      COMPLETE = 'C', 'Complete'

   status = models.CharField(
      max_length=1, 
      choices=Status.choices, 
      default=Status.PENDING,
      null=False,
      blank=True
   )

   def to_json(self, all_lang_countries_ids=None):
      data = {
         "id": self.id,
         "description": self.description,
         "origin": self.origin or "",
         "word_id": self.word.id if self.word else None,
         "image_id": self.image.id if self.image else None,
         "image_path": self.image.file.url if (self.image and self.image.file) else "",
         "forgetting_frequency": self.forgetting_frequency,
         "countries": [
            {"id": cty.id, "name": cty.name, "iso_code": cty.iso_code}
            for cty in self.country_tags.all()
         ],
         "all_countries": False,
         "examples": [ex.to_json() for ex in self.examples.all()],
         'topic_category': self.get_topic_category_display() or "",
      }
      if all_lang_countries_ids is not None:
         selected_ids = {c["id"] for c in data["countries"]}
         data["all_countries"] = True if selected_ids == all_lang_countries_ids else False
      return data

   def get_selected_countries_ids(self):
      selected_ids = { cty.id for cty in self.country_tags.all() }
      all_lang_countries_ids = {c.id for c in self.word.language.countries.all()}
      if selected_ids == all_lang_countries_ids:
         return ['-999']
      return list(selected_ids)

   def get_missing_fields(self):
      missing = []
      if not self.description:
         missing.append('description')
      # if not self.origin:
         # missing.append('origin')
      return missing

   def __str__(self):
      txt = self.word.language.name.upper() + " - " + self.description
      if len(txt) > 50:
         txt = txt[:50] + '...'
      return txt
   
   def delete(self, *args, **kwargs):
      for example in self.examples.all():
         example.delete()  #to fire example post_delete signals
      
      super().delete(*args, **kwargs)

class Example(models.Model):
   description = models.TextField()
   explanation = models.TextField(null=True, blank=True)
   created = models.DateTimeField(auto_now_add=True)

   class Status(models.TextChoices):
      PENDING = 'P', 'Pending'
      COMPLETE = 'C', 'Complete'

   status = models.CharField(
      max_length=1, 
      choices=Status.choices, 
      default=Status.PENDING,
      null=False,
      blank=True
   )

   part_of_speech = models.ForeignKey('PartOfSpeech', on_delete=models.PROTECT, null=True,
      blank=True)
   definition = models.ForeignKey(Definition, related_name="examples", on_delete=models.CASCADE,
      null=False)

   def to_json(self):
      citation = getattr(self, 'citation', None)

      return {
         "id": self.id,
         "description": self.description,
         "explanation": self.explanation or "",
         "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
         "part_of_speech": self.part_of_speech.name if self.part_of_speech else "",
         "citation": {
            "id": citation.id if citation else "",
            "source_id": citation.source_id if citation else "",
            "episode_id": citation.episode_id if citation else "",
            "segment_id": citation.segment_id if citation else "",
         } if citation else None
      }

   def __str__(self):
      return self.description

   def delete(self, *args, **kwargs):
      if hasattr(self, 'citation') and self.citation:
         self.citation.delete() #to fire citation post_delete signal
         
      super().delete(*args, **kwargs)

class Source(models.Model):
   released_year = models.IntegerField(null=True, blank=True)
   name = models.TextField()
   short_name  = models.CharField(max_length=10, null=True, blank=True)
   author = models.CharField(max_length=255, null=True, blank=True)

   class SourceCategory(models.TextChoices):
      MOVIE = 'MOV', 'Movie'
      TVSHOW = 'TVS', 'TV Show'
      SONG = 'SON', 'Song'
      ALBUM = 'ALB', 'Album'
      # GAME = 'GAM', 'GAME'
      BOOK = 'BOK', 'Book'
      ABOOK = 'ABK', 'Audio Book'
      PODCAST = 'POD', 'Podcast'
      # OTHER = 'OTH', 'OTHER'

      @classmethod
      def get_structure_type(cls, category):
         if category in {cls.TVSHOW}:
            return 'episodes'
         if category in {cls.ALBUM, cls.BOOK}:
            return 'segments'
         return 'none'

   source_category = models.CharField(
      max_length=3,
      choices = SourceCategory.choices,
      blank=False
   )

   image = models.OneToOneField('Image', on_delete=models.SET_NULL, null=True, blank=True)
   language = models.ForeignKey(Language, on_delete=models.PROTECT, null=False)

   REDIRECT_URLS = {
      'MOV': 'play_session_source',
      'SON': 'play_session_source',
      'ABK': 'play_session_source',
      'POD': 'play_session_source',
      'TVS': 'episodes',
      'ALB': 'segments',
      'BOK': 'segments'
   }

   def get_redirect_url(self, lang_id):
      url_name = self.REDIRECT_URLS[self.source_category]
      return reverse(url_name, kwargs={'lang_id': lang_id, 'source_id': self.id})

   def get_citation_count(self):
      return Citation.objects.filter(
         Q(source=self) |
         Q(episode__source=self) |
         Q(segment__source=self)
      ).distinct().count()

   @classmethod
   def get_category_map(cls):
      return {
         code: cls.SourceCategory.get_structure_type(code)
         for code, _ in cls.SourceCategory.choices
      }

   def get_structure_type(self):
      return self.SourceCategory.get_structure_type(self.source_category)

   def __str__(self):
      year_str = f" ({self.released_year})" if self.released_year else ''
      return f"{self.name}{year_str}"

class Episode(models.Model):
   season_number = models.IntegerField(null=True, blank=True)
   episode_number = models.IntegerField(null=False, blank=False)
   name = models.CharField(max_length=255)

   source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="episodes")

   class Meta:
      unique_together = ('source', 'season_number', 'episode_number')
   
   def __str__(self):
      if self.season_number and self.episode_number:
         return f'S{self.season_number}E{self.episode_number} - {self.name}'
      elif self.episode_number:
         return f'E{self.episode_number} - {self.name}'
      return self.name

class Segment(models.Model):
   class SegmentType(models.TextChoices):
      PROLOGUE = 'PRL', 'PROLOGUE'
      CHAPTER = 'CHP', 'CHAPTER'
      EPILOGUE = 'EPL', 'EPILOGUE'
      TRACK = 'TRK', 'TRACK'
      MISSION = 'MIS', 'MISSION'
      ACT = 'ACT', 'ACT'
   
   segment_type = models.CharField(
      max_length=3,
      choices=SegmentType.choices,
      blank=False,
      null=False
   )

   name = models.TextField(null=False, blank=False)
   number = models.IntegerField(null=False, blank=False)

   source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="segments")

   class Meta:
      unique_together = ('segment_type', 'name', 'number')

   def __str__(self):
      return f"{self.number}. {self.name}"

class Citation(models.Model):
   added_at = models.DateTimeField(auto_now_add=True)
   spotted_at = models.DurationField(null=True, blank=True)
   custom_audio = models.FileField(upload_to = 'audio/', null=True, blank=True)
   image = models.OneToOneField('Image', on_delete=models.SET_NULL, null=True)
   page = models.IntegerField(null=True, blank=True)

   example = models.OneToOneField(Example, on_delete=models.CASCADE, related_name="citation")
   source  = models.ForeignKey(Source,  null=True,  on_delete=models.PROTECT, related_name="citations")
   episode = models.ForeignKey(Episode, null=True,  on_delete=models.PROTECT, related_name="citations")
   segment = models.ForeignKey(Segment, null=True,  on_delete=models.PROTECT, related_name="citations")

   class Meta:
      constraints = [
      models.CheckConstraint(
         condition=Q(source__isnull=False) | Q(episode__isnull=False) | Q(segment__isnull=False),
         name='a_source_is_required'
      ) 
   ]


class QuizAttempt(models.Model):
   correct = models.BooleanField(default = False)
   attempted_at = models.DateTimeField(auto_now_add=True)
   deck = models.ForeignKey('Deck', on_delete=models.SET_NULL, null=True)

   definition = models.ForeignKey(Definition, on_delete=models.CASCADE, null=False)


class Deck(models.Model):
   name = models.CharField(max_length=50)
   description = models.TextField(null=True, blank=True)
   image = models.OneToOneField('Image', on_delete=models.SET_NULL, null=True)
   language = models.ForeignKey(Language, on_delete=models.PROTECT)

   questions = models.ManyToManyField( #only stores correct answers, use deck_questions instead
      Definition,
      through='DeckQuestion',
      related_name='decks_as_question'
   )


class DeckQuestion(models.Model):
   deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='deck_questions')
   definition = models.ForeignKey(Definition, on_delete=models.CASCADE)  # correct answer

   distractors = models.ManyToManyField(
      Word,
      related_name='distractor_in_deck_questions',
      blank=True
   )

   class Meta:
      unique_together = ('deck', 'definition')


class Image(models.Model):
   file = models.ImageField(upload_to = 'images/')


class PartOfSpeech(models.Model):
   name = models.CharField(max_length=50, null=False)
   language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='parts_of_speech')

   class Meta:
      unique_together = ('name', 'language')

   def __str__(self):
      return self.name


class Country(models.Model):
   name = models.CharField(max_length=60)
   iso_code = models.CharField(max_length=5, unique=True)
   added_manually = models.BooleanField(default=False)

   languages = models.ManyToManyField(Language, through='CountryLanguage', related_name='countries')
   

   def __str__(self):
      return self.name
   
   class Meta:
      constraints = [
         models.UniqueConstraint(fields=['name', 'iso_code'], name='unique_name_iso')
      ]

class CountryLanguage(models.Model):
   country = models.ForeignKey(Country, on_delete=models.CASCADE)
   language = models.ForeignKey(Language, on_delete=models.CASCADE)

   class Meta:
      unique_together = ('country', 'language')

class WordRelation(models.Model):
   word_1 = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='+')
   word_2 = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='+')

   class RelationType(models.TextChoices):
      SYNONYM = 'SYN', 'SIMILAR TO'
      ANTONYM = 'ANT', 'OPPOSITE TO'
      CONFUSED_WITH = 'CFW', 'CONFUSED WITH'
      HOMOPHONE = 'HPM', 'SOUND ALIKE'
      CATEGORY = 'CAT', 'SAME CATEGORY'

   relation_type = models.CharField(
      max_length=3,
      choices = RelationType.choices,
      null=False,
      blank=False
   )

   class Meta:
      unique_together = ('word_1', 'word_2')
   
   def __str__(self):
      return f"{self.word_1.name} - {self.word_2.name} - {self.relation_type}"
