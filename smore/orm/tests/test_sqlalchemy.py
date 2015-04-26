# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

from marshmallow import fields, validate

import pytest

from ..sqla import fields_for_model

def contains_validator(field, v_type):
    for v in field.validators:
        if isinstance(v, v_type):
            return v
    return False

class AnotherInteger(sa.Integer):
    """Use me to test if MRO works like we want"""
    pass

@pytest.fixture()
def Base():
    return declarative_base()


@pytest.fixture()
def session(Base, models):
    engine = sa.create_engine('sqlite:///:memory:', echo=False)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return Session()


@pytest.fixture()
def models(Base):

    # models adapted from https://github.com/wtforms/wtforms-sqlalchemy/blob/master/tests/tests.py
    student_course = sa.Table(
        'student_course', Base.metadata,
        sa.Column('student_id', sa.Integer, sa.ForeignKey('student.id')),
        sa.Column('course_id', sa.Integer, sa.ForeignKey('course.id'))
    )

    class Course(Base):
        __tablename__ = 'course'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(255), nullable=False)
        # These are for better model form testing
        cost = sa.Column(sa.Numeric(5, 2), nullable=False)
        description = sa.Column(sa.Text, nullable=False)
        level = sa.Column(sa.Enum('Primary', 'Secondary'))
        has_prereqs = sa.Column(sa.Boolean, nullable=False)
        started = sa.Column(sa.DateTime, nullable=False)
        grade = sa.Column(AnotherInteger, nullable=False)

    class School(Base):
        __tablename__ = 'school'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(255), nullable=False)

    class Student(Base):
        __tablename__ = 'student'
        id = sa.Column(sa.Integer, primary_key=True)
        full_name = sa.Column(sa.String(255), nullable=False, unique=True, default='noname')
        dob = sa.Column(sa.Date(), nullable=True)
        date_created = sa.Column(sa.DateTime, default=dt.datetime.utcnow)

        current_school_id = sa.Column(sa.Integer, sa.ForeignKey(School.id), nullable=False)
        current_school = relationship(School, backref=backref('students'))

        courses = relationship(
            'Course',
            secondary=student_course,
            backref=backref("students", lazy='dynamic')
        )

    # So that we can access models with dot-notation, e.g. models.Course
    class _models(object):
        def __init__(self):
            self.Course = Course
            self.School = School
            self.Student = Student
    return _models()

class TestModelFieldConversion:

    @pytest.fixture()
    def school(self, models):
        return models.School(name='Univ. Of Whales')

    @pytest.fixture()
    def student(self, models, school):
        return models.Student(full_name='Monty Python', current_school=school)

    def test_fields_for_model_types(self, models, session):
        fields_ = fields_for_model(models.Student, session=session)
        assert type(fields_['id']) is fields.Int
        assert type(fields_['full_name']) is fields.Str
        assert type(fields_['dob']) is fields.Date
        assert type(fields_['current_school_id']) is fields.Int
        assert type(fields_['date_created']) is fields.DateTime

    def test_defaults_set(self, models, session):
        fields_ = fields_for_model(models.Student, session=session)
        assert isinstance(fields_['date_created'].default, dt.datetime)
        assert fields_['full_name'].default == 'noname'

    def test_length_validator_set(self, models, session):
        fields_ = fields_for_model(models.Student, session=session)
        validator = contains_validator(fields_['full_name'], validate.Length)
        assert validator
        assert validator.max == 255

    def test_sets_nullable(self, models, session):
        fields_ = fields_for_model(models.Student, session)
        assert fields_['dob'].allow_none is True

    def test_sets_enum_choices(self, models, session):
        fields_ = fields_for_model(models.Course, session=session)
        validator = contains_validator(fields_['level'], validate.OneOf)
        assert validator
        assert validator.choices == ('Primary', 'Secondary')

    def test_many_to_many_relationship(self, models, session):
        student_fields = fields_for_model(models.Student, session=session)
        assert type(student_fields['courses']) is fields.QuerySelectList

        course_fields = fields_for_model(models.Course, session=session)
        assert type(course_fields['students']) is fields.QuerySelectList

    def test_many_to_one_relationship(self, models, session):
        student_fields = fields_for_model(models.Student, session=session)
        assert type(student_fields['current_school']) is fields.QuerySelect

        school_fields = fields_for_model(models.School, session=session)
        assert type(school_fields['students']) is fields.QuerySelectList

    def test_exclude_fk(self, models, session):
        student_fields = fields_for_model(models.Student, session=session, exclude_fk=True)
        assert 'current_school_id' not in student_fields

        student_fields2 = fields_for_model(models.Student, session=session, exclude_fk=False)
        assert 'current_school_id' in student_fields2

