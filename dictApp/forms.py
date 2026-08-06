from django import forms
from .models import *
from django.forms import inlineformset_factory, modelformset_factory
from django.forms.models import BaseInlineFormSet
from django.urls import reverse

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
         'data-remove-search': 'true',
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
      widget=forms.Select(attrs={
         'class': 'select2',
      }),
      empty_label="Search for a language",
      queryset=Language.objects.filter(in_user_set=False).order_by('name')
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
         'data-placeholder': "Search for a word",
         'data-min-input-len': '3'
      }),
      queryset=Word.objects.none()
   )

   relation_type = forms.ChoiceField(
      choices=WordRelation.RelationType.choices,
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
      initial="TVS",
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
      

class CitationForm(forms.Form):
   
   spotted_at = forms.DurationField(
      label="Spotted at:",
      widget=forms.TextInput(attrs={
         'placeholder': 'HH:MM:SS',
         'class': 'form-control d-inline',
         'style': 'width: auto'
      }),
      required=True
   )

   word = forms.CharField(
      label="Word",
      widget=forms.Select(attrs={
         'class': 'select2 select2-ajax',
         'data-is-ajax': 'true',
         'data-width': '100%',
         'data-placeholder': 'Word',
         'data-tags': 'true',
         'data-min-input-len': '3',
      }),
      required=True
   )

   definition_input = forms.CharField(
      label='New Definition',
      widget=forms.Textarea(attrs={
         'rows': 2,
         'cols': 50,
         'class': 'form-control resize-none'
      }),
      required=False
   )

   definition_select = forms.CharField(
      label="Definition",
      widget=forms.Select(attrs={
         'class': 'form-select',
      }),
      required=False
   )

   example = forms.CharField(
      widget=forms.Textarea(attrs={
         'rows': 2,
         'cols': 50,
         'class': 'form-control resize-none'
      }),
      required=True
   )

   image_file = forms.ImageField(
      required=False,
      widget=forms.FileInput(attrs={'class': 'form-control'}),
      label='Screenshot'
   )

   page = forms.IntegerField(
      label='Page',
      required=True,
      widget=forms.NumberInput(attrs={
         'class': 'form-control d-inline',
         'style': 'width: auto',
         'placeholder': '#'
      })
   )

   def __init__(self, *args, **kwargs):
      ajax_url = kwargs.pop('ajax_url', None)
      initial_word_id = kwargs.pop('initial_word_id', None)
      initial_word    = kwargs.pop('initial_word', None)
      initial_defn_id = kwargs.pop('initial_defn_id', None)
      can_add_img     = kwargs.pop('can_add_img', None)
      is_book = kwargs.pop('is_book', None)
      super().__init__(*args, **kwargs)

      word_widget = self.fields['word'].widget
      word_widget.attrs['data-ajax-url'] = ajax_url
      word_widget.attrs['data-initial-id'] = initial_word_id
      word_widget.attrs['data-initial-word'] = initial_word
      self.fields['definition_select'].widget.attrs['data-initial-id'] = initial_defn_id

      if not can_add_img:
         del self.fields['image_file']
      if is_book:
         self.fields['spotted_at'].required = False
      else:
         del self.fields['page']
         
      # # when validation fails the same word is selected
      # if self.is_bound and 'word' in self.data:
      #    submitted_id = self.data.get('word')
      #    if submitted_id:
      #       self.fields['word'].queryset = Word.objects.filter(pk=submitted_id)

   def clean(self):
      cleaned_data = super().clean()
      defn_input = cleaned_data.get('definition_input')
      defn_select = cleaned_data.get('definition_select')
      if not defn_input and not defn_select:
         raise forms.ValidationError(f"An existent/new definition is required")
      
      if defn_select and defn_select != '-1':
         try:
            defn_obj = Definition.objects.get(pk=int(defn_select))
            cleaned_data['defn_object']=defn_obj
         except(ValueError, Definition.DoesNotExist):
            raise forms.ValidationError(f"Invalid definition selected")
      elif defn_select == '-1' and not defn_input:
         raise forms.ValidationError(f"Please enter a new definition description")
      
      return cleaned_data


class CitationDelete(forms.Form):
   delete_example = forms.BooleanField(
      required=False,
      initial=False,
      widget=forms.CheckboxInput(attrs={
         'class': 'form-check-input'
      }),
   )

   def __init__(self, *args, citation_id=None, **kwargs):
      super().__init__(*args, **kwargs)
      self.citation_id = citation_id

   def save(self):
      delete_example = self.cleaned_data.get('delete_example')
      citation = Citation.objects.get(pk=self.citation_id)
      if delete_example:
         citation.example.delete()
      if citation.image:
         img = citation.image
         storage = img.file.storage
         if storage.exists(img.file.name):
            storage.delete(img.file.name)
         img.delete()

      citation.delete()



class CitationFormDetailsPage(forms.Form):
   source=forms.ModelChoiceField(
      widget=forms.Select(attrs={
         'placeholder': "Select a source...",
         'class': 'select2',
         'required': 'true',
      }),
      queryset=Source.objects.none(),
      required=True
   )

   episode=forms.ModelChoiceField(
      widget=forms.Select(attrs={
         'placeholder': "Select an episode...",
         'class': 'select2',
         'required': 'true',
      }),
      empty_label="Select an episode",
      queryset=Episode.objects.none(),
      required=False
   )

   spotted_at = forms.DurationField(
      label="Spotted at:",
      widget=forms.TextInput(attrs={
         'placeholder': 'HH:MM:SS',
         'class': 'form-control w-100',
         'style': 'width: auto'
      }),
      required=True
   )

   image_file = forms.ImageField(
      required=False,
      widget=forms.FileInput(attrs={'class': 'form-control'}),
      label='Screenshot'
   )

   def __init__(self, *args, **kwargs):
      lang_id = kwargs.pop('lang_id', None)
      super().__init__(*args, **kwargs)

      source_id = None
      if self.is_bound:
         if lang_id:
            self.fields['source'].queryset = Source.objects.filter(language_id=lang_id)
         source_id = self.data.get(f'{self.prefix}-source')
      elif 'source' in self.initial:
         source_id = self.initial.get('source')
      
      if source_id:
         source = Source.objects.get(pk=source_id)
         self.fields['episode'].queryset = source.episodes.all()


class SegmentForm(forms.ModelForm):

   class Meta:
      model=Segment
      fields=['segment_type', 'number', 'name']
      widgets = {
         'segment_type': forms.Select(attrs={'class': 'select2'}),
         'name': forms.TextInput(attrs={'class': 'form-control'}),
         'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#'}),
      }
      labels = {
         'name': 'Segment name',
      }

   def __init__(self, *args, **kwargs):
      self.source = kwargs.pop('source', None)
      source_category = kwargs.pop('source_category', None)
      super().__init__(*args, **kwargs)
      if source_category == 'ALB':
         self.fields['segment_type'].choices = [
            (Segment.SegmentType.TRACK.value, Segment.SegmentType.TRACK.label)
         ]
      elif source_category == 'BOK' or source_category == 'ABK':
         self.fields['segment_type'].choices = [
            (Segment.SegmentType.PROLOGUE.value, Segment.SegmentType.PROLOGUE.label),
            (Segment.SegmentType.CHAPTER.value, Segment.SegmentType.CHAPTER.label),
            (Segment.SegmentType.EPILOGUE.value, Segment.SegmentType.EPILOGUE.label),
         ]
         self.fields['number'].required = False
         self.fields['name'].required = False

   
   def clean(self):
      cleaned_data = super().clean()
      segment_type = cleaned_data.get('segment_type')
      name = cleaned_data.get('name')
      number = cleaned_data.get('number')

      if segment_type in ['PRL', 'EPL']:
         qs = Segment.objects.filter(source=self.source, segment_type=segment_type)

         if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
      
         if qs.exists():
            name = 'Prologue' if segment_type == 'PRL' else 'Epilogue'
            raise forms.ValidationError(f'A {name} already exists for this source.')
      
      if not name:
         cleaned_data['name'] = 'Prologue' if segment_type == 'PRL' else 'Epilogue'
      
      if not number:
         cleaned_data['number'] = "1"
      
      return cleaned_data

   def save(self, commit=True):
      segment = super().save(commit=False)
      segment.source = self.source

      if commit:
         segment.save()

      return segment

