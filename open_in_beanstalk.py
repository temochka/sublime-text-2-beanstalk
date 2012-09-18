import sublime, sublime_plugin
import os, re

class OpenInBeanstalkCommand(sublime_plugin.WindowCommand):
	def run(self):
		rootdir = self.window.folders()[0]
		filepath = self.window.active_view().file_name().replace(rootdir, "")
		repository = fetch_repository(git(rootdir, "remote -v"))
		branch = fetch_branch(git(rootdir, "branch"))
		os.system("open %s" % url(repository, filepath, branch))

def git(dir, command):
	print "cd %s && git %s" %(dir, command)
	return os.popen("cd %s && git %s" %(dir, command)).read()

def fetch_repository(remotes):
	p = re.compile("\@(.+\.beanstalkapp\.com.*?)\.git")
	m = p.findall(remotes)
	if m:
		return m[0].replace(":", "") 
	else: 
		return None

def fetch_branch(branches):
	p = re.compile("\* (.+)")
	m = p.findall(branches)
	if m:
		return m[0]
	else: 
		return None	

def url(repository, filepath, branch='master'):
	return "https://%s/browse/git%s?branch=%s" %(repository, filepath, branch)