from django.contrib import admin

from .models import Game, Seat, GameLog


class SeatInline(admin.TabularInline):
    model = Seat


class GameLogInline(admin.TabularInline):
    model = GameLog
    readonly_fields = ('id', )
    fields = ('id', 'executor_id', 'command')


class GameAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['owner', 'name', 'seed']}),
        ('Game State',                  {'fields': ['phase', 'message', 'round', 'turn', 'last_applied_gamelog', 'action_seat', 'seats']}),
#        ('Date information',    {'fields': ['pub_date']}),
    ]
    inlines = [SeatInline, GameLogInline]
    list_display = ('name', 'owner', 'phase', 'round')
    readonly_fields = ('seed', 'phase', 'message', 'round', 'turn', 'last_applied_gamelog', 'action_seat', 'seats')
#    list_filter = ['pub_date']
#    search_fields = ['name']


class GameLogAdmin(admin.ModelAdmin):
    list_display = ('game', 'executor_id', 'command')


# Register your models here.
admin.site.register(Game, GameAdmin)
admin.site.register(GameLog, GameLogAdmin)
#admin.site.register(Choice)