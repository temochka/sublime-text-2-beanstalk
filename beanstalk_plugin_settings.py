import sublime, sublime_plugin, webbrowser
from beanstalk import *

class BeanstalkPluginSettingsCommand(sublime_plugin.WindowCommand):
  def run(self):
    copy_and_open_default_settings()
