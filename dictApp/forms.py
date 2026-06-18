from django import forms
from .models import Language, Image

class LanguageForm(forms.ModelForm):
	image_file = forms.ImageField()

	class Meta:
		model = Language
		fields = ['name']


	def save(self, commit=True):
		language = super().save(commit=False)
		image_file = self.cleaned_data.get('image_file')

		if image_file:
			if language.pk and language.image:
				language.image.delete()

			img = Image.objects.create(file=image_file)
			language.image = img

		language.save() #can't use if commmit = False cause that'd leave an orphan img

		return language