class WordListFilters(forms.Form):
   timeUnitType = forms.ChoiceField(
      required=False,
      choices = [
         ('', 'Time unit'),
         ("Y", "Year(s) Ago"),
         ("M", "Month(s) Ago"),
         ("W", "Week(s) Ago"),
         ("D", "Day(s) Ago"),
      ],
      initial='',
      widget=forms.Select(attrs={
         'class': 'select2 w-70',
         'data-allow-clear': 'true',
         'data-placeholder': 'Time unit',
         'data-remove-search': 'true'
      })
   )

   timeUnitValue = forms.IntegerField(
      required=False,
      widget=forms.NumberInput(attrs={
         'class': 'form-control w-30',
         'placeholder': '#'
      })
   )

   forgettingFrequency = forms.ChoiceField(
      required=False,
      choices = [('', '--- Select ---')] + Definition.ForgettingFrequency.choices,
      widget=forms.Select(attrs={
         'class': 'select2',
         'data-allow-clear': 'true',
         'data-placeholder': 'Forgetting frequency',
         'data-remove-search': 'true'
      })
   )

   region = forms.ModelChoiceField(
      required=False,
      queryset=Country.objects.none(),
      widget=forms.Select(attrs={
         'class': 'select2',
         'data-allow-clear': 'true',
         'data-placeholder': 'Region'
      })
   )

   source = forms.IntegerField(
      required=False,
      widget=forms.Select(attrs={
         'class': 'select2 select2-ajax',
         'data-allow-clear': 'true',
         'data-is-ajax': 'true',
         'data-placeholder': 'Source',
         'data-min-input-len': '3'
      })
   )

   def __init__(self, *args, **kwargs):
      lang_id = kwargs.pop('lang_id', None)
      super().__init__(*args, **kwargs)
      source_id = self.data.get('source')
      if lang_id:
         language = Language.objects.filter(pk=lang_id)
         self.fields['region'].queryset = Country.objects.filter(languages__pk=lang_id)
         self.fields['source'].widget.attrs['data-ajax-url'] = reverse('search_source', kwargs={'lang_id': lang_id})
      if source_id:
         try:
            src = Source.objects.get(id=source_id)
            self.fields['source'].widget.choices = [(src.id, src.name)]
         except Source.DoesNotExist:
            pass
