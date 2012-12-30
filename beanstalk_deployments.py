import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkDeploymentsCommand(BeanstalkWindowCommand):
  @with_repo
  def run(self, repo):
    webbrowser.open_new_tab(repo.deployments_url())
