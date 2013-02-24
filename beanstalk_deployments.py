import sublime
import sublime_plugin
import webbrowser
from beanstalk import *


class BeanstalkDeploymentsCommand(BeanstalkWindowCommand):
    @with_repository
    def run(self, repository):
        webbrowser.open_new_tab(repository.deployments_url())
