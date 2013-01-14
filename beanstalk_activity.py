import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkActivityCommand(BeanstalkWindowCommand):
  @with_repository
  def run(self, repository):
    webbrowser.open_new_tab(repository.activity_url())
