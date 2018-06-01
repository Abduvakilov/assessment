from django.shortcuts import render

def user(request):

    return render(request, 'users.html')


def question_answer(request):
    pass

def question_category(request):
    pass