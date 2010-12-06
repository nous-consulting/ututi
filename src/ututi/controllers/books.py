from sqlalchemy import func

from sqlalchemy.sql.expression import desc
from formencode.variabledecode import NestedVariables
from sqlalchemy.orm.exc import NoResultFound
from formencode.foreach import ForEach
from formencode.compound import Pipe
from formencode import Schema, validators, htmlfill
from formencode.api import Invalid

from webhelpers import paginate

from pylons.controllers.util import  abort
from pylons.controllers.util import redirect
from pylons import request, tmpl_context as c, url
from pylons.i18n import _

from datetime import datetime

from ututi.lib.validators import PhoneNumberValidator
from ututi.lib.validators import FileUploadTypeValidator, TranslatedEmailValidator
from ututi.model import PrivateMessage
from ututi.model import Department
from ututi.model import LocationTag
from ututi.model import SearchItem
from ututi.model import Book, meta, City, BookType, SchoolGrade, ScienceType
import ututi.lib.helpers as h
from ututi.model import User
from ututi.lib.validators import LocationTagsValidator
from ututi.lib.image import serve_logo
from ututi.lib.forms import validate
from ututi.lib.search import search_query
from ututi.lib.security import ActionProtector
from ututi.lib.base import BaseController, render

class ChainedSubFormValidator(validators.FormValidator):

    dispatch_on = None
    sub_forms = {}

    def _to_python(self, value_dict, state):
        # XXX relying on the fact that field we dispatch on has a name
        return self.sub_forms.get(value_dict[self.dispatch_on].name).to_python(value_dict, state)


class BaseValidator(validators.FancyValidator):

    _notfoundmarker = object()

    def validate_python(self, value, state):
        if value is None and self.not_empty:
            raise Invalid(self.message('empty', state), value, state)
        elif value is self._notfoundmarker:
            raise Invalid(self.message('invalid', state), value, state)


class BookDepartmentValidator(BaseValidator):

    messages = {
        'invalid': _(u"Specify correct book department."),
        'empty': _(u"Specify book department.")
        }

    def _to_python(self, value, state):
        if not value:
            return None

        department = Department.getByName(value)
        if department is None:
            return self._notfoundmarker

        return department


class ScienceTypeValidator(BaseValidator):
    """A validator that tests if the selected science type is correct."""

    messages = {
        'invalid': _(u"Specify correct science type."),
        'empty': _(u"Specify science type.")
        }

    def _to_python(self, value, state):
        if not value:
            return None

        try:
            science_type_id = int(value)
        except ValueError:
            return self._notfoundmarker
        return meta.Session.query(ScienceType).filter(ScienceType.id == science_type_id).one()


def city_from_string(string, not_found=None):
    if not string:
        return None

    try:
        city_id = int(string)
    except ValueError:
        return not_found

    return meta.Session.query(City).filter(City.id == city_id).one()


class CityValidator(BaseValidator):
    """A validator for city fields."""

    messages = {
        'invalid': _(u"Selected city is not valid."),
        'empty': _(u"Specify a city please.")
        }

    def _to_python(self, value, state):
        return city_from_string(value, not_found=self._notfoundmarker)

class BookTypeValidator(BaseValidator):

    messages = {
        'invalid': _(u"Selected book type is not valid."),
        'empty': _(u"Specify book type.")
        }

    def _to_python(self, value, state):
        if not value:
            return None

        try:
            type_id = int(value)
        except ValueError:
            return self._notfoundmarker

        return meta.Session.query(BookType).filter(BookType.id == type_id).one()


class SchoolGradeValidator(BaseValidator):

    messages = {
        'invalid': _(u"Selected school grade is not valid."),
        'empty': _(u"Please specify school grade")
        }

    def _to_python(self, value, state):
        if not value:
            return None

        try:
            school_grade_id = int(value)
        except ValueError:
            return self._notfoundmarker

        return meta.Session.query(SchoolGrade).filter(SchoolGrade.id == school_grade_id).one()


