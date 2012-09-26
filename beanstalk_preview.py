import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkPreviewCommand(BeanstalkWindowCommand):
  @with_repo
  def run(self, repo):
    webbrowser.open_new_tab(repo.preview_file_url(self.relative_filename()))
