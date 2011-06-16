import argparse

import imp
import sys

from unittest import TestCase

from httplib2 import ServerNotFoundError
from mock import (Mock, patch)
from nose.tools import (assert_equals, assert_false, raises)

from gh_bugs import utils


class Colouriser(TestCase):
    @patch('sys.stdout')
    def test_is_not_a_tty_colour(self, stdout):
        stdout.isatty = Mock(return_value=False)
        assert_false(sys.stdout.isatty())
        assert_equals(utils.success('test'), 'test')
        assert_equals(utils.fail('test'), 'test')
        assert_equals(utils.warn('test'), 'test')

    @patch('sys.stdout')
    def test_colouriser(self, stdout):
        stdout.isatty = Mock(return_value=True)

        # This horrific-ness is here as the .isatty() test happens at import
        # time, so we need to re-import for tests.
        utils_file = open('gh_bugs/utils.py')
        new_utils = imp.load_module("new_utils", utils_file, utils_file.name,
                           (".py", utils_file.mode, imp.PY_SOURCE))

        assert_equals(new_utils.success('test'), '\x1b[32mtest\x1b[0m')
        assert_equals(new_utils.fail('test'), '\x1b[31mtest\x1b[0m')
        assert_equals(new_utils.warn('test'), '\x1b[33mtest\x1b[0m')
        del sys.modules['new_utils']


class ProjectAction(TestCase):
    def setUp(self):
        self.parser = utils.argh.ArghParser('test_parser')
        # Stub out ._print_message() to stop help messages being displayed on
        # stderr during tests.
        self.parser._print_message = Mock(return_value=True)
        self.namespace = argparse.Namespace()
        self.action = utils.ProjectAction([], '')

    @patch('gh_bugs.utils.get_github_api')
    @patch('gh_bugs.utils.get_git_config_val')
    def test_repo_name(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = 'JNRowe'

        self.action(self.parser, self.namespace, 'misc-overlay')
        assert_equals(self.namespace.project, 'JNRowe/misc-overlay')

        self.action(self.parser, self.namespace, 'JNRowe/misc-overlay')
        assert_equals(self.namespace.project, 'JNRowe/misc-overlay')

        self.action(self.parser, self.namespace, 'ask/python-github2')
        assert_equals(self.namespace.project, 'ask/python-github2')

    @patch('gh_bugs.utils.get_github_api')
    @patch('gh_bugs.utils.get_git_config_val')
    @raises(SystemExit)
    def test_no_user(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = Mock(return_value=True)
        get_git_config_val.return_value = None
        self.action(self.parser, self.namespace, 'misc-overlay')

    @patch('gh_bugs.utils.get_github_api')
    @patch('gh_bugs.utils.get_git_config_val')
    @raises(SystemExit)
    def test_repo_not_found(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = \
            Mock(side_effect=RuntimeError('Repository not found'))
        get_git_config_val.return_value = None
        self.action(self.parser, self.namespace, 'JNRowe/never_exist')

    @patch('gh_bugs.utils.get_github_api')
    @patch('gh_bugs.utils.get_git_config_val')
    @raises(RuntimeError)
    def test_random_error(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = \
            Mock(side_effect=RuntimeError('something went wrong'))
        get_git_config_val.return_value = None
        self.action(self.parser, self.namespace, 'JNRowe/misc-overlay')

    @patch('gh_bugs.utils.get_github_api')
    @patch('gh_bugs.utils.get_git_config_val')
    @raises(SystemExit)
    def test_httplib2_error(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = Mock(side_effect=ServerNotFoundError())
        get_git_config_val.return_value = None
        self.action(self.parser, self.namespace, 'JNRowe/misc-overlay')

    @patch('gh_bugs.utils.get_github_api')
    @patch('gh_bugs.utils.get_git_config_val')
    @raises(SystemExit)
    def test_env_error(self, get_git_config_val, get_github_api):
        get_github_api().repos.show = \
            Mock(side_effect=EnvironmentError('config broken'))
        get_git_config_val.return_value = None
        self.action(self.parser, self.namespace, 'JNRowe/misc-overlay')
