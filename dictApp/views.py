import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from .forms import *
from .models import *
from django.contrib import messages
from django.db.models import ProtectedError, Q, Count, Prefetch
from django.core.paginator import Paginator
from django.core.exceptions import BadRequest
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.urls import reverse
from itertools import groupby
from django.conf import settings
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta, MO


def start_screen(request):
   languages = Language.objects.select_related('image').filter(in_user_set=True).all()

   return render(request, "start_page.html", {
      "languages": languages,
   })


def language_form(request, lang_id=None):

   can_edit_img = request.GET.get('can_edit_img', 'false')
   can_edit_img = can_edit_img.lower() == 'true'

   language = get_object_or_404(Language, pk=lang_id) if lang_id else None
   
   if request.method == 'POST':
      lang_form = LanguageForm(request.POST, request.FILES, instance=language)
               
      if lang_form.is_valid():
         new_lang = lang_form.save()
         if not language:
            new_lang.added_manually=True
            new_lang.save()

         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Redirect': '/languages/'})
         return redirect('languages')
   else:
      countries = language.countries.all().order_by('name') if language else Country.objects.none()
      lang_form = LanguageForm(instance=language, initial={'countries': countries})

   return render(request, "forms/_language_form.html", 
      {
         "form": lang_form,
         "is_edit" : language is not None,
         'edit_lang_id': language.id if language else 0,
         'can_edit_img': can_edit_img
      })

def languages(request):
   languages = Language.objects.select_related('image').all()
   in_home_screen = Language.objects.filter(in_user_set=True).values_list('id', 'name')
   return render(request, "languages.html", {"languages": languages, "in_home_screen": in_home_screen})

def delete_language(request, lang_id):
   instance = get_object_or_404(Language, pk=lang_id)

   if request.method == 'POST':
      img = instance.image
      try:
         instance.delete()	
      except ProtectedError:
         messages.error(request, "Cannot delete language because it still has words. Delete the words first.")
      else:
         if img:
            storage = img.file.storage
            if storage.exists(img.file.name):
               storage.delete(img.file.name)
            img.delete()
         
         messages.success(request, "Language deleted.")

      return redirect('languages')
   
def add_lang_to_set(request):
   if request.method == 'POST':
      form = LanguageAddSetForm(request.POST)
      if form.is_valid():
         language = form.cleaned_data.get('language')
         language.in_user_set=True
         language.save()
         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Redirect': '/'})
         return redirect('start_screen')
   else:
      form = LanguageAddSetForm()
   return render(request, 'forms/_add_language.html', {'form': form})

def add_lang_to_set_with_id(request, lang_id):
   language = get_object_or_404(Language, pk=lang_id)
   language.in_user_set=True
   language.save()

   return redirect('languages')

def remove_lang_from_set(request, lang_id):
   language = get_object_or_404(Language, pk=lang_id)
   language.in_user_set=False
   language.save()
   return redirect('start_screen')


def generic_confirm_delete(request):
   name = request.GET.get('name', '')
   delete_url = request.GET.get('delete_url', '')
   obj_type = request.GET.get('type', 'item')

   return render(request, 'forms/_confirm_delete.html', {
      'name': name,
      'delete_url': delete_url,
      'type': obj_type,
   })


def dashboard(request, lang_id):
   return HttpResponse("<h1>Hello, World!</h1>", content_type="text/html")


