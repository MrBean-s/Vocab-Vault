import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .forms import *
from .models import *
from django.contrib import messages
from django.db.models import ProtectedError
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict



def start_screen(request):
   languages = Language.objects.select_related('image').filter(in_user_set=True).all()
   remaining = len(languages) % 3

   return render(request, "start_page.html", {
      "languages": languages,
      "substract_len_mod3": -remaining,
      "twelve_mod3": round(12 / remaining if remaining > 0 else 12)
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
   language = get_object_or_404(Language, pk=lang_id)
   word = get_object_or_404(Word, pk=word_id) if word_id else None
   
   if request.method == 'POST':
      word_form = WordForm(request.POST, instance=word)
      def_formset = DefinitionFormSet(request.POST, instance=word, prefix='definitions')
   
      # Build example formsets from POST data (same as you'd do in GET, but using POST)
      example_formsets = []
      total_defs = int(request.POST.get('definitions-TOTAL_FORMS', 0))
      for i in range(total_defs):
         prefix = f'def-{i}-examples'
         # We need an instance only if this is an existing definition (has an ID)
         def_id = request.POST.get(f'definitions-{i}-id')
         def_instance = Definition.objects.get(pk=def_id) if def_id else None
         ex_fs = ExampleFormSet(request.POST, prefix=prefix, instance=def_instance)
         example_formsets.append(ex_fs)
   
      # Now validate everything
      if (word_form.is_valid() and def_formset.is_valid() and
         all(ex_fs.is_valid() for ex_fs in example_formsets)):
   
         # Save the Word
         word = word_form.save(commit=False)
         word.language = language
         word.save()
   
         # Iterate over all forms (including deleted ones) and keep the original index
         for idx, def_form in enumerate(def_formset.forms):
            # Skip forms marked for deletion
            if def_form.cleaned_data.get('DELETE', False):
               continue
            definition = def_form.save(commit=False)
            definition.word = word
            definition.save()
   
            # Use the original index to pick the correct example formset
            ex_fs = example_formsets[idx]
            examples = ex_fs.save(commit=False)
            for ex in examples:
               ex.definition = definition
               ex.save()
            for obj in ex_fs.deleted_objects:
               obj.delete()
   
         # Handle deleted definitions (those with DELETE=True, already skipped above)
         for idx, def_form in enumerate(def_formset.forms):
            if def_form.cleaned_data.get('DELETE', False) and def_form.instance.pk:
               def_form.instance.delete()
   
         return redirect('word_details', lang_id=lang_id, word_id=word.id) 
         # If any form is invalid, fall through to render the form with errors
         # (word_form, def_formset, and example_formsets are already bound)
   
   else:
      word_form = WordForm(instance=word)
      def_formset = DefinitionFormSet(instance=word, prefix='definitions')
      example_formsets = []

      for i, def_form in enumerate(def_formset):
         prefix = f'def-{i}-examples'
         def_instance = def_form.instance if def_form.instance.pk else None
         ex_fs = ExampleFormSet(prefix=prefix, instance=def_instance)

         example_formsets.append(ex_fs)
   
   return render(request, 'word_add_edit.html', {
      'word_form': word_form,
      'def_formset': def_formset,
      'example_formsets': example_formsets,
      'has_word': word is not None,
      'word_id': word_id,
      'lang_id': lang_id,
   })
   
def word_list(request, lang_id):
   lang = get_object_or_404(Language, pk=lang_id)
   words = lang.word_set.prefetch_related('definitions__examples').order_by('-id')
   paginator = Paginator(words, 30)
   page_obj = paginator.get_page(request.GET.get('page', 1))

   sources_by_category = {}

   for category, name, id in Source.objects.values_list('source_category', 'name', 'id').iterator():
      label = Source.SourceCategory(category).label
      sources_by_category.setdefault(label, []).append((id, name))

   return render(request, 'word_list.html', {
      'lang_id': lang_id,
      'page_obj': page_obj,
      'sources_by_category': sources_by_category
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
   language = get_object_or_404(Language, pk=lang_id)
   word = get_object_or_404(Word, pk=word_id)

   return render(request, 'word_details.html', {
      'lang_id': lang_id,
      'word': word
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