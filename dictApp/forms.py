from django import forms
from .models import Language, Image

class LanguageForm(forms.ModelForm):
	image_file = forms.ImageField(
		required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

	class Meta:
		model = Language
		fields = ['name']
		widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image_file': forms.FileInput(attrs={'class': 'form-control'})
        }


	def save(self, commit=True):
		language = super().save(commit=False)
		image_file = self.cleaned_data.get('image_file')

		if image_file:
			old_img = language.image
			if language.pk and old_img:
				storage = old_img.file.storage
				if storage.exists(old_img.file.name):
					storage.delete(old_img.file.name)
				old_img.delete()

			new_img = Image.objects.create(file=image_file)
			language.image = new_img

		language.save() #can't use if commmit = False cause that'd leave an orphan img

		return language