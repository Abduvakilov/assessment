from django import forms
from .models import *

class ReportForm(forms.Form):
    exam     = forms.ModelChoiceField(label='Imtihon:', queryset=Exam.objects.all().order_by('start'), required=False)
    branch   = forms.ModelChoiceField(label='Filial:', queryset=Branch.objects.all().order_by('name'), required=False)
    group    = forms.ModelChoiceField(label="Guruh:", queryset=TesteeGroup.objects.all().order_by('name'), required=False)
    summarize= forms.ChoiceField(label='Umumlashtirish:', choices=((0, "---------"),
                                                                  (1, "Filial bo'yicha"),
                                                                  (2, "Yo'nalish bo'yicha")),
                                 required=False)
    csv    = forms.BooleanField(required=False)

class BranchAndGroupForm(forms.Form):
    branch = forms.ModelChoiceField(label='Filial:', queryset=Branch.objects.all().order_by('name'), required=False)
    group    = forms.ModelChoiceField(label="Guruh:", queryset=TesteeGroup.objects.all().order_by('name'), required=False)

class GroupReplaceForm(forms.Form):
    group    = forms.ModelChoiceField(label="Guruh:", queryset=TesteeGroup.objects.all().order_by('name'), required=False)
    delete_group= forms.BooleanField(label="Ko'chirilganidan keyin o'chirib tashlansin", required=False)