# Vendored from SQLAlchemy-Utils 0.42.1.
# Copyright (c) 2012, Konsta Vesterinen. All rights reserved.
# Distributed under the BSD 3-Clause licence; see LICENSE and README.md.

from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.session import object_session


def get_bind(obj):
    """
    Return the bind for given SQLAlchemy Engine / Connection / declarative
    model object.

    :param obj: SQLAlchemy Engine / Connection / declarative model object

    ::

        from sqlalchemy_utils import get_bind


        get_bind(session)  # Connection object

        get_bind(user)

    """
    if hasattr(obj, 'bind'):
        conn = obj.bind
    else:
        try:
            conn = object_session(obj).bind
        except UnmappedInstanceError:
            conn = obj

    if not hasattr(conn, 'execute'):
        raise TypeError(
            'This method accepts only Session, Engine, Connection and '
            'declarative model objects.'
        )
    return conn


def quote(mixed, ident):
    """
    Conditionally quote an identifier.
    ::


        from sqlalchemy_utils import quote


        engine = create_engine('sqlite:///:memory:')

        quote(engine, 'order')
        # '"order"'

        quote(engine, 'some_other_identifier')
        # 'some_other_identifier'


    :param mixed: SQLAlchemy Session / Connection / Engine / Dialect object.
    :param ident: identifier to conditionally quote
    """
    if isinstance(mixed, Dialect):
        dialect = mixed
    else:
        dialect = get_bind(mixed).dialect
    return dialect.preparer(dialect).quote(ident)
