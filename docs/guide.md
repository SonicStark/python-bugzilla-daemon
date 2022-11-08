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

Before we start, it is assumed that you have fully understood the original [python-bugzilla](https://github.com/python-bugzilla/python-bugzilla). Since *MI* can be regarded as a wrapper of the original *CLI*, we will not repeat the contents that can be consulted in `bugzilla.1` or `bugzilla.rst`.

## 2.1. Run *MI*

### 2.1.1. Details

First of all, get into the root directory of this project and then run this in your terminal:

```shell
./bugzilla-mi
```

If there is no accident, you will see the prompt message from `stdout`
```text
|v>ARGINF<v|
ArgumentParser waiting
|^>ARGINF<^|
```
which indicates that *MI* has started running. 

Then you need to write these parameters of a call for original `bugzilla-cli` to current `stdin`. At the end, write a *line break* (which equals, the effect when you press *Enter*). And then wait for the new output from `stdout`.

Next, you may need to write other information to current `stdin` according to the prompt message, such as user name and password. 

Finally, you will always *(of course, when there is no accident)* get the output of this round from `stdout`.

### 2.1.2. An example

Assuming that you run the original `bugzilla-cli` as
```shell
./bugzilla-cli --bugzilla https://bugzilla.mozilla.org/rest info --products
```

Then you should see this stuff on your screen
```text
AUS Graveyard
Add-on SDK Graveyard
Air Mozilla
...
support.mozillamessaging.com Graveyard
www.mozilla.org
www.mozilla.org Graveyard
```

Now you run `./bugzilla-mi` and then should get
```text
|v>ARGINF<v|
ArgumentParser waiting
|^>ARGINF<^|

```
Type
```text
--bugzilla https://bugzilla.mozilla.org/rest info --products
```
in current line and press *Enter*, you should get this stuff:
```text
|v>STRING<v|
AUS Graveyard
Add-on SDK Graveyard
Air Mozilla
...
support.mozillamessaging.com Graveyard
www.mozilla.org
www.mozilla.org Graveyard

|^>STRING<^|

|v>ARGINF<v|
ArgumentParser waiting
|^>ARGINF<^|

```
Now you are in another round waiting for input.

## 2.2. Understand syntax in `stdout`

### 2.2.1. *Expected* :vs: *Unexpected*

**Expected** output in `stdout`, whether single line or multiple lines, is wrapped by *start-flag-line* and *end-flag-line*. Using a *State Machine* like can make it easy to parse these things.

The front and back of the two lines are forced to add *line break* for each, which ensure that they form separate lines and are easily captured. For example, you can use the following Python style regex to match:
```python
r"\|v>[A-Z]{6}<v\|" #start-flag-line
r"\|\^>[A-Z]{6}<\^\|" #end-flag-line
```

**Unexpected** output in `stdout` is also easy to parse, because these things are not wrapped by any preset flags. They are usually caused by exceptions which can not be handled and cause current process to exit abnormally.

### 2.2.2. Meaning of each flag-line

The so called *flag-line* always appear in pair, with one indicating the start of messages and the other indicating the end. Different words wrapped by `>` and `<` indicate different message types.

* `|v>ARGINF<v|`&`|^>ARGINF<^|`&emsp;Messages come from the patched `argparse.ArgumentParser`. This patched stuff would never call `sys.exit` when it fails in parsing. Usually the messages are used to inform you the parser is waiting for input or whether the parameters it read from `stdin` are legal.

* `|v>EXCEPT<v|`&`|^>EXCEPT<^|`&emsp;It indicates that an exception has been caught and properly handled. Exceptions within the expected range could be various. Such as a socket error occurs (e.g. TCP connection timeout), or the Bugzilla server throws an error. These exceptions are not fatal, and indicate that this round is not successful, and it is best to directly jump into a new round.

* `|v>FORMAT<v|`&`|^>FORMAT<^|`&emsp;Output stuff when using `--outputformat` option.

* `|v>ATTACH<v|`&`|^>ATTACH<^|`&emsp;Output stuff from performing `attach` command.

* `|v>ILOGIN<v|`&`|^>ILOGIN<^|`&emsp;Stuff about login or API key. In some situations, terminals will block in the next line of its *end-flag-line*, waiting for the user name, password, or API key to be written into `stdin`. For the interactive behavior about login, it is recommanded to check the methods with names beginning with `interactive_` in `base.py`.

* `|v>STRING<v|`&`|^>STRING<^|`&emsp;Other general output stuff.

## 2.3. Environment variables

### 2.3.1. `PYTHONBUGZILLA_LOG_FILE`

Specify the path of log file. If this environment variable is not set, the log file will be stored in parent directory of the directory in which `_mi.py` locates. And the file name will be equal to `datetime.datetime.now().strftime("BZMI%y%m%d%H%M%S.log")`.

If you specify, please ensure that the path can be handled normally by built-in function `open` (e.g. make sure dir exists), otherwise an exception will be raised and *MI* will exit immediately.

This environment variable is only read during the log setting process before *MI* enters its main loop. Changing it during running will not take effect before the next run of *MI*.

### 2.3.2. `PYTHONBUGZILLA_REQUESTS_TIMEOUT`

Used in `_session._BugzillaSession._get_timeout` and `_session._BugzillaSession.request`. Actually the timeout value will be passed to an instance of `requests.Session`. It works for both *XMLRPC* and *REST* because [requests](https://requests.readthedocs.io/en/latest/) is used as a unified backend.

See also (definition of `_session._BugzillaSession._get_timeout`):
```python
def _get_timeout(self):
    # Default to 5 minutes. This is longer than bugzilla.redhat.com's
    # apparent 3 minute timeout so shouldn't affect legitimate usage,
    # but saves us from indefinite hangs
    DEFAULT_TIMEOUT = 300
    envtimeout = os.environ.get("PYTHONBUGZILLA_REQUESTS_TIMEOUT")
    return float(envtimeout or DEFAULT_TIMEOUT)
```

### 2.3.3. `__BUGZILLA_UNITTEST_DEBUG`

It may be changed by `tests.conftest.pytest_configure`, but only affects the return value of `bugzilla._cli._is_unittest_debug`. It seems that the only function it has is to ensure that global log output level is `DEBUG`.

:warning: As the author of this guide I cannot accurately determine its use at present, please use with care if you need.

### 2.3.4. `__BUGZILLA_UNITTEST`

Referred only in `tests.__init__` as `os.environ["__BUGZILLA_UNITTEST"] = "1"`. It is suspected that this is a bug, the statement is more likely to be `os.environ["__BUGZILLA_UNITTEST_DEBUG"] = "1"`.

:warning: As the author of this guide I cannot accurately determine its use at present, please use with care if you need.

## 2.4 Exit *MI*

It is recommand that do `CTRL`+`C` or equivalent operation. The try-except mechanism in `MI` would catch `KeyboardInterrupt` and print
```text
|v>STRING<v|
Exited at user request
|^>STRING<^|
```
to `stdout` before exit.

# 3. Tips

## 3.1. Explicitly specify *XMLRPC* or *REST*

For example, it is better to use
```text
--bugzilla https://bugzilla.mozilla.org/xmlrpc.cgi 
```
or
```text
--bugzilla https://bugzilla.mozilla.org/rest 
```
rather than
```text
--bugzilla https://bugzilla.mozilla.org
```
If you do not specify explicitly, it may cause unpredictable exceptions to be raised or unexpected operations to be performed, although an automatic probe is supported.

## 3.2. Force creation of new connection instance
