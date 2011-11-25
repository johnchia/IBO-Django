from ibo.models import ParametricArtProblem,BanditContext,PairedComparison
from django.contrib import admin

class ParametricArtProblemAdmin(admin.ModelAdmin):
    # ...
    list_display = ('description','parameters','xp', 'yp')

admin.site.register(ParametricArtProblem, ParametricArtProblemAdmin)

class BanditContextAdmin(admin.ModelAdmin):
    # ...
    list_display = ('id','dimension', 'vector')

admin.site.register(BanditContext, BanditContextAdmin)

class PairedComparisonAdmin(admin.ModelAdmin):
    # ...
    list_display = ('date','preferred_context','unpreferred_context')
admin.site.register(PairedComparison, PairedComparisonAdmin)
