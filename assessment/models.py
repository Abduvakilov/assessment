from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max

class Category(models.Model):
    name           = models.CharField(max_length=127)
    question_count = models.PositiveSmallIntegerField()
    language = models.PositiveSmallIntegerField(choices=((0, 'uz'),
                                                         (1, 'ru'),
                                                         (2, 'en')),
                                                default=0)
    def random_questions(self):
        import random
        ids        = [id for id in self.question_set.filter(is_active=True).values_list('pk', flat=True)]
        random_ids = random.sample(ids, min(len(ids), self.question_count))
        return Question.objects.filter(id__in=random_ids)
    def __str__(self):
        return self.name

class TesteeGroup(models.Model):
    name = models.CharField(max_length=255)
    category = models.ManyToManyField(Category)
    def random_questions(self, lang):
        question_set = []
        for cat in self.category.filter(language=lang):
            question_set += cat.random_questions()
        return question_set
    def __str__(self):
        return self.name

class Exam(models.Model):
    groups   = models.ManyToManyField(TesteeGroup)
    start    = models.DateTimeField('Boshlanish vaqti', default=timezone.now)
    deadline = models.DateTimeField('Tugash vaqti')
    test_time= models.DurationField('Test davomiyligi (soat:daqiqa:soniya)')
    one_time  = models.BooleanField('Faqat bir marotaba topshiriladi', default=True)
    description=models.TextField("Test tarifi", max_length=512, null=True, blank=True)
    def __str__(self):
        return self.start.strftime("%d %b %Y")

class Testee(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)
    ask_name  = models.BooleanField("Har safar ism So'ralsin", default=False)
    group    = models.ForeignKey(TesteeGroup, on_delete=models.SET_NULL, null=True)
    language = models.PositiveSmallIntegerField(choices=((0,'uz'),
                                                         (1,'ru'),
                                                         (2,'en')),
                                                default=0)
    def __str__(self):
        return self.user.username

class Question(models.Model):
    text     = models.TextField(max_length=500)
    image    = models.ImageField(upload_to="images", null=True, blank=True)
    pub_date = models.DateTimeField('Sana', auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    is_multiple_choice = models.BooleanField('Muliple choice',default=False)
    is_active= models.BooleanField('Faol', default=True)
    def max_mark(self):
        return self.choice_set.aggregate(Max('mark'))['mark__max']
    max_mark.short_description = "Baho"
    def __str__(self):
        return self.text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text     = models.TextField(max_length=500)
    mark     = models.SmallIntegerField(default=0)
    def __str__(self):
        return self.text

class Response(models.Model):
    start_time  = models.DateTimeField("Test Boshlangan Vaqt", default=timezone.now)
    end_time    = models.DateTimeField('Tugallangan vaqt', null=True)
    is_finished = models.BooleanField(default=False)
    testee      = models.ForeignKey(Testee, on_delete=models.CASCADE)
    exam        = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True)
    questions   = models.ManyToManyField(Question)
    choices     = models.ManyToManyField(Choice, through='SelectedChoice')
    def __str__(self):
        return self.testee.user.username+"'s response"

class SelectedChoice(models.Model):
    time     = models.DateTimeField('Vaqt', default=timezone.now)
    number   = models.PositiveSmallIntegerField()
    choice   = models.ForeignKey(Choice, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.choice.text
