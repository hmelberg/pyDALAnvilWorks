"""Functions here over-write functions defined in _anvil_designer/componentsUI/users/Users.py"""
import os
from warnings import warn

import pydal.objects
import tests.pydal_def as mydal
from pydal import Field
from _anvil_designer.componentsUI.anvilUsers import *


def add_row(**kwargs):
    row_ref = mydal.db['users'].insert(**kwargs)
    mydal.db.commit()
    return row_ref


def get_by_id(id):
    return mydal.db.users(id)


def logout(user=None):
    """Forget the current logged-in user (Not on anvil.works: user argument will log out that user)"""
    if user:
        query = mydal.db.logged_in_users.user_ref == user.id
        mydal.db(query).delete()
        return
    pid = os.getpid()
    current_test = os.getenv('PYTEST_CURRENT_TEST')
    query = (mydal.db.logged_in_users.pid == pid) \
        & (mydal.db.logged_in_users.pytest == current_test)
    mydal.db(query).delete()
    mydal.db.commit()
    return


def force_login(user_row, remember=False):
    """Set the specified user object (a row from a Data Table) as the current logged-in user.
    It must be a row from the users table. By default, login status is not remembered between sessions."""
    if 'logged_in_users' not in mydal.db.tables:
        mydal.db.define_table('logged_in_users', Field('user_ref', type='reference users'),
                              Field('pid', type='integer'),
                              Field('pytest', 'string'))
    pid = os.getpid()
    current_test = os.getenv('PYTEST_CURRENT_TEST')
    if current_test is None or len(current_test) == 0:
        raise ValueError("PYTEST_CURRENT_TEST is null")
    login = mydal.db((mydal.db.logged_in_users.pid == pid) & (mydal.db.logged_in_users.pytest == current_test)).select()
    if len(login) == 0:
        new_log = mydal.db.logged_in_users.insert(user_ref=user_row,
                                                  pid=pid,
                                                  pytest=current_test)
        mydal.db.commit()
    # else user already logged in
    return


def get_user(allow_remembered=True) -> pydal.helpers.classes.Reference:
    """Get the row from the users table that corresponds to the currently logged-in user.
    If allow_remembered is true (the default), the user may have logged in in a previous session.
    Returns None if no user is logged in."""
    pass
    """Retrieves the user in database corresponding to pid

    Why is there an extra table ``logged_in_users`` ?!?

    So that the returned user is a reference and not a row (pyDAL). Also logged_in_users contains the pid of the test.
    Tests can run in parallel, so the correct user is important."""

    def get_user_with_pid():
        pid = os.getpid()
        current_test = os.getenv('PYTEST_CURRENT_TEST')
        assert current_test
        query = (mydal.db.logged_in_users.pid == pid) & \
                (mydal.db.logged_in_users.pytest == current_test)
        rows = mydal.db(query).select()
        if len(rows) == 1:
            return rows[0]
        elif len(rows) == 0:
            warn(UserWarning("No user logged in. Use 'force_login(user)'."))
            return None
        else:
            raise ValueError("More than one user is logged in for the same pid.")

    if mydal.db is None:
        raise ConnectionError("Database not connected")
    logged_in_user = get_user_with_pid()
    if logged_in_user:
        return logged_in_user.user_ref
    return None
