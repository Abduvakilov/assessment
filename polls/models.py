from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

class Category(models.Model):
    name           = models.CharField(max_length=127)
    question_count = models.PositiveSmallIntegerField()
    def random_questions(self):
        import random
        ids        = self.question_set.objects.values_list('id', flat=True)
        random_ids = random.sample(ids, min(len(ids), self.question_count))
        return Question.objects.filter(id__in=random_ids)
    def __str__(self):
        return self.name

class TesteeGroup(models.Model):
    name = models.CharField(max_length=255)
    category = models.ManyToManyField(Category)
    def random_questions(self):
        question_set = []
        for cat in self.category.all():
            question_set += cat.random_questions()
        return question_set
    def __str__(self):
        return self.name

class Exam(models.Model):
    groups   = models.ManyToManyField(TesteeGroup)
    start    = models.DateTimeField('Boshlanish vaqti', default=timezone.now)
    deadline = models.DateTimeField('Tugash vaqti')
    test_time     = models.TimeField('Test vaqti')
    def __str__(self):
        return self.start.strftime("%d %b %Y")

class Testee(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)
    group    = models.ForeignKey(TesteeGroup, on_delete=models.CASCADE)
    language = models.PositiveSmallIntegerField(choices=((0,'uz'),
                                                         (1,'ru'),
                                                         (2,'en')),
                                                default=0)
    def __str__(self):
        return self.user.username

class Question(models.Model):
    text     = models.CharField(max_length=255)
    text_ru  = models.CharField(max_length=255)
    text_en  = models.CharField(max_length=255)
    pub_date = models.DateTimeField('Sana', auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_multiple_choice = models.BooleanField(default=False)
    def __str__(self):
        return self.text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text     = models.CharField(max_length=255)
    text_ru  = models.CharField(max_length=255)
    text_en  = models.CharField(max_length=255)
    mark     = models.PositiveSmallIntegerField(default=0)
    def __str__(self):
        return self.text

class Response(models.Model):
    start_time   = models.DateTimeField("Test Boshlangan Vaqt", auto_now=True)
    end_time     = models.DateTimeField('Tugallangan vaqt', null=True)
    is_finished  = models.BooleanField(default=False)
    testee       = models.ForeignKey(Testee, on_delete=models.CASCADE)
    exam         = models.ForeignKey(Exam, on_delete=models.CASCADE)
    questions    = models.ManyToManyField(Question)
    def __str__(self):
        return self.testee.user.username+"'s response"

class SelectedChoices(models.Model):
    choices  = models.ManyToManyField(Choice)
    testee   = models.ForeignKey(Testee, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    def __str__(self):
        return self.testee.user.username
