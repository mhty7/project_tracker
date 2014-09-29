from django.contrib import admin
from ngo.apps.board.models import Activity,Beneficiary

class Beneficiary_Inline(admin.TabularInline):
    model = Beneficiary.activity.through

class Activity_admin(admin.ModelAdmin):
    list_filter = ('activity_ty','user')
    search_fields = ['description','activity_ty', 'user__username']
    inlines = [Beneficiary_Inline,]
    readonly_fields = ['fdate','tdate',]



class Beneficiary_admin(admin.ModelAdmin):
    list_filter = ('ty','user')
    search_fields = ['fname','lname','ty', 'user__username']
    filter_horizontal = ('activity',)
    exclude=('activity',)
    

admin.site.register(Activity,Activity_admin)
admin.site.register(Beneficiary,Beneficiary_admin)