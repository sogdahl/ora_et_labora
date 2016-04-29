import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Question, Choice


def create_question(question_text, days, choices=()):
    """
    Creates a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    question = Question.objects.create(
        question_text=question_text,
        pub_date=time
    )

    if choices:
        for choice in choices:
            Choice.objects.create(
                question=question,
                choice_text=choice
            )

    return question


class QuestionMethodTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() should return False for questions whose
        pub_date is in the future.
        """
        future_question = create_question('', 30)
        self.assertEqual(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() should return False for questions whose
        pub_date is older than 1 day.
        """
        old_question = create_question('', -30)
        self.assertEqual(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() should return True for questions whose
        pub_date is within the last day.
        """
        recent_question = create_question('', -0.041667)
        self.assertEqual(recent_question.was_published_recently(), True)


class ChoiceMethodTests(TestCase):

    def test_choices_start_with_zero_votes(self):
        """
        Choices should start with 0 votes
        """
        question = create_question('', 0, ('', ))
        self.assertEqual(question.choice_set.first().votes, 0)

    def test_choice_votes_increment_properly(self):
        """
        Choices should increment by one every time
        """
        question = create_question('', 0, ('', ))
        choice = question.choice_set.first()
        choice.vote()
        self.assertEqual(question.choice_set.first().votes, 1)
        choice.vote()
        self.assertEqual(question.choice_set.first().votes, 2)
        choice.vote()
        self.assertEqual(question.choice_set.first().votes, 3)

    def test_choice_votes_increment_properly_with_concurrent_instances(self):
        """
        Choices should increment by one every time, even if an instance has a stale .votes value
        """
        question = create_question('', 0, ('', ))
        choice_instance_1 = question.choice_set.first()
        choice_instance_2 = question.choice_set.first()
        choice_instance_1.vote()
        # choice_instance_2 still has the stale .votes = 0 but it should still properly increment .votes to 2
        choice_instance_2.vote()
        self.assertEqual(question.choice_set.first().votes, 2)


def create_api_question(client, question_text, days):
    url = reverse('polls:question-list')
    data = {
        'question_text': question_text,
        'pub_date': timezone.now() + datetime.timedelta(days=days)
    }
    return client.post(url, data, format='json')


class QuestionTests(APITestCase):
    def test_create_question(self):
        """
        Ensure we can create a new question object.
        """
        response = create_api_question(self.client, 'who?', 0)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)
        question = Question.objects.get()
        self.assertEqual(question.question_text, 'who?')
        self.assertLess(timezone.now() - question.pub_date, datetime.timedelta(minutes=1))

    def test_create_future_question(self):
        """
        Check to see that a question with pub_date in the future doesn't show up
        """
        response = create_api_question(self.client, 'who?', 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)

        get_url = reverse('polls:question-latest')
        get_response = self.client.get(get_url, format='json')
        self.assertEqual(get_response.data, [])


def create_api_choice(client, question, choice_text):
    url = reverse('polls:choice-list', kwargs={'question': question.pk})
    data = {
        'question': question.pk,
        'choice_text': choice_text
    }
    return client.post(url, data, format='json')


class ChoiceTests(APITestCase):
    def test_create_choice(self):
        """
        Ensure we can create a new choice object.
        """
        question_response = create_api_question(self.client, 'who?', 0)
        self.assertEqual(question_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)
        question = Question.objects.get()

        choice_response = create_api_choice(self.client, question, 'me')
        self.assertEqual(choice_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Choice.objects.count(), 1)

    def test_create_choices_separate(self):
        """
        Ensure that choices only show up for the question they're related to
        """
        question_response = create_api_question(self.client, 'who?', 0)
        self.assertEqual(question_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)
        question1 = Question.objects.get(pk=question_response.data['id'])

        question_response = create_api_question(self.client, 'what?', 0)
        self.assertEqual(question_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 2)
        question2 = Question.objects.get(pk=question_response.data['id'])

        choice_response1a = create_api_choice(self.client, question1, 'me')
        choice_response1b = create_api_choice(self.client, question1, 'you')
        choice_response2a = create_api_choice(self.client, question2, 'this')
        choice_response2b = create_api_choice(self.client, question2, 'that')
        choice_response2c = create_api_choice(self.client, question2, 'the other thing')
        self.assertEqual(choice_response1a.status_code, status.HTTP_201_CREATED)
        self.assertEqual(choice_response1b.status_code, status.HTTP_201_CREATED)
        self.assertEqual(choice_response2a.status_code, status.HTTP_201_CREATED)
        self.assertEqual(choice_response2b.status_code, status.HTTP_201_CREATED)
        self.assertEqual(choice_response2c.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Choice.objects.count(), 5)

        get_url1 = reverse('polls:choice-list', kwargs={'question': question1.pk})
        get_response1 = self.client.get(get_url1, format='json')
        self.assertEqual(len(get_response1.data), 2)
        get_url2 = reverse('polls:choice-list', kwargs={'question': question2.pk})
        get_response2 = self.client.get(get_url2, format='json')
        self.assertEqual(len(get_response2.data), 3)

    def test_vote_for_choice(self):
        """
        Ensure we can vote for a choice properly
        """
        question_response = create_api_question(self.client, 'who?', 0)
        self.assertEqual(question_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)
        question = Question.objects.get()

        choice1_response = create_api_choice(self.client, question, 'me')
        self.assertEqual(choice1_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Choice.objects.count(), 1)
        choice2_response = create_api_choice(self.client, question, 'you')
        self.assertEqual(choice2_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Choice.objects.count(), 2)

        vote_url = reverse('polls:choice-vote-for', kwargs={'question': question.pk, 'pk': choice2_response.data['id']})
        vote_data = {}
        vote_response = self.client.post(vote_url, vote_data, format='json')
        self.assertEqual(vote_response.status_code, status.HTTP_200_OK)
        self.assertEqual(vote_response.data, {"status": "voted"})
        choice1 = Choice.objects.get(pk=choice1_response.data['id'])
        choice2 = Choice.objects.get(pk=choice2_response.data['id'])
        self.assertEqual(choice1.votes, 0)
        self.assertEqual(choice2.votes, 1)


cant_test_angular_this_way = '''
class QuestionViewTests(TestCase):
    def test_index_view_with_no_questions(self):
        """
        If no questions exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_index_view_with_a_past_question(self):
        """
        Questions with a pub_date in the past should be displayed on the
        index page.
        """
        create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_index_view_with_a_future_question(self):
        """
        Questions with a pub_date in the future should not be displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.",
                            status_code=200)
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_index_view_with_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        should be displayed.
        """
        create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_index_view_with_two_past_questions(self):
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


class QuestionIndexDetailTests(TestCase):
    def test_detail_view_with_a_future_question(self):
        """
        The detail view of a question with a pub_date in the future should
        return a 404 not found.
        """
        future_question = create_question(question_text='Future question.',
                                          days=5)
        response = self.client.get(reverse('polls:detail',
                                   args=(future_question.id,)))
        self.assertEqual(response.status_code, 404)

    def test_detail_view_with_a_past_question(self):
        """
        The detail view of a question with a pub_date in the past should
        display the question's text.
        """
        past_question = create_question(question_text='Past Question.',
                                        days=-5)
        response = self.client.get(reverse('polls:detail',
                                   args=(past_question.id,)))
        self.assertContains(response, past_question.question_text,
                            status_code=200)
'''