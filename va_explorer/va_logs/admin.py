from django.contrib import admin
from .models import VerbalAutopsy, Location, CauseOfDeath

# Register your models here.
admin.site.register(VerbalAutopsy)
admin.site.register(Location)
admin.site.register(CauseOfDeath)
