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
        # Public copies of covers (catalog books) go to default storage
        patcher = mock.patch('apps.ebooks.progress.default_storage', storage)
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

    def test_cover_is_shared_with_catalog_book_without_cover(self):
        cover = SimpleUploadedFile('c.jpg', b'\xff\xd8jpeg', content_type='image/jpeg')
        no_cover = Book.objects.create(title='Bez korice')
        self.upload(make_pdf(), book=no_cover.id, cover_file=cover)
        no_cover.refresh_from_db()
        self.assertTrue(no_cover.cover_image.startswith('/media/book_covers/ebook-'))

        # A catalog book that already has a cover keeps it
        with_cover = Book.objects.create(title='Sa koricom', cover_image='https://example.com/c.jpg')
        cover = SimpleUploadedFile('c.jpg', b'\xff\xd8jpeg', content_type='image/jpeg')
        self.upload(make_pdf(), book=with_cover.id, cover_file=cover)
        with_cover.refresh_from_db()
        self.assertEqual(with_cover.cover_image, 'https://example.com/c.jpg')

    def test_book_with_local_cover_can_still_be_edited(self):
        book = Book.objects.create(title='Lokalna', cover_image='/media/book_covers/x.jpg')
        res = self.client.patch(f'/api/books/{book.id}/', {'cover_image': '/media/book_covers/x.jpg', 'title': 'Lokalna 2'}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        res = self.client.patch(f'/api/books/{book.id}/', {'cover_image': 'http://192.168.1.5:8001/media/book_covers/x.jpg'}, format='json')
        book.refresh_from_db()
        self.assertEqual(book.cover_image, '/media/book_covers/x.jpg')
        res = self.client.patch(f'/api/books/{book.id}/', {'cover_image': 'not a url'}, format='json')
        self.assertEqual(res.status_code, 400)

    # --- stickers (parallel reading threads) ---

    def _tracked_pdf(self, pages=100):
        ebook_id = self.upload(make_pdf(), page_count=pages).data['id']
        self.client.post(f'/api/ebooks/{ebook_id}/tracking/', {'enabled': True}, format='json')
        return ebook_id

    def _page(self):
        return UserBook.objects.get(user=self.user).current_page

    def test_stickers_set_overall_progress_to_earliest(self):
        ebook_id = self._tracked_pdf()
        self.client.post(f'/api/ebooks/{ebook_id}/bookmarks/', {'label': 'Stari zavet', 'position': '30', 'progress': 0.3}, format='json')
        res = self.client.post(f'/api/ebooks/{ebook_id}/bookmarks/', {'label': 'Novi zavet', 'position': '70', 'progress': 0.7}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['overall_progress'], 0.3)
        self.assertEqual(len(res.data['bookmarks']), 2)
        self.assertEqual(self._page(), 30)

        # An earlier sticker pulls progress back
        res = self.client.post(f'/api/ebooks/{ebook_id}/bookmarks/', {'label': 'Psalmi', 'position': '10', 'progress': 0.1}, format='json')
        self.assertEqual(self._page(), 10)

        # Removing it moves progress forward to the next earliest
        psalmi = next(b for b in res.data['bookmarks'] if b['label'] == 'Psalmi')
        self.client.delete(f"/api/ebooks/{ebook_id}/bookmarks/{psalmi['id']}/")
        self.assertEqual(self._page(), 30)

    def test_reading_from_a_sticker_moves_it(self):
        ebook_id = self._tracked_pdf()
        res = self.client.post(f'/api/ebooks/{ebook_id}/bookmarks/', {'label': 'Stari', 'position': '30', 'progress': 0.3}, format='json')
        self.client.post(f'/api/ebooks/{ebook_id}/bookmarks/', {'label': 'Novi', 'position': '70', 'progress': 0.7}, format='json')
        stari = res.data['bookmarks'][0]['id']

        res = self.client.patch(f'/api/ebooks/{ebook_id}/', {'position': '45', 'progress': 0.45, 'bookmark': stari}, format='json')
        moved = next(b for b in res.data['bookmarks'] if b['id'] == stari)
        self.assertEqual((moved['position'], moved['progress']), ('45', 0.45))
        self.assertEqual(res.data['overall_progress'], 0.45)
        self.assertEqual(self._page(), 45)

        # Reading without a sticker doesn't move any sticker or the overall progress
        res = self.client.patch(f'/api/ebooks/{ebook_id}/', {'position': '90', 'progress': 0.9}, format='json')
        self.assertEqual(res.data['overall_progress'], 0.45)
        self.assertEqual(self._page(), 45)

    def test_sticker_rename_and_validation(self):
        ebook_id = self.upload(make_epub()).data['id']
        res = self.client.post(f'/api/ebooks/{ebook_id}/bookmarks/', {'label': '  ', 'position': 'epubcfi(/6/2)'}, format='json')
        self.assertEqual(res.status_code, 400)
        res = self.client.post(f'/api/ebooks/{ebook_id}/bookmarks/', {'label': 'Matej 7', 'position': 'epubcfi(/6/2)'}, format='json')
        bid = res.data['bookmarks'][0]['id']
        self.assertIsNone(res.data['bookmarks'][0]['progress'])
        res = self.client.patch(f'/api/ebooks/{ebook_id}/bookmarks/{bid}/', {'label': 'Matej 7:12'}, format='json')
        self.assertEqual(res.data['bookmarks'][0]['label'], 'Matej 7:12')

        other = APIClient()
        other.force_authenticate(self.other)
        self.assertEqual(other.delete(f'/api/ebooks/{ebook_id}/bookmarks/{bid}/').status_code, 404)

    # --- capture from the reader (quotes / notes / words + highlights) ---

    def _capture(self, ebook_id, kind, data, client_id='', position='epubcfi(/6/4!/4/2,/1:0,/1:10)', text='Blaženi'):
        return self.client.post(f'/api/ebooks/{ebook_id}/capture/', {
            'kind': kind, 'data': data, 'position': position, 'text': text, 'client_id': client_id,
        }, format='json')

    def test_capture_creates_objects_with_highlights(self):
        from apps.reading.models import Quote, VocabularyWord
        from apps.reading.models_study import StudyNote
        ebook_id = self.upload(make_epub()).data['id']

        quote = self._capture(ebook_id, 'quote', {'text': 'Blaženi krotki', 'chapter': 'Matej 5'})
        self.assertEqual(quote.status_code, 201, quote.data)
        self.assertIsNotNone(quote.data['ebook']['book'])  # linked to the catalog on first capture
        note = self._capture(ebook_id, 'note', {'content': 'Misao', 'reference': 'Matej 5:5', 'note_type': 'insight'})
        self.assertEqual(note.status_code, 201, note.data)
        word = self._capture(ebook_id, 'word', {'word': 'krotki', 'definition': 'blagi', 'context': 'Blaženi krotki.'})
        self.assertEqual(word.status_code, 201, word.data)

        q = Quote.objects.get(user=self.user)
        self.assertEqual((q.text, q.chapter, q.book_id), ('Blaženi krotki', 'Matej 5', quote.data['ebook']['book']))
        self.assertEqual(StudyNote.objects.get(user=self.user).reference, 'Matej 5:5')
        self.assertEqual(VocabularyWord.objects.get(user=self.user).definition, 'blagi')

        highlights = self.client.get(f'/api/ebooks/{ebook_id}/annotations/').data
        self.assertEqual([h['kind'] for h in highlights], ['quote', 'note', 'word'])
        self.assertEqual(highlights[2]['title'], 'krotki')
        self.assertEqual(highlights[1]['reference'], 'Matej 5:5')

        index = self.client.get('/api/ebooks/annotations/index/?kind=quote').data
        self.assertEqual(index, [{'kind': 'quote', 'object_id': q.id, 'ebook_id': ebook_id, 'position': 'epubcfi(/6/4!/4/2,/1:0,/1:10)'}])

    def test_capture_replay_is_idempotent(self):
        from apps.reading.models import Quote
        ebook_id = self.upload(make_epub()).data['id']
        first = self._capture(ebook_id, 'quote', {'text': 'Jednom'}, client_id='abc-123')
        again = self._capture(ebook_id, 'quote', {'text': 'Jednom'}, client_id='abc-123')
        self.assertEqual((first.status_code, again.status_code), (201, 200))
        self.assertEqual(Quote.objects.filter(user=self.user).count(), 1)

    def test_deleting_quote_removes_highlight(self):
        from apps.reading.models import Quote
        ebook_id = self.upload(make_epub()).data['id']
        self._capture(ebook_id, 'quote', {'text': 'Prolazno'})
        Quote.objects.get(user=self.user).delete()
        self.assertEqual(self.client.get(f'/api/ebooks/{ebook_id}/annotations/').data, [])

    def test_capture_validation_errors(self):
        ebook_id = self.upload(make_epub()).data['id']
        self.assertEqual(self._capture(ebook_id, 'poem', {'text': 'x'}).status_code, 400)
        self.assertEqual(self._capture(ebook_id, 'word', {'word': 'x'}).status_code, 400)  # definition required

    def test_define_suggests_and_reports_outage(self):
        from apps.ebooks.definitions import DefinitionUnavailable
        with mock.patch('apps.ebooks.views.suggest_definition', return_value='blag, smiren') as suggest:
            res = self.client.post('/api/ebooks/define/', {'word': 'krotki', 'context': 'Blaženi krotki.'}, format='json')
        self.assertEqual(res.data, {'definition': 'blag, smiren'})
        suggest.assert_called_once_with('krotki', 'Blaženi krotki.')
        with mock.patch('apps.ebooks.views.suggest_definition', side_effect=DefinitionUnavailable('down')):
            self.assertEqual(self.client.post('/api/ebooks/define/', {'word': 'x'}, format='json').status_code, 503)

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
