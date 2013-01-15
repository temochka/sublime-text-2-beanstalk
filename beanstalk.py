import sublime, sublime_plugin
from xml.dom.minidom import parseString
from os.path import dirname, normpath, join
import re, os
from functools import wraps
from pprint import pformat, pprint
from beanstalk_api import *
from osx_keychain import with_osx_keychain_support
import threading
import shutil
import sys

settings = sublime.load_settings('Beanstalk Tools.sublime-settings')
plugin_dir = os.path.abspath(os.path.dirname(__file__))
debug_mode = False
if settings.get('debug_mode'):
  debug_mode = settings.get('debug_mode')

# Errors #######################################################################

class NotASvnRepositoryError(Exception):
  pass

class NotAGitRepositoryError(Exception):
  pass

class NotABeanstalkRepositoryError(Exception):
  pass

class GitCommandError(Exception):
  pass

# Repositories #################################################################

class BeanstalkRepo:
  def __init__(self):
    self._api_client = None
    self._beanstalk_id = None

  @property
  def api_client(self):
    if self._api_client:
      return self._api_client
    self._api_client = APIClient(self.info['account'], self.info['username'],
                                 self.info['password'])
    return self._api_client

  @property
  def beanstalk_id(self):
    if self._beanstalk_id:
      return self._beanstalk_id

    repositories = self.api_client.repositories()

    for repository in repositories:
      if repository['repository']['name'] == self.name:
        log("Repository ID: %d" % repository['repository']['id'])
        self._beanstalk_id = repository['repository']['id']
        return self._beanstalk_id

    return None

  @property
  def environments(self):
    return self.api_client.environments(self.beanstalk_id)

  def release(self, environment_id, revision, message=""):
    return self.api_client.release(self.beanstalk_id, environment_id,
                                   revision, message)

class GitRepo(BeanstalkRepo):
  def __init__(self, path):
    self.path = path

    if not self.is_git():
      raise NotAGitRepositoryError

    self.info = self.info()

    if not self.info:
      raise NotABeanstalkRepositoryError

    BeanstalkRepo.__init__(self)
    log("Parsed GIT repo: ", pformat(self.info))

  def git(self, command):
    os.chdir(self.path)
    f = os.popen("git %s" % command)
    output = f.read().strip()
    exit_code = f.close()

    if exit_code:
      raise GitCommandError("Failed to execute `git %s` at %s" % \
                            (command, self.path))
    return output

  def info(self):
    return self.parse_remotes(self.git("remote -v"))

  def path_from_rootdir(self, filename):
    rootdir = self.git("rev-parse --show-toplevel")
    if self.path != rootdir:
      _, _, path_from_rootdir = self.path.partition(rootdir)
      return strip_leading_slashes(join(path_from_rootdir, filename))
    return filename

  def branch(self):
    return self.parse_branch(self.git("branch"))

  def revision(self):
    return self.git("rev-parse HEAD")

  def browse_file_url(self, filename):
    return git_browse_file_url(self.info['url'],
                               self.path_from_rootdir(filename), self.branch())

  def blame_file_url(self, filename):
    return git_blame_file_url(
        self.info['url'], self.path_from_rootdir(filename),
        self.revision(), self.branch())

  def preview_file_url(self, filename):
    return git_preview_file_url(
        self.info['url'], self.path_from_rootdir(filename),
        self.revision(), self.branch())

  def parse_remotes(self, remotes):
    remotes = map(lambda l: tuple(re.split("\s", l)[0:2]), remotes.splitlines())
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
    url = remote[4:-4].replace(":", "")
    protocol = 'ssh'
    account = url.split('.')[0]
    name = url.split('/')[-1]

    return {
      'remote_alias': remote_alias,
      'protocol' : 'ssh',
      'url' : url,
      'remote_uri' : remote,
      'repository_name' : name,
      'account' : account,
      'username' : '',
      'password' : ''
    }

  def parse_http_remote(self, remote_alias, remote):
    uri = remote[8:-4].replace("git.beanstalkapp.com", "beanstalkapp.com")
    url = uri.split("@")[-1]
    name = url.split('/')[-1]
    account = url.split('.')[0]
    username = ''
    password = ''

    if '@' in uri:
      username, password = uri.split("@")[0].split(':').append('')

    return {
      'remote_alias' : remote_alias,
      'protocol' : 'http',
      'url' : url,
      'remote_uri' : remote[8:],
      'repository_name' : name,
      'account' : account,
      'username' : username,
      'password' : password
    }

  def fetch_remote_heads(self):
    return self.parse_heads(self.git('ls-remote -h ' + self.remote_url))

  def parse_heads(self, heads):
    f = lambda l: tuple(re.split("\s", l.replace('refs/heads/', ''))[::-1])
    return dict(map(f, heads.splitlines()))

  def activity_url(self):
    return activity_url(self.info['url'])

  def deployments_url(self):
    return deployments_url(self.info['url'])

  def release_environment_url(self, environment_id):
    return release_environment_url(self.info['url'], environment_id)

  @property
  def name(self):
    return self.info['repository_name']

  @property
  def remote_url(self):
    if self.info['protocol'] == 'http':
      return "https://%s:%s@%s" % (self.info['username'], self.info['password'],
                                   self.info['remote_uri'])
    else:
      return self.info['remote_uri']

  def release_thread(self):
    return ReleaseThread

  def prepare_release_thread(self):
    return PrepareGitReleaseThread

  def supports_deployments(self):
    return true

