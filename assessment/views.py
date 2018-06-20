from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, StreamingHttpResponse, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from .models import *
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
import csv
import xlwt
import random
from django.utils import translation
from django.utils.translation import gettext as _
from .forms import ReportForm

def seconds(time):
    return int((time - timezone.make_aware(datetime(2018, 1, 1))).total_seconds())

@login_required
def lang(request, language_id=None):
    if language_id is None:
        return render(request, 'lang.html', {'title' : _('Tilni Tanlang'),
                                             'languages' : languages})
    language = languages[language_id]
    translation.activate(language[1])
    request.session[translation.LANGUAGE_SESSION_KEY] = language[1]
    request.session['lang_code'] = language[0]
    return HttpResponseRedirect(reverse('assessment:index'))


@login_required
def index(request):
    if 'lang_code' not in request.session:
        return HttpResponseRedirect(reverse('assessment:lang'))
    if 'responseid' in request.session:
        response = Response.objects.get(pk=request.session['responseid'])
        if response.is_finished is False:
            return HttpResponseRedirect(reverse('assessment:test', args=(1,)))
    lang_code = request.session['lang_code']
    testee = request.user.testee
    exams = Exam.objects.filter(groups=testee.group,
                                start__lt=timezone.now(),
                                deadline__gt=timezone.now()).order_by('start')
    exams_with_no_response = exams.exclude(response__in=Response.objects.filter(testee=testee))
    categories = testee.group.category.filter(language=lang_code)
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
    lang_code = request.session['lang_code']
    question_set = testee.group.random_questions(lang_code)
    exam   = Exam.objects.get(pk=request.POST.get("examid"))
    response = Response.objects.create(start_time=timezone.now(), testee=testee,
                                       exam=exam)
    response.questions.set(question_set)
    request.session['responseid'] = response.pk
    end_time = seconds(timezone.now() + exam.test_time)
    request.session['end_time'] = end_time
    nums = list(range(10))
    random.shuffle(nums)
    request.session['random'] = nums # 10 is taken as maximum number of choices to shuffle
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
    choices = question.choice_set.all()
    random = request.session['random'][:choices.count()]
    choices = [x for _, x in sorted(zip(random, list(choices)))]
    return render(request, 'test.html', {'title' : _('{}-savol').format(question_no),
                                         'time_left' : seconds_left,
                                         'test_time' : int(response.exam.test_time.total_seconds()),
                                         'question' :question,
                                         'choices' : choices,
                                         'questions' : question_set,
                                         'prev' : question_no-1,
                                         'question_no' : question_no,
                                         'next' : question_no+1 if question_no != question_count else None,
                                         'choosen' : choosen,
                                         'type' : type,})


