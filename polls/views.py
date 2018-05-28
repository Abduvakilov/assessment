from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum

def seconds(time):
    return int((time.replace(tzinfo=None) - datetime(2018, 1, 1)).total_seconds())

@login_required
def index(request):
    if 'end_time' in request.session and request.session['end_time']>seconds(timezone.now()):
        return HttpResponseRedirect(reverse('test', args=(1,)))
    exams = None
    if hasattr(request.user.testee, 'group'):
        group = request.user.testee.group
        exams = Exam.objects.filter(groups=group,
                                    start__lt=timezone.now(),
                                    deadline__gt=timezone.now()).order_by('start')
        # for idx, val in enumerate(exams):
        #     test_time = exams[idx].test_time.total_seconds()
        #     exams[idx]['hours']   = (test_time / 3600)
        #     exams[idx]['minutes'] = (test_time / 60) % 60
    return render(request, 'index.html', {'exams':exams})


@login_required
def start(request):
    if 'end_time' in request.session and request.session['end_time']>seconds(timezone.now()):
        return HttpResponseRedirect(reverse('test'))
    testee = request.user.testee
    question_set = testee.group.random_questions()
    exam   = Exam.objects.get(pk=request.POST.get("examid"))
    response = Response.objects.create(start_time=timezone.now(), testee=testee,
                                       exam=exam)
    response.questions.set(question_set)
    request.session['responseid'] = response.pk
    end_time = seconds(timezone.now()+exam.test_time)
    request.session['end_time']   = end_time
    request.session.set_expiry(end_time+600)
    return HttpResponseRedirect(reverse('test', args=(1,)))

@login_required
def test(request, question_no):
    if 'end_time' not in request.session:
        return HttpResponseRedirect(reverse('index'))
    seconds_left = request.session['end_time'] - seconds(timezone.now())
    if seconds_left<0:
        return render(request, 'finish.html', {
            'error': 408, # time out
        })

    response_id   = request.session.get('responseid', None)
    response      = Response.objects.get(pk=response_id)
    if response.is_finished:
        return HttpResponseRedirect(reverse('finish'))
    if question_no is None:
        question_no = 1
    question_count= response.questions.count()
    question = response.questions.all()[question_no-1]
    type     = "checkbox" if question.is_multiple_choice else "radio"
    question_set = [False]*question_count
    sc = SelectedChoice.objects.filter(response=response)
    for c in sc:
        question_set[c.number-1] = True
    choosen = sc.filter(number=question_no).values_list('choice', flat=True)
    return render(request, 'test.html', {'time_left': seconds_left,
                                         'question':question,
                                         'questions': question_set,
                                         'prev': question_no-1,
                                         'question_no': question_no,
                                         'next':question_no+1 if question_no != question_count else None,
                                         'choosen': choosen,
                                         'type':type})


@login_required
def choose(request, question_no):
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    choices = request.POST.getlist('choice')
    if len(choices) == 0:
        return render(request, 'test.html', {
            'error_message': 'Javob tanlanmadi',
        })
    else:
        SelectedChoice.objects.filter(response=response, number=question_no).delete()
        for choice in choices:
            SelectedChoice.objects.create(number=question_no,
                                          response=response,
                                          choice_id=choice)
        if question_no<response.questions.count():
            question_no += 1
            return HttpResponseRedirect(reverse('test', args=(question_no,)))
        else:
            return HttpResponseRedirect(reverse('confirm'))


@login_required
def confirm(request):
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    choices  = response.choices.all()
    questions= response.questions.all()
    question_set = []
    for question in questions:
        question_set += [{
            'text': question.text,
            'choice': choices.filter(question=question).values_list('text', flat=True)
        }]
    return render(request, 'confirm.html', {'question_set':question_set,})


@login_required
def finish(request):
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    mark    =response.choices.aggregate(Sum('mark'))['mark__sum']
    response.is_finished = True
    response.end_time = timezone.now()
    response.save()
    del request.session['responseid']
    del request.session['end_time']
    return render(request, 'finish.html', {'mark':mark})


@login_required
def tester(request):
    return render(request, 'tester.html')
