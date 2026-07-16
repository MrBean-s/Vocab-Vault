import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .forms import *
from .models import *
from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.urls import reverse


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
      else:
         print('not valid')
      return redirect('start_screen')
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
   words = lang.word_set.prefetch_related('definitions__examples').order_by('-id')
   paginator = Paginator(words, 30)
   page_obj = paginator.get_page(request.GET.get('page', 1))
   page_range = paginator.get_elided_page_range(
      number=page_obj.number,
      on_each_side=2,
      on_ends=1
   )

   sources_by_category = {}

   for category, name, id in Source.objects.values_list('source_category', 'name', 'id').iterator():
      label = Source.SourceCategory(category).label
      sources_by_category.setdefault(label, []).append((id, name))

   return render(request, 'word_list.html', {
      'lang_id': lang_id,
      'page_obj': page_obj,
      'sources_by_category': sources_by_category,
      'pages': page_range
   })


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

   return render(request, 'partial/_image_preview.html', {'image': instance})


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
   items = []
   print(f'query: {query} lang_id: {lang_id}')
   if query:
      items = list(
         Word.objects.filter(
            name__icontains=query, language_id=lang_id
         ).values('id', 'name').order_by('name')[:15]
      )
   
   return JsonResponse(items, safe=False)


def word_relation(request, lang_id, word_id, rel_word_id):
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

   return render(request, 'forms/_relation_options.html', {
      "lang_id": lang_id,
      'word': word,
      "rel_word": rel_word,
      'form': form
   })

def confirm_unlink(request, lang_id, word_id, rel_word_id):
   word = get_object_or_404(Word, pk=word_id)
   rel_word = get_object_or_404(Word, pk=rel_word_id)

   if request.method == "POST":
      relations = WordRelation.objects.filter(
         (Q(word_1=word) & Q(word_2=rel_word)) |
         (Q(word_1=rel_word) & Q(word_2=word))
      )
      relations.delete()
      return redirect('word_details', lang_id=lang_id, word_id=word_id)

   return render(request, 'forms/_confirm_unlink.html', {
      "lang_id": lang_id,
      "word": word,
      "rel_word": rel_word,
      "form_url": request.path
   })