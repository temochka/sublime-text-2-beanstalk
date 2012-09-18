import sublime, sublime_plugin
import re, os

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
    repository_path = self.fetch_repository(self.git("remote -v"))
    if not repository_path:
      raise NotABeanstalkRepositoryError
    return repository_path

  def branch(self):
    return self.fetch_branch(self.git("branch"))

  def revision(self):
    return self.git("rev-parse HEAD")

  def browse_file_url(self, filename):
    return Beanstalk.GitBrowseFileUrl(self.repository_path(), filename, self.branch())

  def blame_file_url(self, filename):
    return Beanstalk.BlameFileUrl(self.repository_path(), filename, self.revision(), self.branch())

  def fetch_repository(self, remotes):
    p = re.compile("\@(.+\.beanstalkapp\.com.*?)\.git")
    m = p.findall(remotes)
    return m[0].replace(":", "") if m else None

  def fetch_branch(self, branches):
    p = re.compile("\* (.+)")
    m = p.findall(branches)
    return m[0] if m else None

  def is_git(self):
    code = os.system('cd %s && git rev-parse' % self.path)
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
  def BlameFileUrl(repository, filepath, revision, branch='master'):
    return "https://%s/blame%s?branch=%s&rev=%s" %(repository, filepath, branch, revision)

