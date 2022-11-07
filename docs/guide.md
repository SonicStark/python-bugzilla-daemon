# 1. The way from [python-bugzilla](https://github.com/python-bugzilla/python-bugzilla)

## 1.1. About *MI*

### 1.1.1. WHAT

**MI** stands for **Machine Interface**. The concept of MI originates from the well-known [GDB: The GNU Project Debugger](https://www.sourceware.org/gdb/) with docs at [GDB User Manual - The GDB/MI Interface](https://sourceware.org/gdb/current/onlinedocs/gdb/GDB_002fMI.html#GDB_002fMI).

For this project, when you run **MI** from your terminal, it starts to wait until it reads a line from `stdin`, then performs the corresponding operation, and finally writes some results and necessary information to `stdout`. Of course, these corresponding operations may also include reading some strings from `stdin`, such as obtaining the user name and password during interactive login. 

### 1.1.2. WHY

[python-bugzilla](https://github.com/python-bugzilla/python-bugzilla) is undoubtedly an excellent project. It is packaged as a python library and published on [python-bugzilla - PyPI](https://pypi.org/project/python-bugzilla/). After running the installation scripts in `setup.py`, users could not only `import bugzilla` in their code, but also run `/usr/bin/bugzilla` directly in the terminal to use it through **CLI**.

However, through **CLI**, one call of `/usr/bin/bugzilla` can only complete one action, and each run requires some complex internal processes, such as detecting the basic information of the target, establishing HTTP(S) connections, etc. These expensive internal processes disappear from RAM with the end of script execution, and no  cache mechanism is established on the disks.

Therefore, we consider deploying a loop-like structure and some cache mechanisms and in our new interface, so that multiple actions can be performed just in a single run, and shared information can be used repeatedly to reduce the overhead.

Not only that, we also hope that our new interface can **not only** be friendly to old users and provide compatibility as much as possible, **but also** provide machine-oriented convenience, so that it can be used as a backend of automatic control systems such as [expect](https://man7.org/linux/man-pages/man1/expect.1.html), [pexpect](https://github.com/pexpect/pexpect), [wexpect](https://github.com/raczben/wexpect), etc. (*This may remind you that running **python-bugzilla** in a separate process to avoid the infection of **GPL-2.0 license** to some extent. But this is surely NOT our original intention. We sincerely hope that you readers always be loyal to the spirit of open-source.*)

All the above reminds us of [GDB/MI Interface](https://sourceware.org/gdb/current/onlinedocs/gdb/GDB_002fMI.html#GDB_002fMI). So we borrowed the concept of **MI** from here and developed what you see today: run `bugzilla-mi`, after seeing the prompt of *ArgumentParser waiting*, type just exactly the same parameters to `stdin` when running `bugzilla-cli`, then press Enter (actually a **line break** is typed in), and then continue to type something or just wait, and finally get the expected output in `stdout`. After that you will continue to see the prompt of *ArgumentParser waiting*, and then get into another new round of typing parameters.

### 1.1.3. HOW

It is easy to find that after installation running `/usr/bin/bugzilla` in terminal is exactly equivalent to running `python ./bugzilla-cli` in the project root directory of [python-bugzilla](https://github.com/python-bugzilla/python-bugzilla). And `bugzilla-cli` is actually just a wrapper of `_cli.main`. So we do the surgery on a copy of `_cli.py`, i.e., `_mi.py`. Although original `_cli.py` looks complex, it is highly cohesive and low coupling, so the surgery is easy. We

* wrap a cluster of output messages (consisting of single or multiple lines) between *start-flag-line* `|v>*<v|` and *end-flag-line* `|^>*<^|`;
* redirect logs output so that it is written to a file instead of being written to `stderr` to avoid potential impact;
* patch built-in `argparse.ArgumentParser` to make it print message to `stdout` in our new format, and no longer call `sys.exit` when it fails in parsing;
* patch other functions that have calls of `print` to make them print to `stdout` in our new format;
* add a cache mechanism in `_make_bz_instance` to make a new instance when necessary;
* add many `try-except` and `raise` statements to make the round by round loop process run robustly without unexpected interruption. 

## 1.2. Something shrunk

You can see that although generally we are adding sth rather than deleting, many files have been deleted compared with the original content. We will briefly explain this below to help you understand the purpose of doing so.

### 1.2.1. setup files

The main purpose we expect is to serve as a backend of some automation control systems. In this case, we believe that installing into *site-packages* of your Python environment may be a bad choice. We expect the users to be **free to choose and control** where to place and run these scripts without the help of `pip`. Therefore, it is sufficient to provide only `bugzilla-cli` for forward compatibility and `bugzilla-mi` for daily use. If you want to import from *site-packages*, or just type `bugzilla --balabala` in your terminal and press Enter anyway, you are recommended to select the original [python-bugzilla](https://github.com/python-bugzilla/python-bugzilla).

### 1.2.2. tests, quality-checks and docs

Limited by our time and resources, these less important content has been removed. And our development does not involve changing the original code in package `bugzilla`, we only add something new. What we need to confirm is that once there is no problem in original *python-bugzilla*, the code added by us will also work well. Therefore, only things related to the newly added code are retained.



# 2. Usage
