from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

from pytils.translit import slugify

User = get_user_model()
URL_ADD = 'notes:add'
URL_SUCCESS = 'notes:success'
URL_EDIT = 'notes:edit'
URL_DELETE = 'notes:delete'
ONE_NOTE = 1


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'slug'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.url_add = reverse(URL_ADD)
        cls.url_redirect = reverse(URL_SUCCESS)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url_add, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_can_create_note(self):
        response = self.author_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_redirect)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_empty_slug(self):
        count_note_before = Note.objects.count()
        self.form_data.pop('slug')
        response = self.author_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_redirect)
        count_note_after = Note.objects.count()
        self.assertEqual(count_note_before + ONE_NOTE, count_note_after)
        note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(note.slug, expected_slug)
        self.assertEqual(self.form_data['title'], note.title)
        self.assertEqual(self.form_data['text'], note.text)


class TestNoteEditDelete(TestCase):
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'slug'
    NEW_NOTE_TITLE = 'Обновленный заголовок заметки'
    NEW_NOTE_TEXT = 'Обновленный текст заметки'
    NEW_NOTE_SLUG = 'new_slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Не автор заметки')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author)
        cls.url_redirect = reverse(URL_SUCCESS)
        cls.url_edit = reverse(URL_EDIT, args=(cls.note.slug,))
        cls.url_delete = reverse(URL_DELETE, args=(cls.note.slug,))
        cls.form_data = {
            'text': cls.NEW_NOTE_TEXT,
            'title': cls.NEW_NOTE_TITLE,
            'slug': cls.NEW_NOTE_SLUG,
        }

    def test_author_can_delete_note(self):
        count_note_before = Note.objects.count()
        response = self.author_client.post(self.url_delete)
        self.assertRedirects(response, self.url_redirect)
        count_note_after = Note.objects.count()
        self.assertEqual(count_note_before - ONE_NOTE, count_note_after)

    def test_user_cant_delete_note_of_another_user(self):
        count_note_before = Note.objects.count()
        response = self.reader_client.delete(self.url_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        count_note_after = Note.objects.count()
        self.assertEqual(count_note_before, count_note_after)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.url_edit, self.form_data)
        self.assertRedirects(response, self.url_redirect)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)
        self.assertEqual(self.note.author, self.author)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.url_edit, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)
        self.assertEqual(self.note.author, self.author)

    def test_not_unique_slug(self):
        count_note_before = Note.objects.count()
        url = reverse(URL_ADD)
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING))
        count_note_after = Note.objects.count()
        self.assertEqual(count_note_before, count_note_after)
