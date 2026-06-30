import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .forms import *
from .models import Language, Image, Word, Source, Definition, Example
from django.contrib import messages
from django.db.models import ProtectedError
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt



def start_screen(request):
  languages = Language.objects.select_related('image').all()
  remaining = len(languages) % 3

  return render(request, "start_page.html", {
    "languages": Language.objects.select_related('image').all(),
    "substract_len_mod3": -remaining,
    "twelve_mod3": round(12 / remaining if remaining > 0 else 12)
  })

def language_form(request, lang_id=None):

  instance = get_object_or_404(Language, pk=lang_id) if lang_id else None

  if request.method == 'POST':
    print(f"lang_id : {lang_id}")
    form = LanguageForm(request.POST, request.FILES, instance=instance)
    if form.is_valid():			
      form.save()

      return redirect('languages')
  else:
    form = LanguageForm(instance=instance)
  return render(request, "forms/_language_form.html", 
    {
      "form": form,
      "is_edit" : instance is not None,
      'edit_lang_id': instance.id if instance else 0
    })

def languages(request):
  languages = Language.objects.select_related('image').all()
  return render(request, "languages.html", {"languages": languages})

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
    print(request.POST)
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

      return redirect(request.path)
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
      print(f"--- def_index {i} ---")
      for f in ex_fs.forms:
          print(f"  prefix={f.prefix}, instance={f.instance}")
      example_formsets.append(ex_fs)

  return render(request, 'word.html', {
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
  
  print(sources_by_category)

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