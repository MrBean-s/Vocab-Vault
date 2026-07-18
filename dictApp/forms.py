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
      widget=forms.SelectMultiple(attrs={'class': 'select2', 'data-placeholder': 'Select a country'}),
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
      else:
         existing_ids = set()

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

   def save(self, commit=True):
      definition = super().save(commit=False)
      image_file = self.cleaned_data.get('image_file')
      
      if image_file:
         old_img = definition.image

         if definition.pk and old_img:
            storage = old_img.file.storage
            if storage.exists(old_img.file.name):
               storage.delete(old_img.file.name)
            old_img.delete()

         new_img = Image.objects.create(file=image_file)
         definition.image = new_img

      if commit:
         definition.save()

      return definition


class ExampleForm(forms.ModelForm):
   part_of_speech = forms.ModelChoiceField(
      queryset=PartOfSpeech.objects.none(),
      widget=forms.Select(attrs={
         'class': 'select2',
         'data-allow-open': 'true',
         'data-placeholder': 'Category',
         'data-width': '45%',
         'data-remove-search': 'true'
      }),
      required=False,
   )
   class Meta:
      model = Example
      fields = ['description', 'explanation', 'part_of_speech']
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
   def __init__(self, *args, **kwargs):
      lang = kwargs.pop('language', None)
      is_last = kwargs.pop('is_last', False)
      super().__init__(*args, **kwargs)
      if lang:
         self.fields['part_of_speech'].queryset = PartOfSpeech.objects.filter(language=lang)
         self.fields['part_of_speech'].widget.attrs.update({
            'backend-rendered': 'false' if is_last else 'true',
            'data-select2-width': '45%',
         })

class SkipEmptyDeletedInlineFormSet(BaseInlineFormSet):
   def clean(self):
      super().clean()
      for form in self.forms:
         if self._should_delete_form(form):
            # Discard all field errors – this row is going to be deleted
            form._errors = {}

class BaseExampleFormSet(SkipEmptyDeletedInlineFormSet):
   def __init__(self, *args, language=None, **kwargs):
      self.language = language
      super().__init__(*args, **kwargs)

   def get_form_kwargs(self, index):
      kwargs = super().get_form_kwargs(index)
      kwargs['language'] = self.language
      kwargs['is_last'] = (index == self.total_form_count() - 1)
      return kwargs

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
   formset=BaseExampleFormSet,
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

class LanguageAddSetForm(forms.Form):
   language=forms.ModelChoiceField(
      widget=forms.Select(attrs={'class': 'select2'}),
      empty_label="Search for a language",
      queryset=Language.objects.all().order_by('name')
   )


class LinkWordForm(forms.Form):
   word_1_id = forms.IntegerField(
      min_value=1,
      required=True,
      widget=forms.NumberInput(attrs={
         'class': 'd-hidden',
      })
   )

   word_2=forms.ModelChoiceField(
      label="Related word",
      widget=forms.Select(attrs={
         'class': 'select2 select2-ajax',
         'data-is-ajax': 'true',
         'data-width': "100%",
         'data-placeholder': "Search for a word"
      }),
      queryset=Word.objects.none()
   )

   relation_type = forms.ChoiceField(
      choices=WordRelation.RelationType.choices,
      required=False,
      widget=forms.Select(attrs={'class': 'form-control'})
   )

   category = forms.ChoiceField(
      choices=WordRelation.TopicCategory.choices,
      required=False,
      widget=forms.Select(attrs={'class': 'form-control'})
   )

   def clean(self):
      cleaned_data = super().clean()
      word_1_id = cleaned_data.get('word_1_id')
      selected_word = cleaned_data.get('word_2')
      if word_1_id and selected_word:
         if word_1_id == selected_word.pk:
            raise forms.ValidationError("A word cannot be linked to itself.")

         if WordRelation.objects.filter(word_1_id=word_1_id, word_2=selected_word).exists():
            raise forms.ValidationError(f"This word is already linked to {selected_word.name}")

      return cleaned_data

   def __init__(self, *args, **kwargs):
      ajax_url = kwargs.pop('ajax_url', None)
      super().__init__(*args, **kwargs)

      widget = self.fields['word_2'].widget
      
      if ajax_url is not None:
         widget.attrs['data-ajax-url'] = ajax_url

      if self.is_bound and 'word_2' in self.data:
         submitted_id = self.data.get('word_2')
         if submitted_id:
            self.fields['word_2'].queryset = Word.objects.filter(pk=submitted_id)

class RelationTypeForm(forms.Form):
   relation_type = forms.ChoiceField(
      choices=WordRelation.RelationType.choices,
      required=False,
      widget=forms.Select(attrs={'class': 'form-control'})
   )

class SourceForm(forms.ModelForm):
   image_file = forms.ImageField(
      required=False,
      widget=forms.FileInput(attrs={'class': 'form-control img-input',})
   )

   source_category = forms.ChoiceField(
      choices=Source.SourceCategory.choices,
      required=True,
      initial="OTH",
      widget=forms.Select(attrs={'class': 'form-select'}),
      label="Category"
   )

   class Meta:
      model = Source
      fields = ["released_year", "name", "short_name", "author", "source_category"]
      widgets = {
         'name': forms.TextInput(attrs={'class': 'form-control'}),
         'released_year': forms.TextInput(attrs={'class': 'form-control'}),
         'short_name': forms.TextInput(attrs={'class': 'form-control'}),
         'author': forms.TextInput(attrs={'class': 'form-control'}),
      }
      labels = {'name': 'Source name'}

   def clean(self):
      cleaned_data = super().clean()
      name = cleaned_data.get('name')
      short_name = cleaned_data.get('short_name')
      if name and short_name:
         qs = Source.objects.filter(Q(name__iexact=name) | Q(short_name__iexact=short_name))

         if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
         
         if qs.exists():
            raise forms.ValidationError("A show with that name or short_name already exist")
      
      return cleaned_data
   
   def save(self, commit=True):
      source = super().save(commit=False)
      image_file = self.cleaned_data.get('image_file')
      
      if image_file:
         old_img = source.image

         if source.pk and old_img:
            storage = old_img.file.storage
            if storage.exists(old_img.file.name):
               storage.delete(old_img.file.name)
            old_img.delete()

         new_img = Image.objects.create(file=image_file)
         source.image = new_img

      if commit:
         source.save()
      
      return source


class EpisodeForm(forms.ModelForm):

   class Meta:
      model=Episode
      fields=['season_number', 'episode_number', 'name']
      widgets = {
         'season_number': forms.NumberInput(attrs={'class': 'form-control'}),
         'episode_number': forms.NumberInput(attrs={'class': 'form-control'}),
         'name': forms.TextInput(attrs={'class': 'form-control'}),
      }
      labels = { 'name': 'Episode name'}

   def clean(self):
      cleaned_data = super().clean()

      season_number = cleaned_data.get('season_number')
      episode_number = cleaned_data.get('episode_number')
      
      source = self.instance.source

      existing = Episode.objects.filter(
         source=source,
         season_number=season_number,
         episode_number=episode_number
      )

      if self.instance.pk:
         existing = existing.exclude(pk=self.instance.pk)

      if existing.exists():
         raise forms.ValidationError(f"Episode {episode_number} already exist in season {season_number}")

      return cleaned_data
      