def word(request, lang_id, word_id=None):
   language = get_object_or_404(
      Language.objects.prefetch_related('countries', 'parts_of_speech'),
      pk=lang_id
   )
   
   word = get_object_or_404(
      Word.objects
         .select_related('language')
         .prefetch_related('language__countries', 'definitions__country_tags'),
      pk=word_id
   ) if word_id else None

   country_qs = Country.objects.filter(languages__pk=language.id)
   def_selected_ctys = {}

   if word:
      def_selected_ctys = {
         defn.id: defn.get_selected_countries_ids()
         for defn in word.definitions.all()
      }

   if request.method == 'POST':
      word_form = WordForm(request.POST, instance=word)

      def_formset = DefinitionFormSet(
         request.POST,
         request.FILES,
         instance=word,
         prefix='definitions',
      )
   
      # Build example formsets from POST data
      example_formsets = []
      total_defs = int(request.POST.get('definitions-TOTAL_FORMS', 0))
      for i in range(total_defs):
         prefix = f'def-{i}-examples'

         def_id = request.POST.get(f'definitions-{i}-id')
         def_instance = Definition.objects.get(pk=def_id) if def_id else None
         ex_fs = ExampleFormSet(request.POST, prefix=prefix, instance=def_instance, language=language)
         example_formsets.append(ex_fs)

      if (word_form.is_valid() and def_formset.is_valid() and
         all(ex_fs.is_valid() for ex_fs in example_formsets)):
         
         word = word_form.save(commit=False)
         word.language = language
         word.save()
   
         for idx, def_form in enumerate(def_formset.forms):
            # Skip forms marked for deletion
            if def_form.cleaned_data.get('DELETE', False):
               continue
            definition = def_form.save(commit=False)
            definition.word = word
            definition.save()

            country_set = request.POST.getlist(f'def-{idx}-countries')

            if '-999' in country_set: # -999: ALL tag
               definition.country_tags.set(language.countries.all());
               definition.save()
            else:
               countries = Country.objects.filter(id__in=country_set)
               definition.country_tags.set(countries)

            # original index to pick the correct example formset
            ex_fs = example_formsets[idx]
            examples = ex_fs.save(commit=False)
            for ex in examples:
               ex.definition = definition
               ex.save()
            for obj in ex_fs.deleted_objects:
               obj.delete()
   
         # Handle deleted definitions
         for idx, def_form in enumerate(def_formset.forms):
            if def_form.cleaned_data.get('DELETE', False) and def_form.instance.pk:
               img_to_del = def_form.instance.image
               if img_to_del:
                  storage = img_to_del.file.storage
                  if storage.exists(img_to_del.file.name):
                     storage.delete(img_to_del.file.name)

                  img_to_del.delete()

               def_form.instance.delete()

   
         return redirect('word_details', lang_id=lang_id, word_id=word.id)
   else:
      word_form = WordForm(instance=word)
      def_formset = DefinitionFormSet(instance=word, prefix='definitions')
      for def_form in def_formset:
         if def_form.instance.pk:
            def_form.selected_country_ids = def_selected_ctys.get(def_form.instance.pk, [])
         else:
            def_form.selected_country_ids = []

      example_formsets = []

      for i, def_form in enumerate(def_formset):
         prefix = f'def-{i}-examples'
         def_instance = def_form.instance if def_form.instance.pk else None
         ex_fs = ExampleFormSet(prefix=prefix, instance=def_instance, language=language)


         example_formsets.append(ex_fs)
   
   return render(request, 'word_add_edit.html', {
      'word_form': word_form,
      'def_formset': def_formset,
      'example_formsets': example_formsets,
      'has_word': word is not None,
      'word_id': word_id,
      'lang_id': lang_id,
      'country_qs': country_qs,
   })

def word_delete(request, lang_id, word_id):
   word = get_object_or_404(
      Word.objects.prefetch_related('definitions'),
      pk=word_id,
      language_id=lang_id
   )

   for defn in word.definitions.all():
      img = defn.image
      if img:
         storage = img.file.storage
         if storage.exists(img.file.name):
            storage.delete(img.file.name)

         img.delete()

   word.delete()
   messages.success(request, "Word deleted")

   return redirect('word_list', lang_id=lang_id)


