from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max, Sum
from django.utils.translation import gettext_lazy as _

languages = [(0, 'uz', "Узбекча"),
             (1, 'ru', "Русский"),
             # (2, 'en', "English")
             ]
language_coice = [(x, z) for x, y, z in languages]

class Branch(models.Model):
    name = models.CharField(_('Filial nomi'), max_length=127)
    code = models.PositiveSmallIntegerField(_("Filial kodi"))
    def __str__(self):
        return str(self.code) + ' ' + self.name
    class Meta:
        verbose_name = _("Filial")
        verbose_name_plural = _("Filiallar")

class Category(models.Model):
    name           = models.CharField(_("Guruh Nomi"),max_length=127)
    question_count = models.PositiveSmallIntegerField(_("Savollar soni"))
    language       = models.PositiveSmallIntegerField(_("Savollar tili"), choices=language_coice,
                                                      default=0)
    def random_questions(self):
        import random
        ids        = [id for id in self.question_set.filter(is_active=True).values_list('pk', flat=True)]
        random_ids = random.sample(ids, min(len(ids), self.question_count))
        return Question.objects.filter(id__in=random_ids)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = _("Savol Toifasi")
        verbose_name_plural = _("Savol Toifalari")

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
    class Meta:
        verbose_name = "Test topshiruvchilar guruhi"
        verbose_name_plural = "Test topshiruvchilar guruhlari"

class Exam(models.Model):
    groups   = models.ManyToManyField(TesteeGroup)
    start    = models.DateTimeField('Boshlanish vaqti', default=timezone.now)
    deadline = models.DateTimeField('Tugash vaqti')
    test_time= models.DurationField('Test davomiyligi (soat:daqiqa:soniya)')
    one_time  = models.BooleanField('Faqat bir marotaba topshiriladi', default=True)
    description=models.TextField("Test tarifi", max_length=512, null=True, blank=True)
    def __str__(self):
        return self.start.strftime("%d %b %Y")+" - "+", ".join(self.groups.values_list('name', flat=True)[:3])
    class Meta:
        verbose_name = "Imtihon"
        verbose_name_plural = "Imtihonlar"

class Testee(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)
    ask_name = models.BooleanField("Har safar ism So'ralsin", default=False)
    group    = models.ForeignKey(TesteeGroup, on_delete=models.SET_NULL, null=True)
    branch   = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.user.get_full_name()
    class Meta:
        verbose_name = "Test topshiruvchi"
        verbose_name_plural = "Test topshiruvchilar"

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
    class Meta:
        verbose_name = "Test Savoli"
        verbose_name_plural = "Test savollari"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text     = models.TextField(max_length=500)
    mark     = models.SmallIntegerField(default=0)
    def __str__(self):
        return self.text
    class Meta:
        verbose_name = "Variant"
        verbose_name_plural = "Variantlar"

class Response(models.Model):
    testee      = models.ForeignKey(Testee, on_delete=models.CASCADE)
    start_time  = models.DateTimeField(_("Test Boshlangan Vaqt"), default=timezone.now)
    end_time    = models.DateTimeField('Tugallangan vaqt', null=True)
    is_finished = models.BooleanField(default=False)
    exam        = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True)
    questions   = models.ManyToManyField(Question)
    choices     = models.ManyToManyField(Choice, through='SelectedChoice')
    language    = models.PositiveSmallIntegerField(choices=language_coice,
                                                   default=0)

    def get_mark(self):
        return self.choices.aggregate(Sum('mark'))['mark__sum'] or 0
    get_mark.short_description = "Baho"
    def max_mark(self):
        return  self.questions.annotate(Max('choice__mark')).aggregate(Sum('choice__mark__max'))['choice__mark__max__sum']
    max_mark.short_description = "To'liq baho"
    def get_test_time(self):
        if self.end_time is not None:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return round(self.exam.test_time.total_seconds() / 60, 2)
    get_test_time.short_description = 'Sarflangan Vaqt (daqiqa)'
    def __str__(self):
        return self.testee.user.get_full_name() +"ning javobi"



    class Meta:
        verbose_name = "Topshirilgan javob"
        verbose_name_plural = "Topshirilgan javoblar"
        permissions = (
            ("can_create_reports", "Can create reports"),
        )

class SelectedChoice(models.Model):
    time     = models.DateTimeField('Vaqt', default=timezone.now)
    number   = models.PositiveSmallIntegerField()
    choice   = models.ForeignKey(Choice, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.choice.text
    class Meta:
        verbose_name = "Tanlangan javob"
        verbose_name_plural = "Tanlangan javoblar"