class SvnRepo(BeanstalkRepo):
  def __init__(self, path):
    self.path = path

    if not self.is_svn():
      raise NotASvnRepositoryError

    self.info = self.get_info()

    if not self.info:
      raise NotABeanstalkRepositoryError

    log("Parsed SVN repository info:", pformat(self.info))
    BeanstalkRepo.__init__(self)

  def get_info(self):
    svn_info = self.svn("info")

    return self.parse_svn_info(svn_info)

  def parse_svn_info(self, svn_info):
    if not 'svn.beanstalkapp.com' in svn_info:
      return None

    dom = parseString(svn_info)

    root_url = dom.getElementsByTagName('root')[0].firstChild.data
    root_uri = root_url[8:].replace('svn.beanstalkapp.com', 'beanstalkapp.com')
    username, password = extract_http_auth_credentials(root_uri)
    web_uri = root_uri.split('@')[-1]
    url = dom.getElementsByTagName('url')[0].firstChild.data
    branch = strip_leading_slashes(url.replace(root_url, ''))
    repository_name = web_uri.split('/')[-1]
    account = web_uri.split('.')[0]
    revision = dom.getElementsByTagName("commit")[0].attributes["revision"].value

    return {
      'protocol' : 'http',
      'web_uri' : web_uri,
      'url' : url,
      'repository_name' : repository_name,
      'branch' : branch,
      'account' : account,
      'username' : username,
      'password' : password,
      'revision' : revision
    }

  def svn(self, command):
    os.chdir(self.path)
    return os.popen("svn %s --xml" %(command)).read()

  @property
  def repository_path(self):
    return self.info['web_uri']

  def branch(self):
    return self.info['branch']

  def revision(self):
    return self.info['revision']

  def browse_file_url(self, filename):
    return svn_browse_file_url(self.repository_path, filename, self.branch())

  def blame_file_url(self, filename):
    return svn_blame_file_url(self.repository_path, filename,
                              self.revision(), self.branch())

  def preview_file_url(self, filename):
    return svn_preview_file_url(self.repository_path, filename,
                                self.revision(), self.branch())

  def is_svn(self):
    os.chdir(self.path)
    code = os.system('svn info')
    return not code

  @property
  def name(self):
    return self.info['repository_name']

  def activity_url(self):
    return activity_url(self.repository_path)

  def deployments_url(self):
    return deployments_url(self.repository_path)

  def supports_deployments(self):
    return true

  def remote_revision(self):
    svn_info = self.svn("info %s" % self.info['url'])
    dom = parseString(svn_info)
    revision = dom.getElementsByTagName("commit")[0].attributes["revision"].value
    return revision

  def release_thread(self):
    return ReleaseThread

  def prepare_release_thread(self):
    return PrepareSvnReleaseThread

  def release_environment_url(self, environment_id):
    return release_environment_url(self.info['web_uri'], environment_id)