def word_list(request, lang_id):
   lang = get_object_or_404(Language, pk=lang_id)
   words_qs = lang.word_set.all()

   form = WordListFilters(request.GET, lang_id=lang_id)
   context = { 'lang_id': lang_id, 'form': form }

   # for dynamic prefetch
   def_qs = Definition.objects.prefetch_related('country_tags')
   ex_qs = Example.objects.select_related(
      'citation__source', 
      'citation__episode', 
      'citation__segment',
      'part_of_speech',
   )

   if form.is_valid():
      time_unit_type = form.cleaned_data.get('timeUnitType')
      time_unit_value = form.cleaned_data.get('timeUnitValue')
      forgetting_frequency = form.cleaned_data.get('forgettingFrequency')
      region = form.cleaned_data.get('region')
      source = form.cleaned_data.get('source')
   
      if time_unit_type in ['D', 'W', 'M', 'Y'] and time_unit_value:
         gmt6_zone = timezone(timedelta(hours=-6))
         gmt6_now = datetime.now(gmt6_zone)

         if time_unit_type == 'M':
            target = gmt6_now - relativedelta(months=time_unit_value)
            start_date = target.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + relativedelta(months=1) - timedelta(microseconds=1)

         elif time_unit_type == 'Y':
            target = gmt6_now - relativedelta(years=time_unit_value)
            start_date = target.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + relativedelta(years=1) - timedelta(microseconds=1)

         elif time_unit_type == 'W':
            target = gmt6_now - relativedelta(weeks=time_unit_value)
            start_date = (target + relativedelta(weekday=MO(-1))).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + relativedelta(weeks=1) - timedelta(microseconds=1)

         elif time_unit_type == 'D':
            target = gmt6_now - relativedelta(days=time_unit_value)
            start_date = target.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = target.replace(hour=23, minute=59, second=59, microsecond=999999)
         
         context.update({'start_date': start_date, 'end_date': end_date})

         words_qs = words_qs.filter(added_at__range=(start_date, end_date))

      if forgetting_frequency:
         words_qs = words_qs.filter(definitions__forgetting_frequency=forgetting_frequency)
         def_qs = def_qs.filter(forgetting_frequency=forgetting_frequency)
      
      if region:
         qualifying_def_ids = Definition.objects.annotate(
            total_tags=Count('country_tags')
         ).filter(
            total_tags=1,
            country_tags=region
         ).values_list('pk', flat=True)

         words_qs = words_qs.filter(definitions__pk__in=qualifying_def_ids)
         def_qs = def_qs.filter(pk__in=qualifying_def_ids)
      if source:
         source_q = (
            Q(citation__source_id=source) |
            Q(citation__episode__source_id=source) |
            Q(citation__segment__source_id=source)
         )
         matching_examples = Example.objects.filter(source_q)

         words_qs = words_qs.filter(definitions__examples__in=matching_examples)
         def_qs = def_qs.filter(examples__in=matching_examples).distinct()
         ex_qs = ex_qs.filter(source_q)

   def_prefetch = Prefetch(
      'definitions',
      queryset=def_qs.prefetch_related(Prefetch('examples', queryset=ex_qs))
   )

   words_qs = words_qs.distinct().prefetch_related(def_prefetch).order_by('-id')

   paginator = Paginator(words_qs, 10)
   page_obj = paginator.get_page(request.GET.get('page', 1))
   page_range = paginator.get_elided_page_range(
      number=page_obj.number,
      on_each_side=2,
      on_ends=1
   )

   context.update({'page_obj': page_obj, 'pages': page_range})

   return render(request, 'word_list.html', context)


@csrf_exempt
def import_words_from_old_json(request, lang_id):
   language = get_object_or_404(Language, pk=lang_id)
   if request.method != 'POST':
      return JsonResponse({'error': 'POST only'}, status=405)
   try:
      data = json.loads(request.body)
   except json.JSONDecodeError:
      return JsonResponse({'error': 'Invalid JSON'}, status=400)
   if not isinstance(data, list):
      return JsonResponse({'error': 'Expecting list of words'}, status=400)

   created_word_ids = []
   errors = []

   try:
      with transaction.atomic():
         for word_data in data:
            name = word_data.get('name')
            if not name:
               errors.append(f'Missing name in {word_data}')
               raise ValueError('Missing name')

            word = Word.objects.create(name=name, language=language)

            for def_data in word_data.get('definitions', []):
               desc = def_data.get('definition')  # old field name
               if not desc:
                     errors.append(f'Missing definition for word "{name}"')
                     raise ValueError('Missing definition')

               definition = Definition.objects.create(
                     word=word,
                     description=desc
               )

               for ex_data in def_data.get('examples', []):
                     ex_text = ex_data.get('example')
                     if not ex_text:
                        errors.append(f'Missing example for word "{name}"')
                        raise ValueError('Missing example')

                     Example.objects.create(
                        definition=definition,
                        description=ex_text
                     )

            created_word_ids.append(word.id)
   except ValueError:
      pass

   if errors:
      return JsonResponse({'status': 'failed', 'errors': errors}, status=400)

   return JsonResponse({'status': 'ok', 'created_word_ids': created_word_ids}, status=201)

