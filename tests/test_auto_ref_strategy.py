# -*- coding: utf-8 -*-
import pytest
from apispec.auto_ref_strategy import default_schema_class_resolver
from .schemas import PetSchema


class TestDefaultSchemaClassResolver:

    @pytest.mark.parametrize('schema', [PetSchema])
    def test_cls(self, schema):
        cls = default_schema_class_resolver(schema)
        assert cls == PetSchema
        assert len(cls.opts.exclude) == 0
        assert not getattr(cls, '_schema_name', None)

    @pytest.mark.parametrize('schema', [PetSchema()])
    def test_instance_simple(self, schema):
        cls = default_schema_class_resolver(schema)
        assert cls == PetSchema
        assert len(cls.opts.exclude) == 0
        assert not getattr(cls, '_schema_name', None)

    @pytest.mark.parametrize('schema', [PetSchema(only=('id',))])
    def test_instance_only(self, schema):
        cls = default_schema_class_resolver(schema)
        cls2 = default_schema_class_resolver(schema)
        assert isinstance(cls, type)
        assert cls != PetSchema
        assert cls == cls2
        assert len(cls.opts.exclude) == 1
        assert 'name' in cls.opts.exclude
        assert getattr(cls, '_schema_name', None)

    @pytest.mark.parametrize('schema', [PetSchema(exclude=('id',))])
    def test_instance_exclude(self, schema):
        cls = default_schema_class_resolver(schema)
        cls2 = default_schema_class_resolver(schema)
        assert isinstance(cls, type)
        assert cls != PetSchema
        assert cls == cls2
        assert len(cls.opts.exclude) == 1
        assert 'id' in cls.opts.exclude
        assert getattr(cls, '_schema_name', None)
