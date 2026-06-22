from django import forms
from .models import Language, Image, Word, Definition, Example
from django.forms import inlineformset_factory

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

class WordForm(forms.ModelForm):
	class Meta:
		model = Word
		fields = ['name']
		labels = { 'name': 'Word or phrase name'}
		widgets = {
			'name': forms.TextInput(attrs={
					'class': 'form-control banner-input',
					'placeholder': 'Word name'
				}),
			
		}

class DefinitionForm(forms.ModelForm):
	image_file = forms.ImageField(required=False)

	class Meta:
		model = Definition
		fields = ['description', 'origin']
		labels = {
            'description': 'Defintion',
            'origin': 'Definition origin'
        }
		widgets = {
            'description': forms.Textarea(
		        attrs={
		            'rows': 2, 
		            'cols': 50, 
		            'class': 'form-control resize-none',
		        }
		    ),
            'origin': forms.Textarea(
		        attrs={
		            'rows': 2, 
		            'cols': 50, 
		            'class': 'form-control resize-none',
		        }
		    ),
            'image_file': forms.FileInput(attrs={'class': 'form-control'})
        }

	

class ExampleForm(forms.ModelForm):
	class Meta:
		model = Example
		fields = ['description', 'explanation', 'custom_audio', 'part_of_speech']
		labels = {
			'description': 'Example ',
			'explanation': 'In other words / Explanation'
		}
		widgets = {
			'description': forms.Textarea(
		        attrs={
		            'rows': 1, 
		            'cols': 50, 
		            'class': 'form-control resize-none',
		            'placeholder': 'Write an example'
		        }
		    ),
		    'explanation': forms.Textarea(
		        attrs={
		            'rows': 1, 
		            'cols': 50, 
		            'class': 'form-control resize-none',
		            'placeholder': 'Explained in other words'
		        }
		    ),
		}

DefinitionFormSet = inlineformset_factory(
	Word, Definition,
	form=DefinitionForm,
	extra=1,
	can_delete=True
)

ExampleFormSet = inlineformset_factory(
	Definition, Example,
	form=ExampleForm,
	extra=1,
	can_delete=True
)