import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkDeployCommand(BeanstalkWindowCommand):
  @with_repo
  @require_http_credentials
  def run(self, repo):
    repo.repository_id()