class BookSubFormBase(Schema):

    allow_extra_fields = True
    logo = FileUploadTypeValidator(allowed_types=('.jpg', '.png', '.bmp', '.tiff', '.jpeg', '.gif'))
    title = validators.UnicodeString(not_empty=True)
    author = validators.UnicodeString(not_empty=True)
    price = validators.UnicodeString()
    description = validators.UnicodeString()
    delete_logo = validators.Bool()

    city = CityValidator(not_empty=True)
    book_type = BookTypeValidator(not_empty=True)

    owner_email = TranslatedEmailValidator()
    owner_name = validators.UnicodeString()
    owner_phone = PhoneNumberValidator()

    # XXX Setting default sub section values to None
    university_science_type = validators.Constant(None)
    location = validators.Constant(None)
    school_science_type = validators.Constant(None)
    school_grade = validators.Constant(None)
    other_science_type = validators.Constant(None)


class UniversityBookForm(BookSubFormBase):

    university_science_type = ScienceTypeValidator(not_empty=True)
    location = Pipe(ForEach(validators.UnicodeString(strip=True)),
                    LocationTagsValidator(not_empty=True))


class SchoolBookForm(BookSubFormBase):

    school_science_type = ScienceTypeValidator(not_empty=True)
    school_grade = SchoolGradeValidator(not_empty=True)


class OtherBookForm(BookSubFormBase):

    other_science_type = ScienceTypeValidator(not_empty=True)


class BookForm(Schema):

    pre_validators = [NestedVariables()]
    allow_extra_fields = True

    department = BookDepartmentValidator(not_empty=True)

    chained_validators = [ChainedSubFormValidator(
            dispatch_on='department',
            sub_forms = {'university': UniversityBookForm,
                         'school': SchoolBookForm,
                         'other': OtherBookForm})]