def search(request, lang_id):
   language = get_object_or_404(Language, pk=lang_id)
   
   if not request.META.get('HTTP_HX_REQUEST'):
      return redirect('dashboard', lang_id=lang_id)

   form = ModalSearchForm(request.GET or None, initial={'filter': ['word']})
   filters = []
   results = {}
   is_submission = False

   if form.is_valid():
      is_submission = True
      query = form.cleaned_data['query'].lower()
      filters = form.cleaned_data['filter']
      temp_limit = form.cleaned_data.get('limit')
      limit = 5 if not temp_limit or not(0 < temp_limit <= 30) else temp_limit
      newest_first = form.cleaned_data['newest_first']
      order = 'id' if not newest_first else '-id'
   else:
      return render(request, 'modals/simple_search.html', {
      'lang_id': lang_id,
      'search_form': form,
      'results_dict': results
      })
      
   if 'word' in filters:
      word_results = Word.objects.filter(
      name__icontains=query, language_id=lang_id
      ).values_list('id', 'name').order_by(order)[:limit]

      for wid, wname in word_results.iterator():
         results.setdefault('words', []).append({'word_id': wid, 'word': wname})

   if 'definition' in filters:
      desc_results = Definition.objects.filter(
         description__icontains=query, word__language_id=lang_id
      ).values_list('description', 'word__name', 'word__id').order_by(order)[:limit]

      for desc, wname, wid in desc_results.iterator():
         results.setdefault('definitions', []).append({
            'word_id': wid, 'definition': desc, 'word': wname,
         })
   
   if 'example' in filters:
      ex_results = Example.objects.filter(
         description__icontains=query, definition__word__language_id=lang_id
      ).values_list(
         'description', 'definition__word__name', 'definition__word__id'
      ).order_by(order)[:limit]
      
      temp = defaultdict(list)
      for desc, wname, wid in ex_results:
         temp[(wname, wid)].append(desc)

      example_results = [
         { 'word': word, 'word_id': word_id, 'examples': examples }
         for (word, word_id), examples in temp.items()
      ]

      if example_results:
         results["examples"] = example_results

   return render(request, 'modals/simple_search.html', {
      'lang_id': lang_id,
      'search_form': form,
      'results_dict': results,
      'is_submission': is_submission,
      'has_results': len(results) > 0 
   })
   
   
def word_details(request, lang_id, word_id):
   language = get_object_or_404(
      Language.objects.prefetch_related('countries', 'parts_of_speech'),
      pk=lang_id
   )
   
   word = get_object_or_404(
      Word.objects.prefetch_related('definitions__country_tags'),
      pk=word_id
   )

   rels = WordRelation.objects.filter(word_1=word).select_related('word_2')
   related_words = [
      { "id": rel.word_2.id, "name": rel.word_2.name, "relation": rel.get_relation_type_display().title() }
      for rel in rels
   ]
   
   all_lang_countries_ids = {c.id for c in language.countries.all()}
   context = { 
      "name": word.name,
      "id": word.id,
      "definitions": [
         defn.to_json(all_lang_countries_ids=all_lang_countries_ids)
         for defn in word.definitions.all()
      ]
   }

   return render(request, 'word_details.html', {
      'lang_id': lang_id,
      'ngram_code': language.google_ngram_code,
      'context': context,
      'related_words': related_words
   })

def countries(request):
   if request.method == "POST":
      form = CountryForm(request.POST)
      if form.is_valid():
         country = form.save(commit=False)
         country.added_manually = True
         country.save()
         return redirect('countries')
   else:   
      form = CountryForm(instance=None)

   countries = Country.objects.all().order_by('name')

   return render(request, 'countries.html', {
      'form': form,
      'countries': countries
   })

def delete_country(request, cty_id):
   instance = get_object_or_404(Country, pk=cty_id)

   if request.method == 'POST':
      instance.delete()      
      messages.success(request, "Country deleted.")

      return redirect('countries')

def show_image(request, img_id):
   instance = get_object_or_404(Image, pk=img_id)

   return render(request, 'modals/_image_preview.html', {'image': instance})


def link_word(request, lang_id, word_id):
   word1 = get_object_or_404(Word, pk=word_id)
   ajax_url = reverse('search_word', kwargs={'lang_id': lang_id})

   if request.method == "POST":
      form = LinkWordForm(request.POST, ajax_url=ajax_url)

      if form.is_valid():
         word2 = form.cleaned_data['word_2']
         rel_type = form.cleaned_data['relation_type']


         if word2.language.pk == lang_id:
            WordRelation.objects.get_or_create(
               word_1=word1,
               word_2=word2,
               defaults={'relation_type': rel_type}
            )
            WordRelation.objects.get_or_create(
               word_1=word2,
               word_2=word1,
               defaults={'relation_type': rel_type}
            )

         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Redirect': f'/lang/{lang_id}/word/{word_id}/'})
         return redirect('word_details', lang_id=lang_id, word_id=word_id)
   else:
      form = LinkWordForm(ajax_url=ajax_url)

   form.fields['word_1_id'].initial = word1.id


   return render(request, 'forms/_link_word_form.html', {
      "form": form,
      "lang_id": lang_id,
      "word_id": word_id
   })


