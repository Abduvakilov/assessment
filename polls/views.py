from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Question, Choice, SelectedChoices, Testee, Response, Exam
from django.contrib.auth.decorators import login_required
from django.utils import timezone

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
    question_set = testee.group.random_questions()
    exam   = Exam.objects.get(pk=request.POST.get("examid"))
    response = Response.objects.create(start_time=timezone.now(), testee=testee,
                                       exam=exam)
    response.questions.set(question_set)
    request.session['responseid'] = response.pk
    return HttpResponseRedirect(reverse('test'))

@login_required
def test(request):
    if 'question_no' not in request.session:
        request.session['question_no'] = 0
    question_no   = request.session['question_no']
    response_id   = request.session.get('responseid', None)
    next_question = Response.objects.get(pk=response_id).questions.all()[question_no]
    type          = "checkbox" if next_question.is_multiple_choice else "radio"
    return render(request, 'test.html', {'question':next_question, 'type':type})


@login_required
def choose(request):
    question_no   = request.session['question_no']
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    choices = request.POST.getlist('choice')
    if len(choices) == 0:
        return render(request, 'test.html', {
            'error_message': 'Javob tanlanmadi',
        })
    else:
        selectid = request.session.get('selectid', None)
        if selectid is None:
            sc = SelectedChoices.objects.create(testee=request.user.testee,
                                                response=response)
            request.session['selectid'] = sc.pk
        else:
            sc = SelectedChoices.objects.get(pk=selectid)
        for choice in choices:
            c = get_object_or_404(Choice, id=choice)
            sc.choices.add(c)
        if question_no<response.questions.all().count()-1:
            request.session['question_no'] += 1
            return HttpResponseRedirect(reverse('test'))
        else:
            response.end_time = timezone.now()
            response.save()
            return HttpResponseRedirect(reverse('finish'))


@login_required
def finish(request):
    return render(request, 'finish.html')
