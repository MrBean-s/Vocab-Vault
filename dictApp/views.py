from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .forms import LanguageForm
from .models import Language, Image
from django.contrib import messages
from django.db.models import ProtectedError
# Create your views here.


def start_screen(request):
	languages = Language.objects.select_related('image').all()
	remaining = len(languages) % 3

	return render(request, "start_page.html", {
		"languages": Language.objects.select_related('image').all(),
		"substract_len_mod3": -remaining,
		"twelve_mod3": round(12 / remaining if remaining > 0 else 12)
	})

def language_form(request, lang_id = None):

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
			'edit_lang_id': instance.id if instance is not None else 0
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