def word_only_search(request, lang_id):
   query = request.GET.get('query', '')
   if query:
      word_qs = Word.objects.filter(
         name__icontains=query, language_id=lang_id
      ).values('id', 'name').order_by('name')[:15]

      results = {
         'results': [ {"id": item['id'], "text": item['name']} for item in word_qs]
      }
   return JsonResponse(results)


def link_word_edit(request, lang_id, word_id, rel_word_id):
   word = get_object_or_404(Word, pk=word_id)
   rel_word = get_object_or_404(Word, pk=rel_word_id)

   relations = WordRelation.objects.filter(
      (Q(word_1=word) & Q(word_2=rel_word)) |
      (Q(word_1=rel_word) & Q(word_2=word))
   )
   form = RelationTypeForm({'relation_type': relations.first().relation_type})

   if request.method == "POST":
      form = RelationTypeForm(request.POST)
      if form.is_valid():
         for rel in relations:
            rel.relation_type = form.cleaned_data['relation_type']
            rel.save()

         return redirect('word_details', lang_id=lang_id, word_id=word_id)

   return render(request, 'forms/_link_word_edit.html', {
      "lang_id": lang_id,
      'word_id': word_id,
      "rel_word": rel_word,
      'form': form
   })

def unlink_word(request, lang_id, word_id, rel_word_id):
   word = get_object_or_404(Word, pk=word_id)
   rel_word = get_object_or_404(Word, pk=rel_word_id)

   if request.method == "POST":
      relations = WordRelation.objects.filter(
         (Q(word_1=word) & Q(word_2=rel_word)) |
         (Q(word_1=rel_word) & Q(word_2=word))
      )
      relations.delete()
      return redirect('word_details', lang_id=lang_id, word_id=word_id)

   return render(request, 'forms/_unlink_word.html', {
      "lang_id": lang_id,
      "word": word,
      "rel_word": rel_word,
      "form_url": request.path
   })


def sources(request, lang_id):

   section_sources = Source.objects.filter(
      language_id=lang_id,
      source_category__in=['BOK', 'MOV', 'TVS', 'ALB']
   ).order_by('-source_category')

   CATEGORY_ORDER = ['TVS', 'MOV', 'BOK', 'ALB']
   
   #to preserve insertion order
   category_labels = dict(Source.SourceCategory.choices)
   sections = {category_labels[code]: [] for code in CATEGORY_ORDER if code in category_labels}

   for source in section_sources:
      label = source.get_source_category_display()
      if label in sections:
         sections[label].append(source)

   sections = {label: sources for label, sources in sections.items() if sources}

   audio_sources = Source.objects.filter(
      language_id=lang_id,
      source_category__in=['ABK', 'SON', 'POD']
   ).order_by('-source_category')

   return render(request, 'sources.html', {
      'lang_id': lang_id,
      'sections' : sections,
      'audio_sources': audio_sources
   })

def sources_add_edit(request, lang_id, source_id=None):

   source = get_object_or_404(Source, pk=source_id) if source_id else None
   language = get_object_or_404(Language, pk=lang_id)

   if request.method == "POST":
      form = SourceForm(request.POST, request.FILES, instance=source)
      if form.is_valid():
         source = form.save(commit=False)
         source.language = language
         source.save()

         action = 'edited' if source_id else 'created'
         messages.success(request, f"Source {action}")
         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Refresh': 'true'})
         return redirect('sources', lang_id=lang_id)
   else:
      form = SourceForm(instance=source)
      
   return render(request, 'forms/_source_form.html', {
      "lang_id": lang_id,
      "source": source,
      "form": form,
      "is_edit": source_id is not None
   })


def source_delete(request, lang_id, source_id):
   source = get_object_or_404(Source, pk=source_id)

   if request.method == 'POST':
      img = source.image
      try:
         source.delete()	
      except ProtectedError:
         messages.error(request, "Cannot delete Source cause it still has related data. Delete all episodes/content first.")
      else:
         if img:
            storage = img.file.storage
            if storage.exists(img.file.name):
               storage.delete(img.file.name)
            img.delete()
         
         messages.success(request, "Source deleted.")

      return redirect('sources', lang_id=lang_id)


def episodes(request, lang_id, source_id):
   source = get_object_or_404(Source, pk=source_id)
   episodes = Episode.objects.filter(source_id=source_id).order_by('season_number')
   grouped_by_season = {season: list(group) for season, group in groupby(episodes, key=lambda x: x.season_number)}

   return render(request, 'episodes.html', {
      'lang_id': lang_id,
      'grouped_by_season': grouped_by_season,
      'source': source
   })


