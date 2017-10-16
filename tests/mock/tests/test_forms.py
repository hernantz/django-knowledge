from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from .test_base import TestCase
from knowledge.models import Question, Response
from knowledge.forms import QuestionForm, ResponseForm


class BasicFormTest(TestCase):
    """
    This tests reflect our defaults... namely KNOWLEDGE_ALLOW_ANONYMOUS,
    KNOWLEDGE_AUTO_PUBLICIZE, and KNOWLEDGE_FREE_RESPONSE.
    """

    def test_question_form_display(self):
        self.assertEqual(
            None,
            QuestionForm(self.anon)
        )

        self.assertNotEqual(
            None,
            QuestionForm(self.joe)
        )

        self.assertNotEqual(
            None,
            ResponseForm(self.admin, self.question)
        )

    def test_response_form_display(self):
        self.assertEqual(
            None,
            ResponseForm(self.anon, self.question)
        )

        self.assertNotEqual(
            None,
            ResponseForm(self.joe, self.question)
        )

        self.assertNotEqual(
            None,
            ResponseForm(self.admin, self.question)
        )

        # the default is to let others comment on
        # questions, even if they aren't staff and
        # didn't ask the question (KNOWLEDGE_FREE_RESPONSE)
        self.assertNotEqual(
            None,
            ResponseForm(self.bob, self.question)
        )

        # lock the question...
        self.question.lock()

        self.assertEqual(
            None,
            ResponseForm(self.admin, self.question)
        )

    def test_form_saving(self):
        QUESTION_POST = {
            'title': 'This is a title friend!',
            'body': 'This is the body friend!',
            'status': 'private'
        }

        form = QuestionForm(self.joe, QUESTION_POST)

        self.assertTrue(form.is_valid())

        question = form.save()

        self.assertEqual(question.status, 'private')
        self.assertEqual(question.name, None)
        self.assertEqual(question.email, None)
        self.assertEqual(question.title, 'This is a title friend!')
        self.assertEqual(question.body, 'This is the body friend!')
        self.assertEqual(question.user, self.joe)


        RESPONSE_POST = {
            'body': 'This is the response body friend!'
        }

        form = ResponseForm(self.joe, question, RESPONSE_POST)

        self.assertTrue(form.is_valid())

        response = form.save()

        self.assertEqual(response.status, 'inherit')
        self.assertEqual(response.name, None)
        self.assertEqual(response.email, None)
        self.assertEqual(response.body, 'This is the response body friend!')
        self.assertEqual(response.user, self.joe)
    
    def test_form_question_status(self):
        # test the default for anonymous in tests/settings.py...
        form = QuestionForm(self.joe)
        self.assertIn('status', list(form.fields.keys()))

        # internal is only selectable for admins
        QUESTION_POST = {
            'title': 'This is a title friend!',
            'body': 'This is the body friend!',
            'status': 'internal'
        }

        self.assertFalse(QuestionForm(self.joe, QUESTION_POST).is_valid())
        self.assertTrue(QuestionForm(self.admin, QUESTION_POST).is_valid())

        QUESTION_POST = {
            'title': 'This is a title friend!',
            'body': 'This is the body friend!',
            'status': 'public'
        }
        question = QuestionForm(self.joe, QUESTION_POST).save()
        self.assertEqual(question.status, 'public')
