from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Applserv)
admin.site.register(NameOptions)
admin.site.register(User)
admin.site.register(VotingRes)