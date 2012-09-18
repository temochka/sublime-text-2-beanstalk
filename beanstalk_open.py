import sublime, sublime_plugin
import os
from beanstalk import *

class BeanstalkOpenCommand(sublime_plugin.WindowCommand):
  def run(self):
    plugin = Plugin(self.window)
    try:
      repo = GitRepo(plugin.rootdir())
      os.system("open %s" % repo.browse_file_url(plugin.relative_filename()))
    except NotAGitRepositoryError, NotABeanstalkRepositoryError:
      pass
