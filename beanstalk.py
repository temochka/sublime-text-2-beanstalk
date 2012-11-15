import sublime, sublime_plugin
from xml.dom.minidom import parseString
import re, os
from functools import wraps

class NotASvnRepositoryError(Exception):
  pass

class NotAGitRepositoryError(Exception):
  pass

class NotABeanstalkRepositoryError(Exception):
  pass

class GitRepo:
  def __init__(self, path):
    self.path = path
    if not self.is_git():
      raise NotAGitRepositoryError

    self.repository_path = self.repository_path()

  def git(self, command):
    os.chdir(self.path)
    return os.popen("git %s" % command).read().strip()

  def repository_path(self):
    repository_path = self.parse_repository(self.git("remote -v"))
    if not repository_path:
      raise NotABeanstalkRepositoryError
    return repository_path

  def path_from_rootdir(self, filename):
    rootdir = self.git("rev-parse --show-toplevel")
    if self.path != rootdir:
      _, _, path_from_rootdir = self.path.partition(rootdir)
      return path_from_rootdir + '/' + filename
    return filename

  def branch(self):
    return self.parse_branch(self.git("branch"))

  def revision(self):
    return self.git("rev-parse HEAD")

  def browse_file_url(self, filename):
    return git_browse_file_url(self.repository_path, self.path_from_rootdir(filename), self.branch())

  def blame_file_url(self, filename):
    return git_blame_file_url(self.repository_path, self.path_from_rootdir(filename), self.revision(), self.branch())

  def preview_file_url(self, filename):
    return git_preview_file_url(self.repository_path, self.path_from_rootdir(filename), self.revision(), self.branch())

  def parse_repository(self, remotes):
    remotes = list(set(map(lambda l: re.split("\s", l)[1], remotes.splitlines())))
    return self.make_repository_url(remotes)

  def parse_branch(self, branches):
    p = re.compile("\* (.+)")
    m = p.findall(branches)
    return m[0] if m else None

  def is_git(self):
    os.chdir(self.path)
    code = os.system('git rev-parse')
    return not code

  def make_repository_url(self, remotes):
    for r in remotes:
      if r.startswith('git@') and 'beanstalkapp.com' in r:
        return r[4:-4].replace(":", "")
      elif r.startswith('https://') and 'git.beanstalkapp.com' in r:
        return r[8:-4].replace("git.beanstalkapp.com", "beanstalkapp.com").split("@")[-1]

class SvnRepo:
  def __init__(self, path):
    self.path = path
    if not self.is_svn():
      raise NotASvnRepositoryError

    self.repository_path = self.repository_path()

  def svn(self, command):
    os.chdir(self.path)
    return os.popen("svn %s --xml" %(command)).read()

  def repository_path(self):
    repository_path = self.parse_repository(self.svn("info"))
    if not repository_path:
      raise NotABeanstalkRepositoryError
    return repository_path

  def branch(self):
    return self.parse_branch(self.svn("info"))

  def revision(self):
    return self.parse_revision(self.svn("info"))

  def browse_file_url(self, filename):
    return svn_browse_file_url(self.repository_path, filename, self.branch())

  def blame_file_url(self, filename):
    return svn_blame_file_url(self.repository_path, filename, self.revision(), self.branch())

  def preview_file_url(self, filename):
    return svn_preview_file_url(self.repository_path, filename, self.revision(), self.branch())

  def parse_repository(self, info):
    dom = parseString(info)
    url = dom.getElementsByTagName('root')[0].firstChild.data
    url = url.replace("https://", "")
    return url.replace("svn.beanstalkapp.com", "beanstalkapp.com")

  def parse_branch(self, info):
    dom = parseString(info)
    url = dom.getElementsByTagName('url')[0].firstChild.data
    p = re.compile("beanstalkapp\.com\/.+?\/(.*)")
    m = p.findall(url)
    return m[0] if m else None

  def parse_revision(self, info):
    dom = parseString(info)
    return dom.getElementsByTagName("commit")[0].attributes["revision"].value

  def is_svn(self):
    os.chdir(self.path)
    code = os.system('svn info')
    return not code

class BeanstalkWindowCommand(sublime_plugin.WindowCommand):
  def rootdir(self):
    folders = self.window.folders()
    return [i for i in folders if self.filename().startswith(i + os.sep)][0]

  def relative_filename(self):
    _, _, filename = self.filename().partition(self.rootdir())
    return filename

  def filename(self):
    return self.window.active_view().file_name()

  @property
  def repository(self):
    try:
      return GitRepo(self.rootdir())
    except (NotAGitRepositoryError, NotABeanstalkRepositoryError):
      pass

    try:
      return SvnRepo(self.rootdir())
    except (NotASvnRepositoryError, NotABeanstalkRepositoryError):
      pass

    raise Exception


def with_repo(func):
  @wraps(func)
  def wrapper(self):
    try:
      return func(self, self.repository)
    except Exception:
      sublime.message_dialog("Beanstalk Subversion or Git repository not found.")
  return wrapper


def git_browse_file_url(repository, filepath, branch='master'):
  return "https://%s/browse/git%s?branch=%s" % (repository, filepath, branch)

def git_blame_file_url(repository, filepath, revision, branch='master'):
  return "https://%s/blame%s?branch=%s&rev=%s" % (repository, filepath, branch, revision)

def git_preview_file_url(repository, filepath, revision, branch='master'):
  return "https://%s/previews%s?back_to=file&branch=%s&rev=%s" % (repository, filepath, branch, revision)

def svn_browse_file_url(repository, filepath, branch='master'):
  return "https://%s/browse/%s%s" % (repository, branch, filepath)

def svn_blame_file_url(repository, filepath, revision, branch='master'):
  return "https://%s/blame/%s%s?rev=%s" % (repository, branch, filepath, revision)

svn_preview_file_url = git_preview_file_url