# Decorators ###################################################################
def require_file(func):
  @wraps(func)
  def wrapper(self):
    if self.filename():
      return func(self)
    sublime.message_dialog("Please open a file first.")
  return wrapper

def require_http_credentials(func):
  @wraps(func)
  def wrapper(self, repository):
    if repository.info['username'] and repository.info['password']:
      return func(self, repository)

    log("Remote-level premissions are not present")
    
    username, password = get_credentials(repository.info['account'])

    if username and password:
      repository.info['username'] = username
      repository.info['password'] = password
      return func(self, repository)
    else:
      display_error_message(
        "HTTP credentials are required to perform this action.",
        copy_and_open_default_settings
      )

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
                  "Beanstalk Subversion or Git repository not found at %s." % \
                  self.rootdir())
  return wrapper

def handle_http_errors_gracefully(func):
  @wraps(func)
  def wrapper(*args):
    try:
      return func(*args)
    except HTTPUnauthorizedError:
      display_error_message("Invalid Beanstalk API credentials.", 
                            copy_and_open_default_settings)
    except HTTPInternalServerError:
      display_error_message(
          "Oops! Beanstalk API responded with 500 Internal Server Error." \
          "Make sure the API is enabled on your Beanstalk account.")
  return wrapper

def handle_vcs_errors_gracefully(func):
  @wraps(func)
  def wrapper(*args):
    try:
      return func(*args)
    except GitCommandError as e:
      display_error_message(e.__str__())
  return wrapper


# Threads ######################################################################

class PrepareGitReleaseThread(threading.Thread):
  def __init__(self, window, repository, on_done):
    self.repository = repository
    self.window = window
    self.on_done = on_done

    threading.Thread.__init__(self)

  @handle_http_errors_gracefully
  @handle_vcs_errors_gracefully
  def run(self):
    environments = self.repository.environments
    self.remote_heads = self.repository.fetch_remote_heads()
    self.environments_list = map(lambda e: e['server_environment']['name'],
                                 environments)
    self.environments_ids = map(lambda e: e['server_environment']['id'],
                                environments)
    self.environments_dict = dict(map(
        lambda e: (e['server_environment']['id'], e['server_environment']),
        environments))

    def show_quick_panel():
      if not self.environments_list:
        sublime.error_message('There are no environments to list.')
        return
      self.window.show_quick_panel(self.environments_list, 
                                   self.on_environment_done)
    sublime.set_timeout(show_quick_panel, 10)

  def on_environment_done(self, picked):
    if picked == -1:
      return

    environment_id = self.environments_ids[picked]
    self.environment = self.environments_dict[environment_id]

    branch = self.environment['branch_name']
    self.revision = self.remote_heads[branch]

    log("Environment ID: %d" % environment_id)
    log("Revision: %s" % self.revision)

    def show_input_panel():
      self.window.show_input_panel("Enter a deployment note:", "", 
                                   self.on_message_done, None, None)
    sublime.set_timeout(show_input_panel, 10)

  def on_message_done(self, message):
    self.on_done(self.environment, self.revision, message)

class ReleaseThread(threading.Thread):
  def __init__(self, window, repository, environment_id, revision, message,
               on_done):
    self.repository = repository
    self.window = window
    self.environment_id = environment_id
    self.revision = revision
    self.message = message
    self.on_done = on_done

    threading.Thread.__init__(self)

  @handle_http_errors_gracefully
  @handle_vcs_errors_gracefully
  def run(self):
    release = self.repository.release(self.environment_id, self.revision,
                                      self.message)
    self.on_done(release)