@login_required
def choose(request, question_no):
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    choices = request.POST.getlist('choice')
    if len(choices) == 0:
        return render(request, 'test.html', {
            'error_message': _('Javob tanlanmadi'),
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
    end_time     = request.session['end_time']
    seconds_left = end_time - seconds(timezone.now())
    questions= response.questions.all()
    questions_missed = []
    for number, question in enumerate(questions):
        choice = choices.filter(question=question)
        if not choice.exists():
            questions_missed += [{
                'number' : number+1,
                'text' : question.text,
                'choice' : choice.values_list('text', flat=True)
            }]
    return render(request, 'confirm.html', {'title': _('Testni yakunlash'),
                                            'time_left' : seconds_left,
                                            'test_time' : int(response.exam.test_time.total_seconds()),
                                            'questions_missed' : questions_missed,})


@login_required
def finish(request):
    response_id   = request.session.get('responseid', None)
    response = get_object_or_404(Response, id=response_id)
    mark_percent = '{}%'.format(response.get_mark()*100//response.max_mark())
    if response.is_finished == False:
        response.is_finished = True
        response.end_time = timezone.now()
        response.save()
    time_spent = "{}:{}:{}".format(int((response.end_time-response.start_time).total_seconds()//3600), int((response.end_time-response.start_time).total_seconds()//60%60), int((response.end_time-response.start_time).total_seconds()%60))
    start      = timezone.make_naive(response.start_time)
    test_day   = start.strftime(_('%d-%B, %Y-yil'))
    start_time = start.strftime('%-H:%M:%S')
    end_time   = timezone.make_naive(response.end_time).strftime('%-H:%M:%S')

    return render(request, 'finish.html', {'title': _('Test natijasi'),
                                           'mark_percent' : mark_percent,
                                           'response' : response,
                                           'categories' : response.testee.group.category.filter(language=response.language),
                                           'test_day' : test_day,
                                           'start_time' : start_time,
                                           'end_time': end_time,
                                           'time_spent' : time_spent})



########################## Tester Zone ###############################
@login_required
def tester(request):
    error = None
    if not request.user.is_staff:
        error = 403 # No Permission Forbidden
    return render(request, 'tester.html', {'title' : _('Tester Zone'),'error': error})


@login_required
def import_questions(request):
    title = "Savollarni fayl ko'rinishida kiritish"
    def response_with_error(error):
        return render(request, 'import.html', {'title': title,
                                               'categories_available' : categories_available,
                                               'error': error})
    if not request.user.is_staff:
        return response_with_error("Ruhsat yo'q") # Forbidden
    success = False
    categories_available = Category.objects.values_list('name', flat=True)
    if request.method == 'POST':
        if 'txt' not in request.FILES['file'].name:
            return response_with_error("Faqat .txt formatidagi fayl yuklanishi mumkin")   # wrong extension

        # try:
        txt_to_import = request.FILES['file'].read().decode('cp1251')
        rows = [x.strip() for x in txt_to_import.split("\n") if x.strip()]
        categories = [x[1:].strip() for x in rows if x.startswith("?")] # Get category line and cut ? mark
        categories_found = Category.objects.filter(name__in=categories)
        if len(categories) == 0:
            return response_with_error("Savollar toifalari to'g'ri kiritilganinga ishonch xosil qiling") # Categories not found
        if len(categories) != len(categories_found):
            return response_with_error("Savollar toifalari to'g'ri kiritilganinga ishonch xosil qiling") # Categories not found

        print(rows)
        category_no = -1 # negative to make zero after increment
        question_no = -1
        question_started = False
        question_list = []
        def create_choice(row, mark):
            global question_started
            if question_started:
                question_started = False
                question_list[question_no].save()
            Choice.objects.create(question=question_list[question_no],
                                  text=row[1:].strip(),
                                  mark=mark)
        for row in rows:
            global question_started
            if row.startswith('-'):
                create_choice(row, 0)
            elif row.startswith('+'):
                create_choice(row, 1)
            elif row.startswith('?'):
                category_no += 1
                category = categories_found[category_no]
                print(category_no)
                print(question_no)
            elif not question_started:
                question_no += 1
                question_started = True
                question_list.append( Question(text=row,
                                               category=category) )
            else:
                question_list[question_no].text += "\n"+row
        success = True
        # except:
        #     return response_with_error("Savollar qolif bo'yicha kiritilganinga ishanch xosil qiling")
    return render(request, 'import.html', {'title': title,
                                           'categories_available': categories_available,
                                           'success' : success})


@login_required
def result(request, response_id):
    language = languages[0][1]
    translation.activate(language)
    request.session[translation.LANGUAGE_SESSION_KEY] = language

    if not request.user.is_staff:
        return HttpResponseForbidden(_("Ruhsat yo'q"))  # No Permission Forbidden

    response = get_object_or_404(Response, id=response_id)
    mark_percent = '{}%'.format(response.get_mark()*100//response.max_mark())
    start      = timezone.make_naive(response.start_time)
    test_day   = start.strftime(_('%d-%B, %Y-yil'))
    start_time = start.strftime('%-H:%M:%S')
    if response.end_time:
        end_time   = timezone.make_naive(response.end_time).strftime('%-H:%M:%S')
    else:
        end_time = start + response.exam.test_time
    question_set = []
    for question in response.questions.all():
        question_set += [{
            'text': question.text,
            'choice': response.choices.filter(question=question)
        }]

    return render(request, 'result.html', {'title' : _('Imtihon Natijalari'),
                                           'mark_percent' : mark_percent,
                                           'question_set' : question_set,
                                           'response' : response,
                                           'categories' : response.testee.group.category.filter(language=response.language),
                                           'test_day':test_day,
                                           'start_time':start_time,
                                           'end_time':end_time,})


@login_required
def report(request):
    if  not request.user.is_staff:
        return render(request, 'report.html', {'error': 403})  # No Permission Forbidden
    if request.method == 'POST':
        form = ReportForm(request.POST)
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
                return render(request, 'report.html', {'form': form, 'error': 404})  # Hech nima topilmadi

            if request.POST['summarize'] == '1':   # Filial bo'yicha
                rows = summarize(Branch, responses)
            elif request.POST['summarize'] == '2': # Guruh bo'yicha
                rows = summarize(TesteeGroup, responses)
            else:
                rows = [[_('Ism Familiyasi'), _('Imtihon kuni'), _('Davomiyligi (daq)'), _('Ball'), _("To'liq ball"), _('Savollar soni'), _("Yo'nalish"), _('Filial') ]]
                rows += [[response.testee.user.get_full_name(), timezone.make_naive(response.start_time),
                          response.get_test_time(), response.get_mark(), response.max_mark(),
                          response.questions.count(), getattr(response.testee.group, 'name', ''), getattr(response.testee.branch, 'name', '')] for response in responses]

            filename = "Test-"+timezone.now().strftime('%d.%m.%y')
            if 'csv' not in request.POST:
                return export_xls(rows, filename, bool(request.POST['summarize']))
            else:
                return export_csv(rows, filename)
    else:
        form = ReportForm()

    return render(request, 'report.html', {'form': form})

def summarize(Class, responses):
    if Class == Branch:
        str = _("Filial nomi")
        code= 'testee__branch'
    else:
        str = _("Guruh nomi")
        code= 'testee__group'
    rows = [[str, _('Minimum'), _("O'rtacha"), _('Maksimum'), _("Testga sarflangan vaqt (o'rtacha)")]]
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

def export_xls(rows, filename, is_summary):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="{}.xls"'.format(filename)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(_('Imtihon Natijalari'))

    # Sheet header, first row
    body_format = xlwt.XFStyle()
    body_format.font.bold = True
    for col_num in range(len(rows[0])):
        ws.write(0, col_num, rows[0][col_num], body_format)
    del rows[0]

    # Sheet body, remaining rows
    body_format.font.bold = False
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd.mm.yy'

    def get_type(col_num):
        if is_summary:
            return body_format
        if col_num == 1:
            return date_format
        return body_format
    row_num = 1
    for row in rows:
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], get_type(col_num))
        row_num += 1

    wb.save(response)
    return response

class Echo:
    # An object that implements just the write method of the file-like interface
    def write(self, value):
        #Write the value by returning it, instead of storing in a buffer.
        return value

def export_csv(rows, filename):
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)
    return response