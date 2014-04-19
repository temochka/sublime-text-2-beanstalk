import sublime
import sublime_plugin
import webbrowser
try:
    from .beanstalk import *
except ValueError:
    from beanstalk import *


class BeanstalkOpenCommand(BeanstalkWindowCommand):
    @require_file
    @with_repository
    def run(self, repository):
        webbrowser.open_new_tab(
            repository.browse_file_url(self.relative_filename()))