class PrepareSvnReleaseThread(threading.Thread):
  def __init__(self, window, repository, on_done):
    self.repository = repository
    self.window = window
    self.on_done = on_done

    threading.Thread.__init__(self)

  @handle_http_errors_gracefully
  @handle_vcs_errors_gracefully
  def run(self):
    environments = self.repository.environments
    self.revision = self.repository.remote_revision()
    self.environments_list = map(lambda e: e['server_environment']['name'],
                                 environments)
    self.environments_ids = map(lambda e: e['server_environment']['id'],
                                environments)
    self.environments_dict = dict(map(
        lambda e: (e['server_environment']['id'], e['server_environment']),
        environments))

    def show_quick_panel():
      if not self.environments_list:
        sublime.error_message('There are no environments to list.')
        return
      self.window.show_quick_panel(self.environments_list, 
                                   self.on_environment_done)
    sublime.set_timeout(show_quick_panel, 10)

  def on_environment_done(self, picked):
    if picked == -1:
      return

    environment_id = self.environments_ids[picked]
    self.environment = self.environments_dict[environment_id]

    log("Environment ID: %d" % environment_id)
    log("Revision: %s" % self.revision)

    def show_input_panel():
      self.window.show_input_panel("Enter a deployment note:", "", 
                                   self.on_message_done, None, None)
    sublime.set_timeout(show_input_panel, 10)

  def on_message_done(self, message):
    self.on_done(self.environment, self.revision, message)

# Command ######################################################################
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

# Misc #########################################################################

@with_osx_keychain_support
def get_credentials(account):
  credentials = load_credentials()

  if not credentials:
    return ('', '')

  if account in credentials:
    return credentials[account]
  
  return ('', '')

# From funcy: https://github.com/Suor/funcy
def partition(n, step, seq=None):
  if seq is None:
    return partition(n, n, step)
  return [seq[i:i+n] for i in xrange(0, len(seq)-n+1, step)]

def load_credentials():
  credentials = settings.get('credentials')
  return dict((account, (user, password))
      for account, user, password in partition(3, credentials))

def log(*lines):
  if not debug_mode:
    return

  for line in lines:
    print line

def display_error_message(message, on_done = None):
  def display_error():
    sublime.error_message(message)
    if on_done:
      on_done()
  sublime.set_timeout(display_error, 10)

def copy_and_open_default_settings():
  user_settings_path = join(sublime.packages_path(), 'User',
                            'Beanstalk Tools.sublime-settings')

  if not os.path.exists(user_settings_path):
    default_settings_path = join(os.path.abspath(plugin_dir),
                                 'Beanstalk Tools.sublime-settings')
    shutil.copy(default_settings_path, user_settings_path)

  sublime.active_window().open_file(user_settings_path)

def extract_http_auth_credentials(uri):
  username = password = ''

  if '@' in uri:
    username, password = root_uri.split('@')[0].split(':').append('')

  return (username, password)

def strip_leading_slashes(path):
  return path.lstrip('/')

def activity_url(repository):
  return "https://%s" % (repository)

def deployments_url(repository):
  return "https://%s/environments" % (repository)

def release_environment_url(repository, environment_id):
  return "https://%s/environments/%d" % (repository, environment_id)

def git_browse_file_url(repository, filepath, branch='master'):
  return "https://%s/browse/git/%s?branch=%s" % (repository, filepath, branch)

def git_blame_file_url(repository, filepath, revision, branch='master'):
  return "https://%s/blame/%s?branch=%s&rev=%s" % \
            (repository, filepath, branch, revision)

def git_preview_file_url(repository, filepath, revision, branch='master'):
  return "https://%s/previews/%s?back_to=file&branch=%s&rev=%s" % \
            (repository, filepath, branch, revision)

def svn_browse_file_url(repository, filepath, branch='master'):
  return "https://%s/browse/%s/%s" % (repository, branch, filepath)

def svn_blame_file_url(repository, filepath, revision, branch='master'):
  return "https://%s/blame/%s/%s?rev=%s" % \
            (repository, branch, filepath, revision)

def svn_preview_file_url(repository, filepath, revision, subpath=''):
  return "https://%s/previews/%s/%s?back_to=file&rev=%s" % \
            (repository, subpath, filepath, revision)