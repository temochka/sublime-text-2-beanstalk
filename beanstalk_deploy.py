import sublime, sublime_plugin, webbrowser
from beanstalk import *
from package_control import ThreadProgress

class BeanstalkDeployCommand(BeanstalkWindowCommand):
  @with_repo
  @require_http_credentials
  def run(self, repository):
    self.repo = repository

    if not self.repo.supports_deployments:
      sublime.error_message('Deployments support is not implemented for your repository type yet.')
      return

    thread_type = self.repo.prepare_release_thread()
    thread = thread_type(self.window, self.repo, self.on_preparing_done)
    thread.start()
    ThreadProgress(thread, "Preparing GIT release", "Done")

  def on_preparing_done(self, environment, revision, message=''):
    def start_release():
      thread_type = self.repo.release_thread()
      thread = thread_type(self.window, self.repo, environment['id'], revision, message, self.on_releasing_done)
      thread.start()
      ThreadProgress(thread, "Releasing %s" % revision, "Done")

    msg = "Are you sure want to deploy %s to %s?" % (revision, environment['name'])
    if sublime.ok_cancel_dialog(msg):
      sublime.set_timeout(start_release, 10)

  def on_releasing_done(self, release):
    def open_in_browser():
      environment_id = release['release']['environment_id']
      url = self.repo.release_environment_url(environment_id)
      webbrowser.open_new_tab(url)

    sublime.set_timeout(open_in_browser, 10)
