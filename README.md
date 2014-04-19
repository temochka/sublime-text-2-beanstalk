# Beanstalk Tools For Sublime Text #

## Introduction ##

A handy toolset for using [Sublime Text](http://www.sublimetext.com) with [Beanstalk](http://beanstalkapp.com). It allows you to quickly open related Beanstalk pages in your browser.

The plugin supports Sublime Text version 2.0 and above.

## Usage ##

Open a file or directory inside your Git or Subversion repository in Sublime Text.

* Press `Ctrl + Shift + P` and select `Beanstalk: Open File` or just press `Ctrl + Shift + ^` to open currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Blame` to open blame for currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Preview` to preview currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Activity` to see your repository activity in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Deployments` to see release environments existing for your repository in Beanstalk.

Use `Cmd` instead of `Ctrl` on Mac OS X.

## Get it installed ##

### With The Package Control Plugin ###

The easiest way to install Beanstalk Tools is through [Package Control](https://sublime.wbond.net). Once you get it installed, restart Sublime Text and bring up the Command Palette by pressing `Ctrl + Shift + P`. Select `Package Control: Install Package`, wait while Package Control fetches the latest package list, then select `Beanstalk Tools` from the dropdown. The advantage of using this method is that Package Control will automatically keep the plugin version up to date.

### On Mac ###

* [Install GIT](http://guides.beanstalkapp.com/version-control/git-on-mac.html).
* Run Terminal app and execute the following to install the plugin:

```bash
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/
git clone git://github.com/temochka/sublime-text-2-beanstalk.git Beanstalk
```

### On Linux ###

The plugin was tested on Ubuntu 12.04, but should work on most modern linux distributions.

* [Install GIT](http://guides.beanstalkapp.com/version-control/git-on-linux.html).
* Install the plugin from your system console:

```bash
cd ~/.config/sublime-text-2/Packages/
git clone git://github.com/temochka/sublime-text-2-beanstalk.git Beanstalk
```

* Install [Subversion](http://tortoisesvn.net) if needed.

### On Windows ###

The plugin was tested on Windows XP SP3 with [Tortoise SVN](http://tortoisesvn.net) and [Git SCM](http://git-scm.com/download/win). Binaries of both VCS were added to the system PATH.

* Download and install GIT from [Git SCM website](http://git-scm.com/download/win). Make sure to add GIT binaries into your global PATH.
* Run Windows command shell and execute the following to install the plugin:

```
cd %APPDATA%/Sublime Text 2/Packages/
git clone git://github.com/temochka/sublime-text-2-beanstalk.git Beanstalk
```

* Install [Subversion](http://tortoisesvn.net) if needed.
