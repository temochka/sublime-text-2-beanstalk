import sublime
import sublime_plugin
try:
    from .beanstalk import *
except ValueError:
    from beanstalk import *


class BeanstalkPluginSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        copy_and_open_default_settings()
