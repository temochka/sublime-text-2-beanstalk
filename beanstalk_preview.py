import sublime
import sublime_plugin
import webbrowser
from .beanstalk import *


class BeanstalkPreviewCommand(BeanstalkWindowCommand):
    @require_file
    @with_repository
    def run(self, repository):
        webbrowser.open_new_tab(
            repository.preview_file_url(self.relative_filename()))
