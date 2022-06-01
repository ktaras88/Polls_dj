from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """

        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()

        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


def create(request):
    if request.method == 'POST':
        if not request.POST['new_question'].strip():
            return render(request, 'polls/create.html', {'message': "You didn't enter a question.", })
        else:
            create_question = Question(question_text=request.POST['new_question'], pub_date=timezone.now())
            create_question.save()

            return HttpResponseRedirect(reverse('polls:index'))
    else:
        return render(request, 'polls/create.html')


def create_answer(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if question.answer_count < 3:
        if request.method == 'POST':
            if not request.POST['new_answer'].strip():
                return render(request, 'polls/create_answer.html', {'message': "You didn't enter an answer.",
                                                                    'question': question,
                                                                    })
            else:
                question.choice_set.create(choice_text=request.POST['new_answer'], votes=0)

                return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))

        return render(request, 'polls/create_answer.html', {'question': question})
    else:
        return render(request, 'polls/detail.html', {'message_too_much': "You can't add moore than 3 answers.",
                                                     'question': question,
                                                     })
