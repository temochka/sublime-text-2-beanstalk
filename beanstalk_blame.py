import sublime
import sublime_plugin
import webbrowser
try:
    from .beanstalk import *
except ValueError:
    from beanstalk import *


class BeanstalkBlameCommand(BeanstalkWindowCommand):
    @require_file
    @with_repository
    def run(self, repository):
        webbrowser.open_new_tab(
            repository.blame_file_url(self.relative_filename()))
