from django import forms
from .models import *
from django.forms import inlineformset_factory, modelformset_factory
from django.forms.models import BaseInlineFormSet

class LanguageForm(forms.ModelForm):
   image_file = forms.ImageField(
      required=False,
      widget=forms.FileInput(attrs={'class': 'form-control'})
   )

   countries = forms.ModelMultipleChoiceField(
      queryset=Country.objects.all().order_by('name'),
      widget=forms.SelectMultiple(attrs={'class': 'select2'}),
      required=False
   )

   class Meta:
      model = Language
      fields = ['name']
      widgets = {
         'name': forms.TextInput(attrs={'class': 'form-control'}),
      }

   def clean(self):
      cleaned_data = super().clean()
      countries = cleaned_data.get('countries')

      if self.instance.pk:
         existing_ids = set(
            CountryLanguage.objects.filter(language=self.instance)
            .values_list('country_id', flat=True)
         )
         submitted_ids = {country.id for country in countries}
         self.new_country_ids = submitted_ids - existing_ids
         self.remove_country_ids = existing_ids - submitted_ids

      return cleaned_data

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

      if hasattr(self, 'new_country_ids'):
         for cty_id in self.new_country_ids:
            CountryLanguage.objects.create(language_id=language.id, country_id=cty_id)
      
      if hasattr(self, 'remove_country_ids') and self.remove_country_ids:
         CountryLanguage.objects.filter(
            language_id=language.id,
            country_id__in=self.remove_country_ids
         ).delete()

      return language

class CountryForm(forms.ModelForm):
   name = forms.CharField(
      required=False,
      widget=forms.TextInput(attrs={
         'class': 'form-control',
         'placeholder': 'Country name',
         'manual-required': 'true'
      })
   )
   iso_code = forms.CharField(
      required=False,
      widget=forms.TextInput(attrs={
         'class': 'form-control',
         'placeholder': 'e.g. US, UK, AU',
         'manual-required': 'true'
      })
   )
   
   class Meta:
      model = Country
      fields = ['name', 'iso_code']
      labels = { 'name': 'Country name'}
   
   def clean(self):
      cleaned_data = super().clean()
      if cleaned_data.get('DELETE'):
         return cleaned_data
      name = cleaned_data.get('name')
      iso_code = cleaned_data.get('iso_code')

      if Country.objects.filter(name=name).exists():
         self.add_error('name', "This Country Name already exists.")
      if Country.objects.filter(iso_code=iso_code).exists():
         self.add_error('iso_code', "This ISO code already exists.")
      if name and iso_code:
         if Country.objects.filter(name=name, iso_code=iso_code).exists():
            raise forms.ValidationError("This country with this ISO code already exists.")

      return cleaned_data


class WordForm(forms.ModelForm):
   class Meta:
      model = Word
      fields = ['name']
      labels = { 'name': 'Word or phrase name'}
      widgets = {
         'name': forms.TextInput(attrs={
            'class': 'form-control banner-input field-important underline-important',
            'placeholder': 'Word name'
         }),
      }

class DefinitionForm(forms.ModelForm):
   image_file = forms.ImageField(
      required=False,
      widget=forms.FileInput(attrs={'class': 'form-control img-input',})
   )

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
               'rows': 3, 
               'cols': 50, 
               'class': 'form-control resize-none field-description',
               'manual-required': 'true'
            }
         ),
         'origin': forms.Textarea(
            attrs={
               'rows': 2, 
               'cols': 50, 
               'class': 'form-control resize-none field-description',
            }
         ),
         'image_file': forms.FileInput(
            attrs={
               'class': 'form-control p-5'
            }
         )
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
               'rows': 2,
               'cols': 50, 
               'class': 'form-control resize-none field-quote',
               'placeholder': 'Write an example',
               'manual-required': 'true'
            }
         ),
         'explanation': forms.Textarea(
            attrs={
               'rows': 2, 
               'cols': 50, 
               'class': 'form-control resize-none field-explanation',
               'placeholder': 'Explained in other words'
            }
         ),
      }

class SkipEmptyDeletedInlineFormSet(BaseInlineFormSet):
   def clean(self):
      super().clean()
      for form in self.forms:
         if self._should_delete_form(form):
            # Discard all field errors – this row is going to be deleted
            form._errors = {}

DefinitionFormSet = inlineformset_factory(
   Word, Definition,
   form=DefinitionForm,
   formset=SkipEmptyDeletedInlineFormSet,
   extra=1,
   can_delete=True
)

ExampleFormSet = inlineformset_factory(
   Definition, Example,
   form=ExampleForm,
   formset=SkipEmptyDeletedInlineFormSet,
   extra=1,
   can_delete=True
)

class ModalSearchForm(forms.Form):

   SEARCH_FILTER = [
      ('word', 'Words'),
      ('definition', 'Definitions'),
      ('example', 'Examples'),
   ]

   query = forms.CharField(
      max_length=100,
      required=True,
      widget=forms.TextInput(attrs={
         'class': 'form-control',
         'placeholder': 'Search...'
      })
   )

   filter = forms.MultipleChoiceField(
      choices=SEARCH_FILTER,
      widget=forms.CheckboxSelectMultiple(attrs={}),
      required=False,
   )

   limit = forms.IntegerField(
      min_value=1,
      max_value=30,
      initial=5,
      required=False,
      widget=forms.NumberInput(attrs={'class': 'form-control'})
   )

   newest_first = forms.BooleanField(
      required=False,
      initial=True,
      widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'})
   )

   def clean(self):
      cleaned_data = super().clean()

      filter = cleaned_data.get('filter')
      if not filter:
         raise forms.ValidationError("At least one filter is required.")

      return cleaned_data