def episode_add_edit(request, source_id, episode_id=None):
   episode = get_object_or_404(Episode, pk=episode_id) if episode_id else None
   source = get_object_or_404(Source, pk=source_id)

   if request.method == "POST":
      if episode is None:
         episode = Episode(source=source)
      
      form = EpisodeForm(request.POST, instance=episode)
      if form.is_valid():
         episode = form.save(commit=False)
         episode.source = source
         episode.save()
         
         action = 'edited' if episode_id else 'created'
         messages.success(request, f"Episode {action}")
         
         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Refresh': 'true'})
         return redirect('episodes', source_id=source_id)
   else:
      form = EpisodeForm(instance=episode)

   return render(request, 'forms/_episode_form.html', {
      'source_id': source_id,
      'episode_id': episode_id,
      'form': form,
      'is_edit': episode is not None,
      'episode': episode
   })


def episode_delete(request, source_id, episode_id):
   episode = get_object_or_404(Episode, pk=episode_id)
   source = get_object_or_404(Source, pk=source_id)
   try:
      episode.delete()
      messages.success(request, "Episode deleted.")
   except ProtectedError:
      messages.error(request, "Remove all citations before deleting the episode") 
   
   return redirect('episodes', lang_id=source.language_id, source_id=source_id)


def segments(request, lang_id, source_id):
   source = get_object_or_404(
      Source.objects.prefetch_related('segments'),
      pk=source_id
   )

   categorized = {}
   for seg in source.segments.all().order_by('-segment_type'):
      categorized.setdefault(seg.get_segment_type_display(), []).append({'id': seg.id, 'number': seg.number, 'name': seg.name})
   
   return render(request, 'segments.html', {
      'lang_id': lang_id,
      'source_id': source_id,
      'source': source,
      'segments': categorized
   })


def segment_add_edit(request, source_id, segment_id=None):
   source = get_object_or_404(Source, pk=source_id)
   segment = get_object_or_404(Segment, pk=segment_id) if segment_id else None
   if request.method == 'POST':
      form = SegmentForm(request.POST, instance=segment, source=source, source_category=source.source_category)
      if form.is_valid():
         form.save()
         action = 'edited' if segment_id else 'created'
         messages.success(request, f"Segment {action}")

         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Refresh': 'true'})
         return redirect('episodes', source_id=source_id)
   else:
      form = SegmentForm(instance=segment, source=source, source_category=source.source_category)
   
   return render(request, 'forms/_segment_form.html', {
      'form': form,
      'source_id': source_id,
      'is_edit': segment is not None,
      'segment': segment,
   })


def segment_delete(request, source_id, segment_id):
   segment = get_object_or_404(Segment, pk=segment_id)
   source = get_object_or_404(Source, pk=source_id)
   try:
      segment.delete()
      messages.success(request, "Segment deleted.")
   except ProtectedError:
      messages.error(request, "Remove all citations before deleting the segment")
   
   return redirect('segments', lang_id=source.language_id, source_id=source_id)


def citation_delete(request, lang_id, citation_id):
   citation = get_object_or_404(Citation, pk=citation_id)
   
   if request.method == 'POST':
      form = CitationDelete(request.POST, citation_id=citation_id)
      if form.is_valid():
         form.save()
         if request.META.get('HTTP_HX_REQUEST'):
            if citation.episode:
               kind, obj_id = 'episode', citation.episode_id
            elif citation.segment:
               kind, obj_id = 'segment', citation.segment_id
            else:
               kind, obj_id = 'source', citation.source_id

            return HttpResponse(headers={'HX-Redirect': f'/lang/{lang_id}/{kind}/{obj_id}/play-session/'})
         return redirect('episodes', source_id=source_id)
   else:
      form = CitationDelete(citation_id=citation_id)

   return render(request, 'forms/_citation_delete.html', {
      'lang_id': lang_id,
      'citation_id': citation_id,
      'form': form
   })


