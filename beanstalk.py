import threading, shutil, sublime, sublime_plugin, re, os
import json
import urllib.parse as urllib
from functools import wraps
from os.path import dirname, normpath, join
from pprint import pformat

DEFAULT_SETTINGS = {'debug_mode': False}
plugin_dir = os.path.abspath(os.path.dirname(__file__))
settings = {}
debug_mode = False

def plugin_loaded():
    global settings, debug_mode
    settings = sublime.load_settings('Beanstalk Tools.sublime-settings')
    if settings.get('debug_mode'):
        debug_mode = settings.get('debug_mode')

# Errors #################################################################


class NotASvnRepositoryError(Exception):
    pass


class NotAGitRepositoryError(Exception):
    pass


class NotABeanstalkRepositoryError(Exception):
    pass


class GitCommandError(Exception):
    pass

# Decorators #############################################################


def require_file(func):
    @wraps(func)
    def wrapper(self):
        if self.filename():
            return func(self)
        sublime.message_dialog("Please open a file first.")
    return wrapper

def with_repository(func):
    @wraps(func)
    def wrapper(self):
        try:
            self.repository = self.detect_repository()
            return func(self, self.repository)
        except (NotASvnRepositoryError, NotAGitRepositoryError,
                NotABeanstalkRepositoryError):
            sublime.error_message(
                "Beanstalk Subversion or Git repository not found at %s." %
                self.rootdir())
    return wrapper


def handle_vcs_errors_gracefully(func):
    @wraps(func)
    def wrapper(*args):
        try:
            return func(*args)
        except GitCommandError as e:
            display_error_message(e.__str__())
    return wrapper


# From handy: https://github.com/Suor/handy
def cached_property(func):
    @property
    @wraps(func)
    def wrapper(self):
        attname = '_' + func.__name__
        if not hasattr(self, attname):
            setattr(self, attname, func(self))
        return getattr(self, attname)
    return wrapper

# Repositories ###########################################################

