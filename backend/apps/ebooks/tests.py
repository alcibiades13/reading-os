import io
import shutil
import tempfile
import zipfile
from unittest import mock

from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.books.models import Book
from apps.ebooks.models import EBook
from apps.reading.models import BookReadLog, ReadingSession, UserBook
from apps.social.models import FeedItem
from apps.users.models import User

TEMP_STORAGE = tempfile.mkdtemp()


class TempEbookStorage:
    """
    Point EBook file fields at a temp dir. The fields resolve their (callable) storage
    when the model is defined, so override_settings(STORAGES=...) would be too late.
    """
    def setUp(self):
        storage = FileSystemStorage(location=TEMP_STORAGE)
        for name in ('file', 'cover'):
            patcher = mock.patch.object(EBook._meta.get_field(name), 'storage', storage)
            patcher.start()
            self.addCleanup(patcher.stop)
        super().setUp()


def make_epub():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('mimetype', 'application/epub+zip')
        zf.writestr('META-INF/container.xml', '<container/>')
    return SimpleUploadedFile('book.epub', buf.getvalue(), content_type='application/epub+zip')


def make_pdf():
    return SimpleUploadedFile('book.pdf', b'%PDF-1.4 test', content_type='application/pdf')


@override_settings(ALLOWED_HOSTS=['testserver'])
class EBookAPITests(TempEbookStorage, TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_STORAGE, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(email='reader@example.com', password='x', first_name='R', last_name='One')
        self.other = User.objects.create_user(email='other@example.com', password='x', first_name='O', last_name='Two')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def upload(self, file, **data):
        payload = {'file': file, 'title': 'Na Drini ćuprija', 'author': 'Ivo Andrić', **data}
        return self.client.post('/api/ebooks/', payload, format='multipart')

    # --- upload & privacy ---

    def test_upload_detects_format_from_content(self):
        self.assertEqual(self.upload(make_epub()).data['format'], 'epub')
        self.assertEqual(self.upload(make_pdf(), page_count=300).data['format'], 'pdf')

    def test_upload_leaves_tracking_unanswered(self):
        # Multipart must not coerce the missing boolean to False - the reader asks on first open
        self.assertIsNone(self.upload(make_pdf()).data['track_progress'])
        ebook_id = self.upload(make_pdf()).data['id']
        self.client.patch(f'/api/ebooks/{ebook_id}/', {'track_progress': True}, format='json')
        self.assertIsNone(EBook.objects.get(pk=ebook_id).track_progress)

    def test_rejects_non_ebook_and_missing_metadata(self):
        fake = SimpleUploadedFile('x.epub', b'not a book')
        self.assertEqual(self.upload(fake).status_code, 400)
        self.assertEqual(self.upload(make_pdf(), title='  ').status_code, 400)

    def test_file_is_private_to_owner(self):
        ebook_id = self.upload(make_pdf()).data['id']
        self.assertEqual(self.client.get(f'/api/ebooks/{ebook_id}/file/').status_code, 200)

        other = APIClient()
        other.force_authenticate(self.other)
        self.assertEqual(other.get(f'/api/ebooks/{ebook_id}/file/').status_code, 404)
        self.assertEqual(APIClient().get(f'/api/ebooks/{ebook_id}/file/').status_code, 401)

    # --- progress tracking ---

    def test_enable_tracking_creates_catalog_book_and_shelf_entry(self):
        ebook_id = self.upload(make_pdf(), page_count=200, isbn='9788652141234').data['id']
        res = self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': True}, format='json')

        self.assertEqual(res.status_code, 200)
        book = Book.objects.get(isbn='9788652141234')
        self.assertEqual(book.pages, 200)
        self.assertEqual(list(book.authors.values_list('name', flat=True)), ['Ivo Andrić'])
        user_book = UserBook.objects.get(user=self.user, book=book)
        self.assertEqual(user_book.status, 'currently_reading')
        self.assertEqual(res.data['library_entry']['id'], user_book.id)

    def test_tracking_reuses_existing_catalog_book_and_shelf_entry(self):
        book = Book.objects.create(title='Na Drini ćuprija', isbn='9788652141234', pages=400)
        existing = UserBook.objects.create(user=self.user, book=book, status='want_to_read')
        ebook_id = self.upload(make_epub(), isbn='9788652141234').data['id']

        self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': True}, format='json')

        self.assertEqual(Book.objects.filter(isbn='9788652141234').count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.status, 'currently_reading')
        self.assertIsNotNone(existing.started_at)

    def test_epub_without_page_count_can_supply_pages(self):
        ebook_id = self.upload(make_epub()).data['id']
        res = self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': True, 'pages': 320}, format='json')
        self.assertEqual(res.data['total_pages'], 320)

    def test_progress_syncs_forward_only_without_feed_spam(self):
        ebook_id = self.upload(make_pdf(), page_count=200).data['id']
        self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': True}, format='json')
        feed_before = FeedItem.objects.filter(user=self.user).count()

        self.client.patch(f'/api/ebooks/{ebook_id}/', {'position': '100', 'progress': 0.5}, format='json')
        user_book = UserBook.objects.get(user=self.user)
        self.assertEqual(user_book.current_page, 100)

        # Flipping back keeps the furthest page read
        self.client.patch(f'/api/ebooks/{ebook_id}/', {'position': '20', 'progress': 0.1}, format='json')
        user_book.refresh_from_db()
        self.assertEqual(user_book.current_page, 100)

        self.assertEqual(FeedItem.objects.filter(user=self.user).count(), feed_before)

    def test_no_sync_when_tracking_declined(self):
        ebook_id = self.upload(make_pdf(), page_count=200).data['id']
        res = self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': False}, format='json')
        self.assertIs(res.data['track_progress'], False)
        self.client.patch(f'/api/ebooks/{ebook_id}/', {'position': '100', 'progress': 0.5}, format='json')
        self.assertFalse(UserBook.objects.filter(user=self.user).exists())

    def test_finish_marks_read_and_logs(self):
        ebook_id = self.upload(make_pdf(), page_count=200).data['id']
        self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': True}, format='json')
        res = self.client.post(f'/api/ebooks/{ebook_id}/finish/')

        self.assertEqual(res.data['library_entry']['status'], 'read')
        user_book = UserBook.objects.get(user=self.user)
        self.assertEqual(user_book.current_page, 200)
        self.assertEqual(BookReadLog.objects.filter(user_book=user_book).count(), 1)

    def test_session_logging(self):
        ebook_id = self.upload(make_pdf(), page_count=200).data['id']
        self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': True}, format='json')

        short = self.client.post(f'/api/ebooks/{ebook_id}/session/', {'duration_seconds': 20, 'start_progress': 0.1, 'end_progress': 0.2}, format='json')
        self.assertFalse(short.data['logged'])

        res = self.client.post(f'/api/ebooks/{ebook_id}/session/', {'duration_seconds': 900, 'start_progress': 0.1, 'end_progress': 0.2}, format='json')
        self.assertTrue(res.data['logged'])
        session = ReadingSession.objects.get(user=self.user)
        self.assertEqual((session.start_page, session.end_page, session.pages_read), (20, 40, 20))

    def test_link_catalog_creates_book_once(self):
        ebook_id = self.upload(make_epub()).data['id']
        first = self.client.post(f'/api/ebooks/{ebook_id}/link-catalog/').data['book']
        second = self.client.post(f'/api/ebooks/{ebook_id}/link-catalog/').data['book']
        self.assertIsNotNone(first)
        self.assertEqual(first, second)
        self.assertIsNone(EBook.objects.get(pk=ebook_id).track_progress)

    def test_filter_by_book(self):
        book = Book.objects.create(title='Linked')
        self.upload(make_pdf(), book=book.id)
        self.upload(make_pdf())
        res = self.client.get(f'/api/ebooks/?book={book.id}')
        self.assertEqual(res.data['count'], 1)

    def test_delete_removes_file(self):
        ebook_id = self.upload(make_pdf()).data['id']
        storage_name = EBook.objects.get(pk=ebook_id).file.name
        self.client.delete(f'/api/ebooks/{ebook_id}/')
        self.assertFalse(EBook.objects.filter(pk=ebook_id).exists())
        self.assertFalse(EBook._meta.get_field('file').storage.exists(storage_name))


@override_settings(ALLOWED_HOSTS=['testserver'])
class PublicDomainTests(TempEbookStorage, TestCase):
    META = {
        'id': 1342, 'title': 'Pride and Prejudice', 'authors': ['Jane Austen'], 'languages': ['en'],
        'cover_url': 'https://example.invalid/cover.jpg', 'has_epub': True, 'download_count': 1, 'summary': '',
    }

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(email='pd@example.com', password='x', first_name='P', last_name='D')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_author_display_names(self):
        from apps.ebooks.public_domain import display_name
        self.assertEqual(display_name('Austen, Jane'), 'Jane Austen')
        self.assertEqual(display_name('Tolstoy, Leo, graf'), 'Leo Tolstoy')
        self.assertEqual(display_name('Homer'), 'Homer')

    def test_search_parses_opds_feed(self):
        from unittest import mock
        from apps.ebooks import public_domain
        feed = b'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
          <link rel="next" href="/next"/>
          <entry><id>https://www.gutenberg.org/ebooks/authors/search.opds/?query=x</id><title>Authors</title></entry>
          <entry><id>https://www.gutenberg.org/ebooks/2600.opds</id><title>War and Peace</title><content>graf Leo Tolstoy</content></entry>
        </feed>'''
        with mock.patch.object(public_domain, '_fetch', return_value=feed) as fetch:
            data = public_domain.search('tolstoy', 'en', 2)
        self.assertEqual(fetch.call_args.args[1], {'start_index': 26, 'query': 'tolstoy l.en'})
        self.assertTrue(data['has_next'])
        self.assertEqual(data['results'], [{
            'id': 2600, 'title': 'War and Peace', 'authors': ['graf Leo Tolstoy'],
            'cover_url': 'https://www.gutenberg.org/cache/epub/2600/pg2600.cover.medium.jpg',
        }])

    def test_import_creates_private_copy_once(self):
        from unittest import mock
        with mock.patch('apps.ebooks.public_domain.get_book', return_value=self.META), \
             mock.patch('apps.ebooks.public_domain.download_epub', return_value=make_epub().read()) as download, \
             mock.patch('apps.ebooks.public_domain.download_cover', return_value=b'\xff\xd8jpeg'):
            first = self.client.post('/api/ebooks/public-domain/import/', {'gutenberg_id': 1342}, format='json')
            second = self.client.post('/api/ebooks/public-domain/import/', {'gutenberg_id': 1342}, format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data['title'], 'Pride and Prejudice')
        self.assertEqual(first.data['author'], 'Jane Austen')
        self.assertEqual(first.data['source'], 'gutenberg')
        self.assertTrue(first.data['has_cover'])
        self.assertEqual(second.data['id'], first.data['id'])
        self.assertEqual(download.call_count, 1)

    def test_search_marks_owned_books(self):
        from unittest import mock
        EBook.objects.create(user=self.user, title='P', author='A', format='epub', source='gutenberg', source_id='1342', file='x.epub')
        results = {'count': 2, 'has_next': False, 'results': [dict(self.META), dict(self.META, id=11)]}
        with mock.patch('apps.ebooks.public_domain.search', return_value=results):
            res = self.client.get('/api/ebooks/public-domain/search/?q=pride')
        owned = {r['id']: r['ebook_id'] for r in res.data['results']}
        self.assertIsNotNone(owned[1342])
        self.assertIsNone(owned[11])

    def test_catalog_outage_returns_503(self):
        from unittest import mock
        from apps.ebooks.public_domain import CatalogUnavailable
        with mock.patch('apps.ebooks.public_domain.search', side_effect=CatalogUnavailable('down')):
            self.assertEqual(self.client.get('/api/ebooks/public-domain/search/').status_code, 503)
