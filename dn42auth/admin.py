from django.contrib import admin
from .models import DN42User


@admin.register(DN42User)
class DN42UserAdmin(admin.ModelAdmin):
    change_form_template = 'loginas/change_form.html'
