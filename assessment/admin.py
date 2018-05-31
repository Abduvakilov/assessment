from django.contrib import admin
from django.apps import apps
# from .models import Question, Category, Choice, SelectedChoices, Exam, GroupCategories, Response, TesteeGroup

app = apps.get_app_config('assessment')

for model_name, model in app.models.items():
    admin.site.register(model)

# admin.site.register(Question)
# admin.site.register(Category)
# admin.site.register(Choice)
# admin.site.register(SelectedChoices)
# admin.site.register(Exam)
# admin.site.register(GroupCategories)
# admin.site.register(TesteeGroup)
# admin.site.register(Response)
# admin.site.register(Response)
# admin.site.register(Response)