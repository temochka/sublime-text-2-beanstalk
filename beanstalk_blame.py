import sublime, sublime_plugin
import os
from beanstalk import *

class BeanstalkBlameCommand(sublime_plugin.WindowCommand):
  def run(self):
    plugin = Plugin(self.window)
    try:
      repo = GitRepo(plugin.rootdir())
      os.system("open %s" % repo.blame_file_url(plugin.relative_filename()))
    except NotAGitRepositoryError, NotABeanstalkRepositoryError:
      pass
