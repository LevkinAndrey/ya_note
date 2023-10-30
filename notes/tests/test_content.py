from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()
URL_DETAIL = 'notes:list'
URL_ADD = 'notes:add'
URL_EDIT = 'notes:edit'


class TestListNotes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author)

    def test_notes_list_for_different_users(self):
        users = (
            (self.author, self.author_client, True),
            (self.reader, self.reader_client, False)
        )
        for user, user_client, note_in_list in users:
            with self.subTest(user=user, note_in_list=note_in_list):
                url = reverse(URL_DETAIL)
                response = user_client.get(url)
                object_list = response.context['object_list']
                self.assertEqual((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        urls = (
            (URL_ADD, None),
            (URL_EDIT, (self.note.slug,))
        )
        for name, args in urls:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                form = response.context.get('form')
                self.assertIsInstance(form, NoteForm)
