import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionIndexViewTests(TestCase):

    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        create_question(question_text="Past question 1.", days=-30)
        create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class TestVote(TestCase):
    def setUp(self):
        self.question = Question.objects.create(question_text='How are you?', pub_date=timezone.now())
        self.question.save()

        self.question.choice_set.create(choice_text='Fine', votes=0)
        self.question.choice_set.create(choice_text='Good', votes=0)

    def test_vote(self):
        questions = Question.objects.filter(pk=self.question.id)
        self.assertNotEqual(questions, [])
        self.assertEqual(questions.get(pk=self.question.id).id, self.question.id)

        choice_1, choice_2 = Choice.objects.all()
        votes_before_test_1 = choice_1.votes
        votes_before_test_2 = choice_2.votes

        url = reverse('polls:vote', args=(self.question.id,))
        response = self.client.post(url, data={'choice': choice_1.id})

        votes_after_test_1 = Choice.objects.get(id=choice_1.id).votes
        votes_after_test_2 = Choice.objects.get(id=choice_2.id).votes
        self.assertEqual(response.status_code, 302)
        self.assertEqual(votes_before_test_1 + 1, votes_after_test_1)
        self.assertEqual(votes_before_test_2, votes_after_test_2)

    def test_vote_negative(self):
        url = reverse('polls:vote', args=(self.question.id,))
        response = self.client.post(url, data={'choice': 5})
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.question.delete()
        Choice.objects.all().delete()


class TestCreate(TestCase):
    def setUp(self):
        self.question_data = {'new_question': 'How are you?'}
        self.question_empty_data = {'new_question': ''}
        self.question_space_data = {'new_question': ' '}

    def test_create_data(self):
        self.assertFalse(Question.objects.filter(question_text=self.question_data["new_question"]).exists())

        url = reverse('polls:create')
        response = self.client.post(url, data=self.question_data)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(Question.objects.filter(question_text=self.question_data["new_question"]).exists())

    def test_create_empty_data(self):
        self.assertFalse(Question.objects.filter(question_text=self.question_empty_data["new_question"]).exists())

        url = reverse('polls:create')
        response = self.client.post(url, data=self.question_empty_data)
        self.assertEqual(response.status_code, 200)

        self.assertFalse(Question.objects.filter(question_text=self.question_empty_data["new_question"]).exists())

    def test_create_space_data(self):
        self.assertFalse(Question.objects.filter(question_text=self.question_space_data["new_question"]).exists())

        url = reverse('polls:create')
        response = self.client.post(url, data=self.question_space_data)
        self.assertEqual(response.status_code, 200)

        self.assertFalse(Question.objects.filter(question_text=self.question_space_data["new_question"]).exists())

    def tearDown(self):
        self.question_data.clear()
        self.question_empty_data.clear()
        self.question_space_data.clear()


class TestCreateAnswer(TestCase):
    def setUp(self):
        self.question = Question.objects.create(question_text='How are you?', pub_date=timezone.now())
        self.question.save()

    def test_create_answer(self):
        answers_empty = Choice.objects.filter(pk=self.question.id)
        self.assertFalse(answers_empty.exists())

        url = reverse('polls:create_answer', args=(self.question.id,))
        response = self.client.post(url, data={'new_answer': 'some answer'})
        self.assertEqual(response.status_code, 302)

        answers_after = Choice.objects.filter(pk=self.question.id).exists()
        self.assertTrue(answers_after)

    def test_more_than_three_answers(self):
        url = reverse('polls:create_answer', args=(self.question.id,))
        response = self.client.post(url, data={'new_answer': 'First answer'})
        response = self.client.post(url, data={'new_answer': 'Second answer'})
        response = self.client.post(url, data={'new_answer': 'Third answer'})
        count_of_answers_3 = self.question.choice_set.count()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(count_of_answers_3, 3)

        response = self.client.post(url, data={'new_answer': 'Forth answer'})
        count_of_answers_4 = self.question.choice_set.count()
        self.assertEqual(count_of_answers_4, 3)
        self.assertEqual(response.context['message_too_much'], "You can't add moore than 3 answers.")

    def tearDown(self):
        self.question.delete()
        Choice.objects.all().delete()
