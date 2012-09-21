import sublime, sublime_plugin
from xml.dom.minidom import parseString
import re, os

class NotASvnRepositoryError(RuntimeError):
  pass

class NotAGitRepositoryError(RuntimeError):
  pass

class NotABeanstalkRepositoryError(RuntimeError):
  pass

class GitRepo:
  def __init__(self, path):
    self.path = path
    if not self.is_git():
      raise NotAGitRepositoryError

  def git(self, command):
    return os.popen("cd %s && git %s" %(self.path, command)).read()

  def repository_path(self):
    repository_path = self.parse_repository(self.git("remote -v"))
    if not repository_path:
      raise NotABeanstalkRepositoryError
    return repository_path

  def branch(self):
    return self.parse_branch(self.git("branch"))

  def revision(self):
    return self.git("rev-parse HEAD")

  def browse_file_url(self, filename):
    return Beanstalk.GitBrowseFileUrl(self.repository_path(), filename, self.branch())

  def blame_file_url(self, filename):
    return Beanstalk.GitBlameFileUrl(self.repository_path(), filename, self.revision(), self.branch())

  def parse_repository(self, remotes):
    p = re.compile("\@(.+\.beanstalkapp\.com.*?)\.git")
    m = p.findall(remotes)
    return m[0].replace(":", "") if m else None

  def parse_branch(self, branches):
    p = re.compile("\* (.+)")
    m = p.findall(branches)
    return m[0] if m else None

  def is_git(self):
    code = os.system('cd %s && git rev-parse' % self.path)
    return not code

class SvnRepo:
  def __init__(self, path):
    self.path = path
    if not self.is_svn():
      raise NotASvnRepositoryError

  def svn(self, command):
    return os.popen("cd %s && svn %s --xml" %(self.path, command)).read()

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
    return Beanstalk.SvnBrowseFileUrl(self.repository_path(), filename, self.branch())

  def blame_file_url(self, filename):
    return Beanstalk.SvnBlameFileUrl(self.repository_path(), filename, self.revision(), self.branch())

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
    code = os.system('cd %s && svn info' % self.path)
    return not code

class Plugin:
  def __init__(self, window):
    self.window = window

  def rootdir(self):
    return self.window.folders()[0]

  def relative_filename(self):
    return self.window.active_view().file_name().replace(self.rootdir(), "")

class Beanstalk:
  @staticmethod
  def GitBrowseFileUrl(repository, filepath, branch='master'):
    return "https://%s/browse/git%s?branch=%s" %(repository, filepath, branch)

  @staticmethod
  def SvnBrowseFileUrl(repository, filepath, branch='master'):
    return "https://%s/browse/%s%s" %(repository, branch, filepath)

  @staticmethod
  def SvnBlameFileUrl(repository, filepath, revision, branch='master'):
    return "https://%s/blame/%s%s?rev=%s" %(repository, branch, filepath, revision)

  @staticmethod
  def GitBlameFileUrl(repository, filepath, revision, branch='master'):
    return "https://%s/blame%s?branch=%s&rev=%s" %(repository, filepath, branch, revision)

