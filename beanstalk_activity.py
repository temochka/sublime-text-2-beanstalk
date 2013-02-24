import sublime
import sublime_plugin
import webbrowser
from beanstalk import *


class BeanstalkActivityCommand(BeanstalkWindowCommand):
    @with_repository
    def run(self, repository):
        webbrowser.open_new_tab(repository.activity_url())
