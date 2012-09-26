import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkBlameCommand(BeanstalkWindowCommand):
  @with_repo
  def run(self, repo):
    webbrowser.open_new_tab(repo.blame_file_url(self.relative_filename()))