class GitRepo(object):
    def __init__(self, path):
        self.path = path

        if not self.is_git():
            raise NotAGitRepositoryError

        self.info = self.get_info()

        if not self.info:
            raise NotABeanstalkRepositoryError

        log("Parsed GIT repo: ", pformat(self.info))

    def git(self, command):
        os.chdir(self.path)
        log("Executing `git %s` at %s." % (command, self.path))

        f = os.popen("git %s" % command)
        output = f.read().strip()
        exit_code = f.close()

        if exit_code:
            raise GitCommandError("Failed to execute `git %s` at %s" %
                                  (command, self.path))
        return output

    def get_info(self):
        return self.parse_remotes(self.git("remote -v"))

    def path_from_rootdir(self, filename):
        rootdir = normpath(self.git("rev-parse --show-toplevel"))
        if self.path != rootdir:
            _, _, path_from_rootdir = self.path.partition(rootdir)
            return strip_leading_slashes(join(path_from_rootdir, filename))
        return filename

    @property
    def branch(self):
        return self.parse_branch(self.git("branch"))

    @property
    def revision(self):
        return self.git("rev-parse HEAD")

    def parse_remotes(self, remotes):
        remotes = map(
            lambda l: tuple(re.split("\s", l)[0:2]), remotes.splitlines())
        return self.choose_remote(remotes)

    def parse_branch(self, branches):
        p = re.compile("\* (.+)")
        m = p.findall(branches)
        return m[0] if m else None

    def is_git(self):
        os.chdir(self.path)
        code = os.system('git rev-parse')
        return not code

    def choose_remote(self, remotes):
        for remote_alias, remote in remotes:
            beanstalk_remote = self.parse_remote(remote_alias, remote)
            if beanstalk_remote:
                return beanstalk_remote

        return None

    def parse_remote(self, remote_alias, remote):
        if remote.startswith('git@') and 'beanstalkapp.com' in remote:
            return self.parse_ssh_remote(remote_alias, remote)
        elif remote.startswith('https://') and 'git.beanstalkapp.com' in remote:
            return self.parse_http_remote(remote_alias, remote)
        return None

    def parse_ssh_remote(self, remote_alias, remote):
        uri = remote[4:-4]
        protocol = 'ssh'
        account = uri.split('.')[0]
        name = uri.split('/')[-1]

        return {
            'remote_alias': remote_alias,
            'protocol': 'ssh',
            'web_uri': uri.replace(':/' + account, '')
                          .replace(':', '')
                          .replace("git.beanstalkapp.com", "beanstalkapp.com"),
            'remote_uri': remote,
            'repository_name': name,
            'account': account,
            'username': '',
            'password': ''
        }

    def parse_http_remote(self, remote_alias, remote):
        remote_uri = remote[8:].split("@")[-1]
        uri = remote[8:-4].replace("git.beanstalkapp.com", "beanstalkapp.com")
        web_uri = uri.split("@")[-1]
        name = web_uri.split('/')[-1]
        account = web_uri.split('.')[0]
        username, password = extract_http_auth_credentials(uri)

        return {
            'remote_alias': remote_alias,
            'protocol': 'http',
            'web_uri': web_uri,
            'remote_uri': remote_uri,
            'repository_name': name,
            'account': account,
            'username': username,
            'password': password
        }

    def parse_heads(self, heads):
        f = lambda l: tuple(re.split("\s", l.replace('refs/heads/', ''))[::-1])
        return dict(map(f, heads.splitlines()))

    def browse_file_url(self, filename):
        return git_browse_file_url(self.info['web_uri'],
                                   self.path_from_rootdir(filename), self.branch)

    def blame_file_url(self, filename):
        return git_blame_file_url(
            self.info['web_uri'], self.path_from_rootdir(filename),
            self.revision, self.branch)

    def preview_file_url(self, filename):
        return git_preview_file_url(
            self.info['web_uri'], self.path_from_rootdir(filename),
            self.revision, self.branch)

    def activity_url(self):
        return activity_url(self.info['web_uri'])

    def deployments_url(self):
        return deployments_url(self.info['web_uri'])

    @property
    def name(self):
        return self.info['repository_name']

    @property
    def http_url(self):
        return "https://%s:%s@%s" % (self.info['username'],
                                     self.info['password'],
                                     self.http_uri)

    @property
    def http_uri(self):
        if self.info['protocol'] == 'http':
            return self.info['remote_uri']
        else:
            return self.info['web_uri'].replace('beanstalkapp.com',
                                                'git.beanstalkapp.com') + '.git'


class SvnRepo(object):
    def __init__(self, path):
        self.path = path

        if not self.is_svn():
            raise NotASvnRepositoryError

        self.info = self.get_info()

        if not self.info:
            raise NotABeanstalkRepositoryError

        log("Parsed SVN repository info:", pformat(self.info))

    def get_info(self):
        svn_info = self.svn("info")

        return self.load_svn_info(svn_info)

    def load_svn_info(self, svn_info):
        if not 'svn.beanstalkapp.com' in svn_info:
            return None

        info = self.parse_svn_info(svn_info)

        root_url = info['Repository Root']
        root_uri = root_url[8:].replace('svn.beanstalkapp.com',
                                        'beanstalkapp.com')
        username, password = extract_http_auth_credentials(root_uri)
        web_uri = root_uri.split('@')[-1]
        url = info['URL']
        uri = url[8:].split('@')[-1]
        branch = strip_leading_slashes(url.replace(root_url, ''), True)
        repository_name = web_uri.split('/')[-1]
        account = web_uri.split('.')[0]
        revision = int(info['Revision'])

        return {
            'protocol': 'http',
            'web_uri': web_uri,
            'uri': uri,
            'repository_name': repository_name,
            'branch': branch,
            'account': account,
            'username': username,
            'password': password,
            'revision': revision
        }

    def svn(self, command):
        os.chdir(self.path)
        log("Executing `svn %s` at %s." % (command, self.path))
        return os.popen("svn %s" % command).read().strip()

    def parse_svn_info(self, svn_info):
        return dict(tuple(line.split(': ', 1)) for line in svn_info.splitlines())

    @property
    def repository_path(self):
        return self.info['web_uri']

    @property
    def branch(self):
        return self.info['branch']

    @property
    def revision(self):
        return self.info['revision']

    def browse_file_url(self, filename):
        return svn_browse_file_url(self.repository_path, filename, self.branch)

    def blame_file_url(self, filename):
        return svn_blame_file_url(self.repository_path, filename,
                                  self.revision, self.branch)

    def preview_file_url(self, filename):
        return svn_preview_file_url(self.repository_path, filename,
                                    self.revision, self.branch)

    def deployments_url(self):
        return deployments_url(self.repository_path)

    def activity_url(self):
        return activity_url(self.repository_path)

    def is_svn(self):
        os.chdir(self.path)
        code = os.system('svn info')
        return not code

    @property
    def name(self):
        return self.info['repository_name']


