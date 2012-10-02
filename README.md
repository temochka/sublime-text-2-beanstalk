# Sublime Text 2 Beanstalk Tools #

## Introduction ##

A set of handy tools for using Sublime Text 2 editor with Beanstalkapp (http://beanstalkapp.com).

## Usage ##

Open the root directory of your Git or Subversion working copy in Sublime Text 2.

* Press `Ctrl + Shift + P` and select `Beanstalk: Open File` or just press `Ctrl + Shift + ^` to open currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Blame` to open blame for currently edited file in Beanstalk.
* Press `Ctrl + Shift + P` and select `Beanstalk: Preview` to preview currently edited file in Beanstalk.
* More features will be available later.

Use `Cmd` instead of `Ctrl` on Mac OS X.

## Get it installed ##

### With Package Control ###

With the Package Control plugin: The easiest way to install Beanstalk Tools is through Package Control, which can be found at this site: http://wbond.net/sublime_packages/package_control.

Once you get Package Control installed, restart Sublime Text 2 and bring up the Command Palette by pressing `Ctrl + Shift + P`. Select `Package Control: Install Package`, wait while Package Control fetches the latest package list, then select `Beanstalk Tools` from the dropdown. The advantage of using this method is that Package Control will automatically keep the plugin version up to date.

### On Mac ###

```bash
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/
git clone git://github.com/temochka/sublime-text-2-beanstalk.git Beanstalk
```

### On Linux ###

```bash
cd ~/.config/sublime-text-2/Packages/
git clone git://github.com/temochka/sublime-text-2-beanstalk.git Beanstalk
```

### On Windows ###

```
cd %APPDATA%/Sublime Text 2/Packages/
git clone git://github.com/temochka/sublime-text-2-beanstalk.git Beanstalk
```

Make sure you have included all required binaries (`git`, `svn`) in your PATH.

## Known issues ##

Only works for Git and Subversion repositories. Mercurial is not supported yet.