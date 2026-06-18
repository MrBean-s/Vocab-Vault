from django.db import models



class Language(models.Model):
	name = models.CharField(max_length = 200)
	image = models.OneToOneField('Image', on_delete = models.SET_NULL, null = True)


class Word(models.Model):
	name = models.CharField(max_length = 200)
	added_at = models.DateTimeField(auto_now_add = True)

	language = models.ForeignKey(Language, on_delete = models.PROTECT)

	class Meta:
		unique_together = ('name', 'language')


class Definition(models.Model):
	description = models.TextField()
	origin = models.TextField(default = '')

	word = models.ForeignKey(Word, on_delete = models.CASCADE, null = False)
	image = models.OneToOneField('Image', on_delete = models.SET_NULL, null = True)
	country_tags = models.ManyToManyField('Country', related_name = 'definitions')

	class ForgettingFrequency(models.TextChoices):
		FREQUENT = 'FRQ', 'FREQUENT'
		RARE = 'RAR', 'RARE'
		NEVER = 'NVR', 'NEVER'

	forgetting_frequency = models.CharField(
		max_length = 3,
		choices = ForgettingFrequency.choices,
		null = True,
		blank = True
	)


class Example(models.Model):
	description = models.TextField()
	explanation = models.TextField()
	custom_audio = models.FileField(upload_to = 'audio/')
	added_at = models.DateTimeField(auto_now_add = True)
	part_of_speech = models.ForeignKey('PartOfSpeech', on_delete = models.PROTECT, null = True)
	
	definition = models.ForeignKey(Definition, on_delete = models.CASCADE, null = False)
	source = models.ForeignKey('Source', on_delete = models.PROTECT)


class Source(models.Model):
	name = models.TextField()
	short_name  = models.CharField(max_length = 10)
	image = models.OneToOneField('Image', on_delete = models.SET_NULL, null = True)


class QuizAttempt(models.Model):
	correct = models.BooleanField(default = False)
	attempted_at = models.DateTimeField(auto_now_add=True)
	deck = models.ForeignKey('Deck', on_delete = models.SET_NULL, null = True)

	definition = models.ForeignKey(Definition, on_delete = models.CASCADE, null = False)


class Deck(models.Model):
	name = models.CharField(max_length = 50)
	description = models.TextField()
	image = models.OneToOneField('Image', on_delete = models.SET_NULL, null = True)

	questions = models.ManyToManyField(Definition)


class Image(models.Model):
	file = models.ImageField(upload_to = 'images/')


class PartOfSpeech(models.Model):
	name = models.CharField(max_length = 50, null = False)
	language = models.ForeignKey(Language, on_delete = models.CASCADE)

	class Meta:
		unique_together = ('name', 'language')


class Country(models.Model):
	name = models.CharField(max_length = 60)
	iso_code = models.CharField(max_length = 5, unique = True)

	def __str__(self):
		return self.name