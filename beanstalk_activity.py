import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkActivityCommand(BeanstalkWindowCommand):
  @with_repo
  def run(self, repo):
    webbrowser.open_new_tab(repo.activity_url())
