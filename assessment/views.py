from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, StreamingHttpResponse, HttpResponse
from django.urls import reverse
from .models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import datetime
import csv
import xlwt


from .forms import TesterForm

def seconds(time):
    return int((time - timezone.make_aware(datetime(2018, 1, 1))).total_seconds())

@login_required
def index(request):
    if 'responseid' in request.session:
        response = Response.objects.get(pk=request.session['responseid'])
        if response.is_finished is False:
            return HttpResponseRedirect(reverse('assessment:test', args=(1,)))
    exams = None
    if hasattr(request.user.testee, 'group'):
        testee = request.user.testee
        exams = Exam.objects.filter(groups=testee.group,
                                    start__lt=timezone.now(),
                                    deadline__gt=timezone.now()).order_by('start')
        exams_with_no_response = exams.exclude(response__in=Response.objects.filter(testee=testee))
        categories = testee.group.category.filter(language=testee.language)
        if len(categories) == 0:
            return render(request, 'index.html', {'error': 404}) #"Foydalanuvchi tiliga mos imtihonlar topilmadi"
    return render(request, 'index.html', {'exams':exams_with_no_response,
                                          'categories':categories,})


@login_required
def start(request):
    if 'responseid' in request.session:
        response = Response.objects.get(pk=request.session['responseid'])
        if response.is_finished is False:
            return HttpResponseRedirect(reverse('assessment:test', args=(1,)))
    testee = request.user.testee
    question_set = testee.group.random_questions(testee.language)
    exam   = Exam.objects.get(pk=request.POST.get("examid"))
    response = Response.objects.create(start_time=timezone.now(), testee=testee,
                                       exam=exam)
    response.questions.set(question_set)
    request.session['responseid'] = response.pk
    end_time = seconds(timezone.now() + exam.test_time)
    request.session['end_time']   = end_time
    request.session.set_expiry(end_time+600)
    return HttpResponseRedirect(reverse('assessment:test', args=(1,)))


@login_required
def test(request, question_no):
    if 'end_time' not in request.session:
        return HttpResponseRedirect(reverse('assessment:index'))
    end_time     = request.session['end_time']
    seconds_left = end_time - seconds(timezone.now())
    if seconds_left<0:
        return HttpResponseRedirect(reverse('assessment:confirm')) # time out

    response_id   = request.session.get('responseid', None)
    response      = Response.objects.get(pk=response_id)
    if response.is_finished:
        return HttpResponseRedirect(reverse('assessment:finish'))
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
    return render(request, 'test.html', {'title':'{}-savol'.format(question_no),
                                         'time_left': seconds_left,
                                         'test_time': int(response.exam.test_time.total_seconds()),
                                         'question':question,
                                         'questions': question_set,
                                         'prev': question_no-1,
                                         'question_no': question_no,
                                         'next':question_no+1 if question_no != question_count else None,
                                         'choosen': choosen,
                                         'type':type,})


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
            return HttpResponseRedirect(reverse('assessment:test', args=(question_no,)))
        else:
            return HttpResponseRedirect(reverse('assessment:confirm'))


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
    return render(request, 'confirm.html', {'title':'Testni tasdiqlash',
                                            'question_set':question_set,})


