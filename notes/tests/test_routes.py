from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()
URL_HOME = 'notes:home'
URL_ADD = 'notes:add'
URL_EDIT = 'notes:edit'
URL_DETAIL = 'notes:detail'
URL_DELETE = 'notes:delete'
URL_LIST = 'notes:list'
URL_SUCCESS = 'notes:success'
URL_LOGIN = 'users:login'
URL_LOGOUT = 'users:logout'
URL_SIGNUP = 'users:signup'


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
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
        cls.msg = 'Статус страницы не соответствует ожидаемому.'

    def test_pages_availability_for_anonymous_user(self):
        urls = URL_HOME, URL_LOGIN, URL_LOGOUT, URL_SIGNUP
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    msg=self.msg
                )

    def test_availability_for_note_edit_detail_delete(self):
        users_statuses = (
            (self.author, self.author_client, HTTPStatus.OK),
            (self.reader, self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for user, user_client, status in users_statuses:
            urls = URL_EDIT, URL_DETAIL, URL_DELETE
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = user_client.get(url)
                    self.assertEqual(
                        response.status_code,
                        status,
                        msg=self.msg
                    )

    def test_pages_availability_for_auth_user(self):
        users_statuses = (
            (self.author, self.author_client, HTTPStatus.OK),
        )
        for user, user_client, status in users_statuses:
            urls = URL_LIST, URL_SUCCESS, URL_ADD
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name)
                    response = user_client.get(url)
                    self.assertEqual(
                        response.status_code,
                        status,
                        msg=self.msg
                    )

    def test_redirect_for_anonymous_client(self):
        login_url = reverse(URL_LOGIN)
        urls = (
            (URL_LIST, None),
            (URL_SUCCESS, None),
            (URL_ADD, None),
            (URL_DETAIL, (self.note.slug,)),
            (URL_EDIT, (self.note.slug,)),
            (URL_DELETE, (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
