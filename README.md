# Sublime Text 2 Beanstalk Tools #

## Introduction ##

A handy toolset for using [Sublime Text 2](http://www.sublimetext.com/2) with [Beanstalkapp](http://beanstalkapp.com). It allows you to open related Beanstalk pages in your browser quickly and perform Beanstalk deployments right from the editor.

## Usage ##

Open a file or directory inside your Git or Subversion repository in Sublime Text 2.

* Press `Ctrl + Shift + P` and select `Beanstalk: Open File` or just press `Ctrl + Shift + ^` to open currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Blame` to open blame for currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Preview` to preview currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Activity` to see your repository activity in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Release Environments` to see release environments existing for your repository in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Release` to initiate a release using Beanstalk deployments feature.

Use `Cmd` instead of `Ctrl` on Mac OS X.

## Get it installed ##

### With The Package Control Plugin ###

The easiest way to install Beanstalk Tools is through Package Control, which can be found at this site: http://wbond.net/sublime_packages/package_control.

Once you get Package Control installed, restart Sublime Text 2 and bring up the Command Palette by pressing `Ctrl + Shift + P`. Select `Package Control: Install Package`, wait while Package Control fetches the latest package list, then select `Beanstalk Tools` from the dropdown. The advantage of using this method is that Package Control will automatically keep the plugin version up to date.

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

* Install [cURL](http://curl.haxx.se) if you want to perform deployments using the plugin. Ubuntu/Debian users can install cURL via apt package manager:

```bash
sudo apt-get install curl
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

## Important Notes ##

* Only works for Git and Subversion repositories. Mercurial is not supported yet.
* Linux version of Sublime Text 2 is built without SSL support. The plugin uses cURL utility to communicate with Beanstalk API. Please make sure you have it is installed and included into your system PATH.