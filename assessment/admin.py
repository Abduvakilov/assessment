from django.contrib import admin
from django.apps import apps
from .models import *
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.forms import TextInput, Textarea

class ChoiceInline(admin.TabularInline):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    model = Choice
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':100})},
    }
    fieldsets = [
        (None,               {'fields': ['text','category']}),
        ('Boshqa', {'fields': ['image', 'is_multiple_choice', 'is_active'], 'classes': ['collapse']}),
    ]
    inlines = [ChoiceInline]
    list_display = ('text', 'category', 'pub_date', 'max_mark', 'is_active', 'is_multiple_choice')
    list_filter = ['category', 'pub_date', 'is_active', 'is_multiple_choice']
    search_fields = ['text']


class ExamInline(admin.TabularInline):
    model = Exam.groups.through
    verbose_name = "Imtihon topshiruvchi"
    verbose_name_plural = "Imtihon topshiruvchilar"

class ExamAdmin(admin.ModelAdmin):
    inlines = [ExamInline]
    fieldsets = [
        ('Vaqti', {'fields': ['start', 'deadline', 'test_time', 'one_time']}),
    ]
    list_display = ('start', 'deadline', 'test_time', 'one_time')
    list_filter = ['start', 'deadline']

class TesteeGroupInline(admin.TabularInline):
    model = TesteeGroup.category.through
    verbose_name_plural = "Imtihon topshiruvchilar uchun belgilangan savollar"

class TesteeGroupAdmin(admin.ModelAdmin):
    inlines = [TesteeGroupInline]
    list_display = ('name', 'get_categories')
    list_filter = ['name', 'category']
    def get_categories(self, obj):
        return ", ".join([p.name for p in obj.category.all()])
    get_categories.short_description = "Savol Toifalari"
    exclude = ('category',)

class TesteeInline(admin.StackedInline):
    model = Testee
    max_num = 1
    can_delete = False

class UserAdmin(AuthUserAdmin):
    inlines = [TesteeInline]
    def get_testee_group(self, obj):
        return obj.testee.group
    get_testee_group.short_description =  "Guruh"
    get_testee_group.admin_order_field = 'testee__group__name'
    list_display = ('username', 'first_name', 'last_name',  'get_testee_group', 'is_staff')
    AuthUserAdmin.list_filter += ('testee__group',)
    AuthUserAdmin.search_fields += ('testee__group__name',)

admin.site.register(Question, QuestionAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(TesteeGroup, TesteeGroupAdmin)
# admin.site.register(Testee, TesteeAdmin)
admin.site.register(Response)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


admin.site.register(Category)


# class TesteeAdmin(admin.ModelAdmin):
#     # inlines = [UserInline]
#     list_display = ('get_name', 'user', 'group', 'language')
#     list_filter = ['group', 'language']
#     def get_name(self, obj):
#         return obj.user.get_full_name()
#     get_name.short_description = "Ism Familiyasi"
#     get_name.admin_order_field = 'user__first_name'
#
#     search_fields = ['user__first_name', 'user__last_name']