def play_session(request, lang_id, source_id=None, episode_id=None, segment_id=None):
   source = get_object_or_404(Source, pk=source_id) if source_id else None
   episode = get_object_or_404(Episode, pk=episode_id) if episode_id else None
   segment = get_object_or_404(Segment, pk=segment_id) if segment_id else None
   
   if not any([source, episode, segment]):
      return HttpResponseBadRequest('At least one source is required')

   defn_ajax_url = reverse('get_definitions')

   qs = ( 
      Citation.objects
      .values_list(
         'id',
         'spotted_at',
         'example__definition__word_id',
         'example__definition__word__name',
         'example__definition_id',
         'example__definition__description',
         'example_id',
         'example__description',
         'image__file',
         'image_id',
         'page'
      )
   )

   obj = episode or segment or source
   temp_src = getattr(obj, 'source', obj)
   qs = qs.filter(**{('source' if obj == source else obj.__class__.__name__.lower()): obj})

   spreads = [] # for books only

   if temp_src.source_category in ['MOV', 'TVS']:
      template = 'play_session_film.html'
   elif temp_src.source_category in ['ALB', 'SON', 'ABK', 'POD']:
      template = 'play_session_sound.html'
   elif temp_src.source_category in ['BOK']:
      template = 'play_session_book.html'
      
      citations_per_page = 4
      first_left_page_count = 3

      flat_citations = list(qs)

      # First spread: title + 3 citations
      left_first = flat_citations[:first_left_page_count]
      right_first = flat_citations[first_left_page_count:first_left_page_count + citations_per_page]
      spreads.append({'left': left_first, 'right': right_first, 'chapter_title': segment.name,})


      remaining = flat_citations[first_left_page_count + citations_per_page:]

      for i in range(0, len(remaining), citations_per_page * 2):
         left_page = remaining[i:i + citations_per_page]
         right_page = remaining[i + citations_per_page:i + citations_per_page * 2]
         if left_page or right_page:
            spreads.append({
               'left': left_page or [],
               'right': right_page or [],
               'chapter_title': None,
            })
   
   # elif temp_src.source_category in ['GAM', 'OTH']
      # template = 'play_session_timeline.html'
   
   return render(request, template, {
      "lang_id": lang_id,
      "source": source,
      "episode": episode,
      "segment": segment,
      'defn_ajax_url': defn_ajax_url,
      'citations': qs,
      "MEDIA_URL": settings.MEDIA_URL,
      'spreads': spreads if spreads else None
   })


def play_session_cite(request, lang_id, source_id=None, episode_id=None, segment_id=None, citation_id=None):
   source = get_object_or_404(Source, pk=source_id) if source_id else None
   episode = get_object_or_404(Episode, pk=episode_id) if episode_id else None
   segment = get_object_or_404(Segment, pk=segment_id) if segment_id else None
   citation = get_object_or_404(Citation, pk=citation_id) if citation_id else None

   ajax_url = reverse('search_word', kwargs={'lang_id': lang_id})

   if not any([source, episode, segment]):
      return HttpResponseBadRequest('At least one source is required')
   
   can_add_img = bool(episode or (source and source.source_category == 'MOV'))
   is_book = bool(segment and segment.source.source_category == 'BOK')
   
   initial_data = { 'spotted_at': citation.spotted_at, 'example': citation.example.description, 'page': citation.page } if citation else {}

   if request.method == "POST":
      form = CitationForm(request.POST, request.FILES, ajax_url=ajax_url, initial=initial_data, can_add_img=can_add_img, is_book=is_book)
      if form.is_valid():
         word_val = form.cleaned_data['word']
         new_def = form.cleaned_data['definition_input']
         existing_def_id = form.cleaned_data['definition_select']
         
         if word_val.isdigit():
            word = get_object_or_404(Word, pk=int(word_val))
         else:
            word, created = Word.objects.get_or_create(name=word_val, language_id=lang_id)
         
         if existing_def_id and existing_def_id.isdigit() and existing_def_id != '-1':
            definition = get_object_or_404(Definition, pk=int(existing_def_id))
         elif new_def:
            definition = Definition.objects.create(description=new_def, word=word)

         example = citation.example if citation else Example()
         example.description = form.cleaned_data['example']
         example.definition = definition
         example.save()

         image_file = form.cleaned_data.get('image_file')
         spotted_at = form.cleaned_data['spotted_at']

         if not citation:
            citation = Citation.objects.create(
               spotted_at=spotted_at,
               example=example,
               source=source,
               episode=episode,
               segment=segment
            )
         else:
            citation.spotted_at=spotted_at
            old_img = citation.image
            if old_img and image_file:
               storage = old_img.file.storage
               if storage.exists(old_img.file.name):
                  storage.delete(old_img.file.name)
               old_img.delete()
         
         if image_file:
            citation.image = Image.objects.create(file=image_file)
         
         page = form.cleaned_data.get('page')
         citation.page = page
         citation.save()

         if source:
            redirect_url = reverse('play_session_source', kwargs={'lang_id': lang_id, 'source_id': source_id})
         
         elif episode:
            redirect_url = reverse('play_session_episode', kwargs={'lang_id': lang_id, 'episode_id': episode_id})
         
         elif segment:
            redirect_url = reverse('play_session_segment', kwargs={'lang_id': lang_id, 'segment_id': segment_id})

         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Redirect': redirect_url})
         return redirect(redirect_url)
         
   else:      
      if citation:
         form = CitationForm(
            ajax_url=ajax_url,
            initial=initial_data,
            initial_word_id=citation.example.definition.word_id,
            initial_word=citation.example.definition.word.name,
            initial_defn_id=citation.example.definition_id,
            can_add_img=can_add_img,
            is_book=is_book
         )
      else:
         form = CitationForm(ajax_url=ajax_url, can_add_img=can_add_img, is_book=is_book)

   return render(request, 'forms/_citation_form.html', {
      'lang_id': lang_id,
      'source_id': source_id,
      'episode_id': episode_id,
      'segment_id': segment_id,
      'form': form,
      'path': request.path,
      'is_edit': citation is not None,
      'citation_id': citation_id
   })