class BooksController(BaseController):

    def __before__(self):
        c.selected_books_department = None
        c.book = None
        c.book_types = meta.Session.query(BookType).all()

    def _make_pages(self, items):
        return paginate.Page(items,
                             page=int(request.params.get('page', 1)),
                             item_count=items.count() or 0,
                             items_per_page=100)



    def index(self):
        books = meta.Session.query(Book)
        c.books = self._make_pages(books)
        return render('books/index.mako')

    def _load_defaults(self):
        c.book_departments = [('', '')] + [(d.name, d.title) for d in Department.values()]
        c.school_grades = meta.Session.query(SchoolGrade).all()
        c.cities = meta.Session.query(City).all()
        self._load_science_types()

    def _load_science_types(self):
        c.university_science_types = ScienceType.getByDepartment(Department.getByName('university'))
        c.school_science_types = ScienceType.getByDepartment(Department.getByName('school'))
        c.other_science_types = ScienceType.getByDepartment(Department.getByName('other'))

    def _get_science_type(self):
        department = self.form_result['department']
        form = self.form_result
        if department.name == 'university':
            science_type = form['university_science_type']
        elif department.name == 'school':
            science_type = form['school_science_type']
        else:
            science_type = form['other_science_type']
        return science_type

    @validate(schema=BookForm, form='_add')
    @ActionProtector("user")
    def create(self):
        if hasattr(self, 'form_result'):
            title = self.form_result['title']
            price = self.form_result['price']

            science_type = self._get_science_type()

            book = Book(owner = c.user,
                        title = title,
                        price = price,
                        city = self.form_result['city'],
                        type = self.form_result['book_type'],
                        science_type = science_type,
                        department = self.form_result['department'])

            book.author = self.form_result['author']
            book.description = self.form_result['description']
            if self.form_result['logo'] is not None and self.form_result['logo'] != '':
                book.logo = self.form_result['logo'].file.read()
            book.location = self.form_result['location']
            book.owner_name = self.form_result['owner_name']
            book.owner_phone = self.form_result['owner_phone']
            book.owner_email = self.form_result['owner_email']
            book.course = self.form_result['course']
            book.school_grade = self.form_result['school_grade']
            meta.Session.add(book)
            meta.Session.commit()
            h.flash(_('Book was added succesfully'))
            redirect(url(controller='books', action='show', id=book.id))

    @ActionProtector("user")
    def _add(self):
        self._load_defaults()
        c.user_phone_number = c.user.phone_number
        last_user_book = meta.Session.query(Book).filter(Book.created == c.user).order_by(Book.id.desc()).first()
        if not(c.user_phone_number) and last_user_book:
            c.user_phone_number = last_user_book.owner_phone
        return render('books/add.mako')

    def add(self):
        return self._add()

    def show(self, id):
        c.book = meta.Session.query(Book).filter(Book.id == id).one()
        return render('books/show.mako')

    def _edit(self):
        self._load_defaults()
        return render('books/edit.mako')

    @ActionProtector("user")
    def edit(self, id):
        c.book = meta.Session.query(Book).filter(Book.id == id).one()
        if c.book.created != c.user:
            h.flash(_('Only owner of this book can do this action'))
            redirect(url(controller="books", action="index"))

        department_control_id = c.book.department.name + '_science_type'
        defaults = {
            'id': c.book.id,
            'title': c.book.title,
            'author': c.book.author,
            'course': c.book.course,
            'school_grade': (c.book.school_grade.id if c.book.school_grade else None),
            department_control_id: c.book.science_type.id,
            'description': c.book.description,
            'price': c.book.price,
            'department': c.book.department.name,
            'city': c.book.city.id,
            'book_type': c.book.type.id,
            'owner_name': c.book.owner_name,
            'owner_phone': c.book.owner_phone,
            'owner_email': c.book.owner_email
        }

        if c.book.location is not None:
            location = dict([('location-%d' % n, tag)
                             for n, tag in enumerate(c.book.location.hierarchy())])
        else:
            location = []

        defaults.update(location)

        self._load_defaults()
        return htmlfill.render(self._edit(), defaults=defaults)

    @validate(BookForm, form='_edit')
    @ActionProtector("user")
    def update(self):
        if hasattr(self, 'form_result'):
            book = meta.Session.query(Book).filter(Book.id == self.form_result['id']).one()
            book.title = self.form_result['title']
            book.price = self.form_result['price']
            book.city = self.form_result['city']
            book.type = self.form_result['book_type']
            book.science_type = self._get_science_type()
            book.department = self.form_result['department']
            book.author = self.form_result['author']
            book.description = self.form_result['description']
            if self.form_result['delete_logo'] == True:
                book.logo = None
            elif self.form_result['logo'] is not None and self.form_result['logo'] != '':
                book.logo = self.form_result['logo'].file.read()
            book.location = self.form_result['location']
            book.owner_name = self.form_result['owner_name']
            book.owner_phone = self.form_result['owner_phone']
            book.owner_email = self.form_result['owner_email']
            book.course = self.form_result['course']
            book.school_grade = self.form_result['school_grade']
            book.reset_expiration_time()
            meta.Session.commit()
            h.flash(_('Book was updated succesfully'))
            redirect(url(controller='books', action='show', id=book.id))

    def logo(self, id, width=None, height=None):
        return serve_logo('book', int(id), width=width, height=height)

    def search(self):
        c.search_text = request.params.get('text', '')
        c.selected_city_id = request.params.get('city', '')
        c.selected_city = city_from_string(c.selected_city_id)
        search_results = search_query(text=c.search_text, obj_type='book')

        books = search_results
        if c.selected_city is not None:
            books = (search_results
                     .join((Book, Book.id == SearchItem.content_item_id))
                     .join(City).filter(City.id == c.selected_city.id))

        cities = meta.Session.query(City.id,
                                    City.name,
                                    func.count(Book.id.distinct()).label('book_count'))\
            .join(Book, search_results.subquery()).filter(Book.id != None).group_by(City.name, City.id).order_by(desc('book_count')).all()

        c.filter_cities = [('', _("All cities (%(book_count)s)") % {'book_count': search_results.count()})]

        for city_id, city_name, book_count in cities:
            c.filter_cities.append((city_id, _("%(city)s (%(book_count)s)" % {
                            'city': city_name,
                            'book_count': book_count})))

        c.books = self._make_pages(books)
        return render('books/search.mako')

    def catalog(self, books_department=None, books_type_name=None, science_type_id=None, location_id=None, school_grade_id=None):
        c.selected_books_department = books_department
        c.books_department = books_department
        school_grade = None
        science_type = None
        location = None

        c.current_science_types = []
        c.book_department = None
        if books_department is not None:
            c.book_department = Department.getByName(books_department)
            c.current_science_types = ScienceType.getByDepartment(c.book_department)

        c.url_params = {}
        c.books_type = None
        if books_type_name is not None:
            c.books_type = meta.Session.query(BookType).filter(BookType.name==books_type_name).one()
            c.url_params['books_type_name'] = books_type_name

        if location_id is not None:
            location = meta.Session.query(LocationTag).filter(LocationTag.id == location_id).one()

        c.locations = None
        c.school_grades = None
        if c.book_department is not None:
            if c.book_department.name == "university":
                if location_id is not None and location is not None:
                    if location.parent is not None:
                        c.locations = meta.Session.query(LocationTag
                                                         ).filter(LocationTag.parent == location.parent
                                                                  ).order_by(LocationTag.title.asc())
                    else:
                        c.locations = meta.Session.query(LocationTag
                                                         ).filter(LocationTag.parent == location
                                                                  ).order_by(LocationTag.title.asc())
                else:
                    c.locations = meta.Session.query(LocationTag
                                                     ).filter(LocationTag.parent == None
                                                              ).order_by(LocationTag.title.asc())
            elif books_department == "school":
                c.school_grades = meta.Session.query(SchoolGrade)
                if school_grade_id is not None:
                    school_grade = meta.Session.query(SchoolGrade).filter(SchoolGrade.id == school_grade_id).one()

        c.science_type = None
        if science_type_id is not None:
            c.science_type = meta.Session.query(ScienceType).filter(ScienceType.id == science_type_id).one()

        #book filtering:
        books = meta.Session.query(Book)
        if location is not None:
            children = [child.id for child in location.flatten]
            books = books.filter(Book.location_id.in_(children))
        if c.book_department is not None:
            books = books.filter(Book.department_id == c.book_department.id)
        if school_grade is not None:
            books = books.filter(Book.school_grade == school_grade)
        if c.books_type is not None:
            books = books.filter(Book.type == c.books_type)
        if c.science_type is not None:
            books = books.filter(Book.science_type == c.science_type)
        c.books = self._make_pages(books)
        return render('books/catalog.mako')

    @ActionProtector("user")
    def my_books(self):
        books = meta.Session.query(Book).filter(Book.created == c.user)
        c.active_books = books.filter(Book.valid_until >= datetime.utcnow()).all()
        c.expired_books = books.filter(Book.valid_until < datetime.utcnow()).all()
        c.owned_books_number = len(c.active_books) + len(c.expired_books)
        return render('books/my_books.mako')

    @ActionProtector("user")
    def restore_book(self, id):
        book = meta.Session.query(Book).filter(Book.id == id).one()
        if c.user == book.created:
            book.reset_expiration_time()
            meta.Session.commit()
        else:
            h.flash(_("You don't have rights to make this action"))
        redirect(url(controller="books", action="my_books"))

    @ActionProtector("user")
    def private_message(self):
        user_id = request.params.get('user_id')
        c.book = meta.Session.query(Book).filter(Book.id == request.params.get('book_id')).one()
        try:
            c.recipient = meta.Session.query(User).filter_by(id=c.book.created.id).one()
        except NoResultFound:
            abort(404)

        if 'message' in request.params:
            message_text = """%(user_name)s sent you a private message, asking about book %(book_title)s (%(book_url)s):

                           %(message)s""" % {"user_name" : c.user.fullname,
                                "book_url" : url(qualified=True, controller="books", action="show", id=c.book.id),
                                "book_title" : c.book.title,
                                "message" : request.params.get('message')}

            msg = PrivateMessage(c.user, c.recipient,
                                 _("%(ubooks_label)s: %(user_name)s asks about book %(book_title)s") %\
                                     {"ubooks_label" : _('uBooks'), "user_name" : c.user.fullname, "book_title" : c.book.title},
                                  message_text)
            meta.Session.add(msg)
            meta.Session.commit()
            h.flash(_('Message sent.'))
        return render('books/show.mako')