# Command ################################################################


class BeanstalkWindowCommand(sublime_plugin.WindowCommand):
    def rootdir(self):
        if self.filename():
            return dirname(self.filename())
        return self.first_folder()

    def first_folder(self):
        return self.window.folders()[0]

    def relative_filename(self):
        _, _, filename = self.filename().partition(self.rootdir())
        return strip_leading_slashes(filename)

    def filename(self):
        if self.window.active_view():
            return self.window.active_view().file_name()
        return None

    def detect_repository(self):
        try:
            return GitRepo(self.rootdir())
        except (NotAGitRepositoryError, NotABeanstalkRepositoryError):
            pass

        try:
            return SvnRepo(self.rootdir())
        except (NotASvnRepositoryError, NotABeanstalkRepositoryError):
            pass

        raise NotABeanstalkRepositoryError

# From funcy: https://github.com/Suor/funcy
def partition(n, step, seq=None):
    if seq is None:
        return partition(n, n, step)
    return [seq[i:i + n] for i in xrange(0, len(seq) - n + 1, step)]


def log(*lines):
    if not debug_mode:
        return

    for line in lines:
        print(line)


def display_error_message(message, on_done=None):
    def display_error():
        sublime.error_message(message)
        if on_done:
            on_done()
    sublime.set_timeout(display_error, 10)


def copy_and_open_default_settings():
    user_settings_path = join(sublime.packages_path(), 'User',
                              'Beanstalk Tools.sublime-settings')

    if not os.path.exists(user_settings_path):
        with open(user_settings_path, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, sort_keys=True,
                      indent=4, separators=(',', ': '))

    sublime.active_window().open_file(user_settings_path)


def extract_http_auth_credentials(uri):
    username = password = ''
    if '@' in uri:
        username, password = (uri.split('@')[0].split(':') + [''])[:2]
    return (username, password)


def strip_leading_slashes(path, unix_only=False):
    if unix_only:
        slash = '/'
    else:
        slash = os.sep
    return path.lstrip(slash)


# Taken from Ruby stdlib
def shellescape(str):
    if not len(str):
        return "''"
    else:
        return re.sub('([^A-Za-z0-9_\-.,:\/@\n])', "\\\\\\1", str)


def activity_url(repository):
    return "https://%s" % (repository)


def deployments_url(repository):
    return "https://%s/environments" % (repository)


def git_browse_file_url(repository, filepath, branch='master'):
    return "https://%s/browse/git/%s?ref=b-%s" % \
        (repository, filepath, urllib.quote(branch))


def git_blame_file_url(repository, filepath, revision, branch='master'):
    return "https://%s/blame/%s?ref=b-%s&rev=%s" % \
        (repository, filepath, urllib.quote(branch), revision)


def git_preview_file_url(repository, filepath, revision, branch='master'):
    return "https://%s/previews/%s?back_to=file&ref=b-%s&rev=%s" % \
        (repository, filepath, urllib.quote(branch), revision)


def svn_browse_file_url(repository, filepath, branch='master'):
    return "https://%s/browse/%s/%s" % (repository, branch, filepath)


def svn_blame_file_url(repository, filepath, revision, branch='master'):
    return "https://%s/blame/%s/%s?rev=%s" % \
        (repository, branch, filepath, revision)


def svn_preview_file_url(repository, filepath, revision, subpath=''):
    return "https://%s/previews/%s/%s?back_to=file&rev=%s" % \
        (repository, subpath, filepath, revision)
