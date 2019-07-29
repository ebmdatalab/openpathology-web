from django.contrib import admin
from .models import Measure


@admin.register(Measure)
class MeasureAdmin(admin.ModelAdmin):
    pass