@login_required
def finish(request):
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    mark     = response.get_mark()
    total_mark = response.max_mark()
    mark_percent = '{}%'.format(mark*100//total_mark)
    if response.is_finished == False:
        response.is_finished = True
        response.end_time = timezone.now()
        response.save()
    time_spent = "{}:{}:{}".format(int((response.end_time-response.start_time).total_seconds()//3600), int((response.end_time-response.start_time).total_seconds()//60%60), int((response.end_time-response.start_time).total_seconds()%60))
    start      = timezone.make_naive(response.start_time)
    test_day   = start.strftime('%d-%B, %Y-yil')
    start_time = start.strftime('%-H:%M:%S')
    end_time   = timezone.make_naive(response.end_time).strftime('%-H:%M:%S')
    choices  = response.choices.all()
    questions= response.questions.all()
    # max_marks = [question.choice_set.aggregate(Max('mark')) for question in questions]
    # total_mark= sum(max_marks)
    question_set = []
    for question in questions:
        question_set += [{
            'text': question.text,
            'choice': choices.filter(question=question)
        }]
    # del request.session['responseid']
    # del request.session['end_time']
    return render(request, 'finish.html', {'title':'Test natijasi',
                                           'mark':mark,
                                           'total_mark':total_mark,
                                           'mark_percent':mark_percent,
                                           'question_set':question_set,
                                           'response':response,
                                           'test_day':test_day,
                                           'start_time':start_time,
                                           'end_time':end_time,
                                           'time_spent':time_spent})


########################## Tester Zone ###############################
@login_required
def tester(request):
    if not request.user.has_perm('assessment.can_create_reports'):
        return render(request, 'tester.html', {'error': 403})  # No Permission Forbidden
    if request.method == 'POST':
        form = TesterForm(request.POST)
        if form.is_valid():
            responses = Response.objects
            if request.POST['exam']:
                responses = responses.filter(exam_id=request.POST['exam'])
            if request.POST['group']:
                responses = responses.filter(testee__group_id=request.POST['group'])
            if request.POST['branch']:
                responses = responses.filter(testee__branch_id=request.POST['branch'])

            if type(responses).__name__ == "Manager":
                responses = responses.all()
            if not responses.exists():
                return render(request, 'tester.html', {'form': form, 'error': 404})  # Hech nima topilmadi

            if request.POST['summarize'] == '1':   # Filial bo'yicha
                rows = summarize(Branch, responses)
            elif request.POST['summarize'] == '2': # Guruh bo'yicha
                rows = summarize(TesteeGroup, responses)
            else:
                rows = [['Ism Familiyasi', 'Imtihon kuni', 'Davomiyligi (daq)', 'Ball', "To'liq ball", 'Savollar soni', "Yo'nalish", 'Filial' ]]
                rows += [[response.testee.user.get_full_name(), timezone.make_naive(response.start_time),
                          response.get_test_time(), response.get_mark(), response.max_mark(),
                          response.questions.count(), getattr(response.testee.group, 'name', ''), getattr(response.testee.branch, 'name', '')] for response in responses]

            filename = "Test-"+timezone.now().strftime('%d.%m.%y')
            if 'csv' not in request.POST:
                return export_xls(rows, filename)
            else:
                return export_csv(rows, filename)
    else:
        form = TesterForm()

    return render(request, 'tester.html', {'form': form})

def summarize(Class, responses):
    if Class == Branch:
        str = "Filial"
        code= 'testee__branch'
    elif Class == TesteeGroup:
        str = "Guruh"
        code= 'testee__group'
    rows = [[str+' nomi', 'Minimum', "O'rtacha", 'Maksimum', "Testga sarflangan vaqt (o'rtacha)"]]
    for item in Class.objects.all():
        filtered = responses.filter(**{code:item})
        if filtered:
            marks = [r.get_mark() for r in filtered]
            average = sum(marks) / len(marks)
            max_mark = max(marks)
            min_mark = min(marks)
            test_times = [r.get_test_time() for r in filtered]
            test_time_aver = sum(test_times) / len(test_times)
            rows += [[item.name, min_mark, average, max_mark, test_time_aver]]
        else:
            rows += [[item.name, '-', '-', '-', '-']]
    return rows

class Echo:
    # An object that implements just the write method of the file-like interface
    def write(self, value):
        #Write the value by returning it, instead of storing in a buffer.
        return value

def export_xls(rows, filename):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="{}.xls"'.format(filename)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Imtihon Natijalari')

    # Sheet header, first row
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    for col_num in range(len(rows[0])):
        ws.write(0, col_num, rows[0][col_num], font_style)
    del rows[0]

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd.mm.yy'

    row_num = 1
    for row in rows:
        for col_num in range(len(row)):
            if col_num !=1:
                ws.write(row_num, col_num, row[col_num], font_style)
            else:
                ws.write(row_num, col_num, row[col_num], date_format)
        row_num += 1

    wb.save(response)
    return response

def export_csv(rows, filename):
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)
    return response