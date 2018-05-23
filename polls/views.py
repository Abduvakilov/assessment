from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Question, Choice, SelectedChoices, Testee, Response, Exam
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta, time

@login_required
def index(request):
    exams = None
    if hasattr(request.user.testee, 'group'):
        group = request.user.testee.group
        exams = Exam.objects.filter(groups=group,
                                    start__lt=timezone.now(),
                                    deadline__gt=timezone.now()).order_by('start')
    return render(request, 'index.html', {'exams':exams})


@login_required
def start(request):
    testee = request.user.testee
    question_set = testee.group.random_questions
    exam   = Exam.objects.get(pk=request.POST.get("examid"))
    Response.objects.create(start_time=timezone.now(), testee=testee,
                                       exam=exam, question=question_set)
    return HttpResponseRedirect(reverse('test'))

@login_required
def test(request, question_no):
    question =
    type     = "checkbox" if question.is_multiple_choice else "radio"
    return render(request, 'test.html', {'question':question, 'type':type})


@login_required
def choose(request, question_no):
    question = get_object_or_404(Question, id=question_no)
    choices = request.POST.getlist('choice')
    if len(choices) == 0:
        return render(request, 'test.html', {
            'error_message': 'Javob tanlanmadi',
        })
    else:
        selected_choice = []
        for choice in choices:
            c = get_object_or_404(Choice, id=choice)
            selected_choice += [SelectedChoices(testee=request.user.testee,
                                                choices=c,
                                                response=Response.objects.filter(testee=request.user.testee).latest('pk'))]
        return HttpResponseRedirect(reverse('detail', args=(question.id+1,)))
