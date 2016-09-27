from django.contrib import admin
from .models import Server, Job

# Register your models here.
@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    pass

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    actions = ('run_job',)
    list_display = ['name', 'owner', 'is_submitted', 'is_completed']

    def run_job(self, request, queryset):
        def callback(obj):
            print('in callback', obj)
            obj.save()

        for obj in queryset:
            obj.run(callback=callback)
            obj.save()
    run_job.short_description = 'Run selected jobs on remote server'
