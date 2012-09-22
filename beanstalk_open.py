import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkOpenCommand(sublime_plugin.WindowCommand):
  def run(self):
    plugin = Plugin(self.window)
    repo = None

    try:
      repo = GitRepo(plugin.rootdir())
    except NotAGitRepositoryError:
      pass

    try:
      repo = SvnRepo(plugin.rootdir())
    except NotASvnRepositoryError:
      pass

    if not repo:
      print "Subversion or Git repository not found."
      return

    try:
      webbrowser.open_new_tab(repo.browse_file_url(plugin.relative_filename()))
    except NotABeanstalkRepositoryError:
      pass