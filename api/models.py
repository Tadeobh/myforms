from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Form model
class Form(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=511)

    def update_date_updated(self):
        self.date_updated = timezone.now()
        self.save(update_fields=['date_updated'])

    def __str__(self) -> str:
        return f"<Form {self.created_by} {self.pk}>"


# Response model
class Response(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    
    def __str__(self) -> str:
        return f"<Response {self.created_by} {self.pk}>"


# Question model
class Question(models.Model):
    text = models.CharField(max_length=255, default="New Question")
    type = models.CharField(max_length=10, choices=[
        ('text', 'Text'),
        ('select', 'Select one'),
        ('multiple', 'Multiple Choice'),
    ])
    form = models.ForeignKey(Form, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"<Question {self.pk} from Form {self.form.pk}>"


# Option model
class Option(models.Model):
    value = models.CharField(max_length=255)
    position = models.SmallIntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        ordering = ["position"]

    def __str__(self) -> str:
        return f"<Option {self.pk} from Question {self.question.pk}>"


# Answer model
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"<Answer {self.pk} from Response {self.response.pk}>"


# AnswerOption model
class AnswerOption(models.Model):
    value = models.CharField(max_length=255)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("value", "answer"),)

    def __str__(self) -> str:
        return f"<AnswerOption {self.pk} from Answer {self.answer.pk}>"