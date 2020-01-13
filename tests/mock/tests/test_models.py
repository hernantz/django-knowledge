from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.core import mail

from .test_base import TestCase
from knowledge.models import Question, Response


class BasicModelTest(TestCase):
    def test_basic_question_answering(self):
        """
        Given a question asked by a real user, track answering and accepted states.
        """

        ## joe asks a question ##
        question = Question.objects.create(
            user = self.joe,
            title = 'What time is it?',
            body = 'Whenever I look at my watch I see the little hand at 3 and the big hand at 7.'
        )

        self.assertFalse(question.answered())
        self.assertFalse(question.accepted())

        ## admin responds ##
        response = Response.objects.create(
            question = question,
            user = self.admin,
            body = 'The little hand at 3 means 3 pm or am, the big hand at 7 means 3:35 am or pm.'
        )

        self.assertTrue(question.answered())
        self.assertFalse(question.accepted())


        ## joe accepts the answer ##
        question.accept(response)

        self.assertTrue(question.answered())
        self.assertTrue(question.accepted())
        self.assertIn('accept', response.states())

        ## someone clears the accepted answer ##
        question.accept()

        self.assertFalse(question.accepted())

        response = Response.objects.get(id=response.id) # reload
        self.assertNotIn('accept', response.states())

        ## someone used the response accept shortcut ##
        response.accept()

        question = Question.objects.get(id=question.id) # reload
        self.assertTrue(question.answered())
        self.assertTrue(question.accepted())
        self.assertIn('accept', response.states())



    def test_switching_question(self):
        ## joe asks a question ##
        question = self.question
        self.assertEqual(question.status, 'private')
        self.assertIn('private', question.states())

        question.public()
        self.assertEqual(question.status, 'public')
        self.assertIn('public', question.states())

        question.private()
        self.assertEqual(question.status, 'private')
        self.assertIn('private', question.states())

        # no change
        question.inherit()
        self.assertEqual(question.status, 'private')
        self.assertIn('private', question.states())
        question.internal()
        self.assertEqual(question.status, 'private')
        self.assertIn('private', question.states())


    def test_switching_response(self):
        ## joe asks a question ##
        response = self.response
        self.assertEqual(response.status, 'inherit')
        self.assertIn('inherit', response.states())

        response.public()
        self.assertEqual(response.status, 'public')
        self.assertIn('public', response.states())

        response.internal()
        self.assertEqual(response.status, 'internal')
        self.assertIn('internal', response.states())

        response.private()
        self.assertEqual(response.status, 'private')
        self.assertIn('private', response.states())

        response.inherit()
        self.assertEqual(response.status, 'inherit')
        self.assertIn('inherit', response.states())


    def test_private_states(self):
        """
        Walk through the public, private and internal states for Question, and public, private,
        inherit and internal states for Response.

        Then checks who can see what with .can_view(<User>).
        """

        ## joe asks a question ##
        question = self.question

        self.assertFalse(question.can_view(self.anon))
        self.assertFalse(question.can_view(self.bob))

        self.assertTrue(question.can_view(self.joe))
        self.assertTrue(question.can_view(self.admin))


        ## someone comes along and publicizes this question ##
        question.public()

        # everyone can see
        self.assertTrue(question.can_view(self.anon))
        self.assertTrue(question.can_view(self.bob))

        self.assertTrue(question.can_view(self.joe))
        self.assertTrue(question.can_view(self.admin))


        ## someone comes along and privatizes this question ##
        question.private()
        
        self.assertFalse(question.can_view(self.anon))
        self.assertFalse(question.can_view(self.bob))

        self.assertTrue(question.can_view(self.joe))
        self.assertTrue(question.can_view(self.admin))


        ## admin responds ##
        response = self.response
        response.inherit()

        self.assertFalse(response.can_view(self.anon))
        self.assertFalse(response.can_view(self.bob))

        self.assertTrue(response.can_view(self.joe))
        self.assertTrue(response.can_view(self.admin))


        ## someone comes along and publicizes the parent question ##
        question.public()

        self.assertTrue(response.can_view(self.anon))
        self.assertTrue(response.can_view(self.bob))
        self.assertTrue(response.can_view(self.joe))
        self.assertTrue(response.can_view(self.admin))


        ## someone privatizes the response ##
        response.private()

        # everyone can see question still
        self.assertTrue(question.can_view(self.anon))
        self.assertTrue(question.can_view(self.bob))
        self.assertTrue(question.can_view(self.joe))
        self.assertTrue(question.can_view(self.admin))

        # only joe and admin can see the response though
        self.assertFalse(response.can_view(self.anon))
        self.assertFalse(response.can_view(self.bob))

        self.assertTrue(response.can_view(self.joe))
        self.assertTrue(response.can_view(self.admin))


        ## someone internalizes the response ##
        response.internal()

        # everyone can see question still
        self.assertTrue(question.can_view(self.anon))
        self.assertTrue(question.can_view(self.bob))
        self.assertTrue(question.can_view(self.joe))
        self.assertTrue(question.can_view(self.admin))

        # only admin can see the response though
        self.assertFalse(response.can_view(self.anon))
        self.assertFalse(response.can_view(self.bob))
        self.assertFalse(response.can_view(self.joe))

        self.assertTrue(response.can_view(self.admin))

    
    def test_get_responses(self):
        """
        Ensures adding another response isn't crossed into other responses.
        """
        self.assertEqual(len(self.question.get_responses(self.anon)), 0)
        self.assertEqual(len(self.question.get_responses(self.joe)), 1)
        self.assertEqual(len(self.question.get_responses(self.admin)), 1)

        question = Question.objects.create(
            title = 'Where is my cat?',
            body = 'His name is whiskers.',
            user = self.joe
        )
        response = Response.objects.create(
            question = question,
            user = self.admin,
            body = 'I saw him in the backyard.'
        )

        self.assertEqual(len(self.question.get_responses(self.anon)), 0)
        self.assertEqual(len(self.question.get_responses(self.joe)), 1)
        self.assertEqual(len(self.question.get_responses(self.admin)), 1)

        self.assertEqual(len(mail.outbox), 0)

    
    def test_get_public_responses(self):
        """
        Bug mentioned in issue #25.
        """
        question = Question.objects.create(
            title = 'Where is my cat?',
            body = 'His name is whiskers.',
            user = self.joe,
            status = 'public'

        )
        response = Response.objects.create(
            question = question,
            user = self.admin,
            body = 'I saw him in the backyard.',
            status = 'inherit'
        )

        self.assertEqual(len(question.get_responses(self.anon)), 1)
        self.assertEqual(len(question.get_responses(self.joe)), 1)
        self.assertEqual(len(question.get_responses(self.admin)), 1)

        self.assertEqual(len(mail.outbox), 0)

    
    def test_urls(self):
        question_url = reverse('knowledge_thread', args=[self.question.id, slugify(self.question.title)])

        self.assertEqual(self.question.url, question_url)


    def test_locking(self):
        self.assertFalse(self.question.locked)
        self.assertNotIn('lock', self.question.states())

        self.question.lock()

        self.assertTrue(self.question.locked)
        self.assertIn('lock', self.question.states())


    def test_url(self):
        self.assertEqual(
            '/knowledge/questions/{0}/{1}/'.format(
                self.question.id,
                slugify(self.question.title)),
            self.question.get_absolute_url()
        )

    def test_normal_question(self):
        self.assertEqual(self.question.get_name(), 'Joe Dirt')
        self.assertEqual(self.question.get_email(), 'joedirt@example.com')

        question = Question.objects.create(
            title = 'Where is my cat?',
            body = 'His name is whiskers.',
            user = self.bob
        )

        self.assertEqual(question.get_name(), 'bob') # no first/last
        self.assertEqual(question.get_email(), 'bob@example.com')


    def test_anon_question(self):
        question = Question.objects.create(
            title = 'Where is my cat?',
            body = 'His name is whiskers.',
            name = 'Joe Dirt',
            email = 'joedirt@example.com'
        )

        self.assertEqual(question.get_name(), 'Joe Dirt')
        self.assertEqual(question.get_email(), 'joedirt@example.com')























