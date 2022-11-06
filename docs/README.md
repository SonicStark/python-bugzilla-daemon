# Things in `docs`



## The Original

The two files are inherited intact from original [python-bugzilla/python-bugzilla](https://github.com/python-bugzilla/python-bugzilla), 
which describe the usage of `bugzilla` in your terminal. 
This is because the original one provides the feature of installing the CLI tool as `/usr/bin/bugzilla`.
But this feature has been removed by us, so what they describe is actually for `bugzilla-cli` in our *python-bugzilla-mi*.
That is to say, the **actual** command line tool for interacting with Bugzilla referred in the files is `bugzilla-cli` rather than `bugzilla`.
Please always remember this when reading them.

These two files have the same content but in different formats, so you only need to select one to read.

### `bugzilla.rst`

#### What is `.rst` file

From [ReStructuredText](https://en.wikipedia.org/wiki/ReStructuredText):
> reStructuredText (RST, ReST, or reST) is a file format for textual data used primarily in the Python programming language community for technical documentation.
>
> It is a lightweight markup language designed to be both (a) processable by documentation-processing software such as Docutils, and (b) easily readable by human programmers who are reading and writing Python source code.

#### How to open it

Use [Docutils: Written in Python, for General- and Special-Purpose Use](https://docutils.sourceforge.io/).

### `bugzilla.1`

#### What is `.1` file

It is a *Unix Section 1 Manual Page*. And you may ask what the hell *Section 1* & *.1* is. Read this from [why do we have .1 extension in MAN PAGES](https://www.unix.com/fedora/105853-why-do-we-have-1-extension-man-pages.html):
> Because the man pages come in different sections covering different areas, running man man shows me this list:
>    - 1   Executable programs or shell commands
>    - 2   System calls (functions provided by the kernel)
>    - 3   Library calls (functions within program libraries)
>    - 4   Special files (usually found in /dev)
>    - 5   File formats and conventions eg /etc/passwd
>    - 6   Games
>    - 7   Miscellaneous (including macro  packages  and  conventions), e.g. man(7), groff(7)
>    - 8   System administration commands (usually only for root)
>    - 9   Kernel routines [Non standard]

#### How to open it

```shell
man ./bugzilla.1
```



## New things

### `guide.md`

It introduces how our **MI** is built based on the previous **CLI** and its application scenarios. If you are familiar with [python-bugzilla
/python-bugzilla
](https://github.com/python-bugzilla/python-bugzilla), reading it will enable you to quickly understand and use this project.

### `assets`: demos & charts

| Item | Description |
|------|-------------|
| workflow.drawio     | It is drawn with [jgraph/drawio](https://github.com/jgraph/drawio) and shows how we maintain this project. |
| workflow.drawio.png | Rendered from `workflow.drawio` for using in `python-bugzilla-mi/README.md`. |
