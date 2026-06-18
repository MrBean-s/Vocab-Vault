from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .forms import LanguageForm
from .models import Language, Image
# Create your views here.
def dashboard(request, lang_id):
	return HttpResponse("<h1>Hello, World!</h1>", content_type="text/html")

def language_form(request, lang_id = None):

	instance = get_object_or_404(Language, pk=lang_id) if lang_id else None
	
	if request.method == 'POST':
		form = LanguageForm(request.POST, request.FILES, instance = instance)
		if form.is_valid():			
			form.save()

			return redirect('start_screen')
	else:
		form = LanguageForm(instance=instance)
	return render(request, "language_form.html", {"form": form, "is_edit" : instance is not None})




def start_screen(request):

	return render(request, "start_page.html", {"languages": Language.objects.select_related('image').all()})