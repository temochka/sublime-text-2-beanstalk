import sublime, sublime_plugin, webbrowser
from beanstalk import *
from package_control import ThreadProgress

class BeanstalkDeployCommand(BeanstalkWindowCommand):
  @with_repository
  @require_http_credentials
  def run(self, repository):
    thread_type = self.repository.prepare_release_thread
    thread = thread_type(self.window, self.repository, self.on_preparing_done)
    thread.start()
    ThreadProgress(thread, "Preparing for a Beanstalk release", "Done")

  def on_preparing_done(self, environment, revision, message=''):
    def start_release():
      thread_type = self.repository.release_thread
      thread = thread_type(self.window, self.repository, environment['id'], revision, message, self.on_releasing_done)
      thread.start()
      ThreadProgress(thread, "Releasing %s" % revision, "Done")

    msg = "Are you sure want to deploy revision %s to %s?" % (revision, environment['name'])
    if sublime.ok_cancel_dialog(msg):
      sublime.set_timeout(start_release, 10)

  def on_releasing_done(self, release):
    def open_in_browser():
      environment_id = release['release']['environment_id']
      url = self.repository.release_environment_url(environment_id)
      webbrowser.open_new_tab(url)

    sublime.set_timeout(open_in_browser, 10)
