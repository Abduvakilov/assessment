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
        return HttpResponseRedirect(reverse('test'))
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
    return HttpResponseRedirect(reverse('test'))

@login_required
def test(request):
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
    if 'question_no' not in request.session:
        request.session['question_no'] = 0
    question_no   = request.session['question_no']
    next_question = response.questions.all()[question_no]
    type          = "checkbox" if next_question.is_multiple_choice else "radio"
    return render(request, 'test.html', {'time_left': seconds_left,
                                         'question':next_question,
                                         'question_no': question_no+1,
                                         'type':type})


@login_required
def choose(request):
    question_no   = request.session.get('question_no', None)
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    choices = request.POST.getlist('choice')
    if len(choices) == 0:
        return render(request, 'test.html', {
            'error_message': 'Javob tanlanmadi',
        })
    else:
        for choice in choices:
            SelectedChoice.objects.create(testee=request.user.testee,
                                          response=response,
                                          choice_id=choice)
        if question_no<response.questions.count()-1:
            request.session['question_no'] += 1
            return HttpResponseRedirect(reverse('test'))
        else:
            response.end_time = timezone.now()
            response.save()
            return HttpResponseRedirect(reverse('finish'))


@login_required
def finish(request):
    question_no   = request.session.get('question_no', None)
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    if question_no>=response.questions.count()-1:
        mark    =response.choices.aggregate(Sum('mark'))['mark__sum']
        response.is_finished = True
        response.save()
        del request.session['question_no']
        del request.session['responseid']
        del request.session['end_time']
        return render(request, 'finish.html', {'mark':mark})
    else:
        return HttpResponseRedirect(reverse('test'))

@login_required
def tester(request):
    return render(request, 'tester.html')


