from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Applserv)
admin.site.register(NameOptions)
admin.site.register(Results)
admin.site.register(Users)
admin.site.register(VotingRes)