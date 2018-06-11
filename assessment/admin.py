from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.forms import Textarea
from django.utils.html import format_html

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
    min_num = 1
    can_delete = False

class QuestionInline(admin.StackedInline):
    model = Response.questions.through
    verbose_name = "Tushgan savol"
    verbose_name_plural = "Tushgan savollar"

class ResponseAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    exclude = ('questions',)
    def result(self, obj):
        return format_html("<a href='/tester/result/{}'>Ko'rish</a>", obj.pk)
    result.allow_tags = True
    result.short_description = 'Natija'

    list_display = ('testee', 'start_time', 'end_time', 'get_mark', 'max_mark', 'result', 'exam')
    list_filter = ('testee__group', 'testee__branch', 'start_time', 'exam')
    search_fields = ['testee__group__name', 'testee__branch__name', 'testee__user__first_name', 'testee__user__last_name']



class UserAdmin(AuthUserAdmin):
    inlines = [TesteeInline]
    def get_testee_group(self, obj):
        return obj.testee.group
    get_testee_group.short_description =  "Guruh"
    get_testee_group.admin_order_field = 'testee__group'
    def get_testee_branch(self, obj):
        return obj.testee.branch
    get_testee_branch.short_description =  "Filial"
    get_testee_branch.admin_order_field = 'testee__branch'
    list_display = ('username', 'first_name', 'last_name',  'get_testee_branch', 'get_testee_group', 'is_staff')
    AuthUserAdmin.list_filter += ('testee__branch', 'testee__group',)
    AuthUserAdmin.search_fields += ( 'testee__branch', 'testee__group__name',)

admin.site.register(Question, QuestionAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(TesteeGroup, TesteeGroupAdmin)
# admin.site.register(Testee, TesteeAdmin)
admin.site.register(Response, ResponseAdmin)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


admin.site.register(Category)
admin.site.register(Branch)


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