def get_definitions(request):
   word_id = request.GET.get('word_id')
   if not word_id:
      return HttpResponseBadRequest('word_id is missing')

   if not word_id.isdigit():
      return JsonResponse({'results': []})

   word = get_object_or_404(
      Word.objects.prefetch_related('definitions'),
      pk=word_id
   )

   results = {
      'results': [ {'id': defn.id, 'text': defn.description} for defn in word.definitions.all() ]
   }

   return JsonResponse(results)

def search_episodes_or_segments(request, source_id):
   search_episodes = request.GET.get('search_episodes', '')

   if search_episodes == '':
      return HttpResponseBadRequest('The search episode option is missing')
   
   source = get_object_or_404(
      Source.objects.prefetch_related('episodes', 'segments'),
      pk=source_id
   )

   if search_episodes:
      results = { 'results': [ { 'value': ep.id, 'text': str(ep) } for ep in source.episodes.all() ] }
   else:
      results = { 'results': [ { 'value': seg.id, 'text': str(seg) } for seg in source.segments.all() ] }

   return JsonResponse(results)


def get_sources(request, lang_id):
   language = get_object_or_404(Language, pk=lang_id)
   data = { 
      'results': [
         {'value': src.id, 'text': str(src), 'category': src.source_category}
         for src in Source.objects.filter(language_id=lang_id)
      ]
   }
   return JsonResponse(data)


def search_source(request, lang_id):
   query = request.GET.get('query', '')
   
   if not query:
      return JsonResponse({"results": []})

   categories = dict(Source.SourceCategory.choices)
   by_category = defaultdict(list)

   for src in Source.objects.filter(language_id=lang_id, name__icontains=query).values('id', 'name', 'source_category'):
      cat = src['source_category']
      url = reverse(Source.REDIRECT_URLS[cat], kwargs={'lang_id': lang_id, 'source_id': src['id']})
      by_category[categories.get(cat)].append({'id': src['id'], 'text': src['name'], 'redirect_url': url})
   
   results = [ {"text": cat, "children": items} for cat, items in by_category.items() ]

   return JsonResponse({"results": results})

def example_cite(request, lang_id, example_id):

   example = get_object_or_404(Example, pk=example_id)

   if request.method == 'POST':
      form = CitationFormDetailsPage(request.POST, request.FILES, prefix="src-ep", lang_id=lang_id)
      
      if form.is_valid():
         source = form.cleaned_data['source']
         episode = form.cleaned_data.get('episode')
         spotted_at = form.cleaned_data['spotted_at']

         citation = Citation.objects.create(
            spotted_at=spotted_at,
            example=example,
            source=source if not episode else None,
            episode=episode,
         )

         image_file = form.cleaned_data.get('image_file')
         if image_file:
            citation.image = Image.objects.create(file=image_file)
            citation.save()

         if episode:
            redirect_url = reverse('play_session_episode', kwargs={'lang_id': lang_id, 'episode_id': episode.id})
         elif source:
            redirect_url = reverse('play_session_source', kwargs={'lang_id': lang_id, 'source_id': source.id})         

         if request.META.get('HTTP_HX_REQUEST'):
            return HttpResponse(headers={'HX-Redirect': redirect_url})
   else:
      form = CitationFormDetailsPage(prefix="src-ep", lang_id=lang_id)

   return render(request, 'forms/_citation_form_details_page.html', {
      'form': form,
      'lang_id': lang_id,
      'example_id': example_id
   })