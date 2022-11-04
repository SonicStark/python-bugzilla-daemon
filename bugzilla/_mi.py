#!/usr/bin/env python3
#
# bugzilla - a commandline frontend for the python bugzilla module
#
# Copyright (C) 2007-2017 Red Hat Inc.
# Author: Will Woods <wwoods@redhat.com>
# Author: Cole Robinson <crobinso@redhat.com>
#
# bugzilla-mi - a Machine Interface for the python bugzilla module
#
# Author: SonicStark <50692172+SonicStark@users.noreply.github.com>
#
# This work is licensed under the GNU GPLv2 or later.
# See the COPYING file in the top-level directory.

import datetime
import errno
import getpass
import json
import locale
import logging
import os
import re
import socket
import sys
import tempfile
import types
import urllib.parse
import xmlrpc.client

import requests.exceptions

import bugzilla

import bugzilla
from ._cli import _is_unittest_debug
from ._cli import open_without_clobber
from ._cli import _setup_root_parser
from ._cli import _setup_action_new_parser
from ._cli import _setup_action_query_parser
from ._cli import _setup_action_info_parser
from ._cli import _setup_action_modify_parser
from ._cli import _setup_action_attach_parser
from ._cli import _setup_action_login_parser
from ._cli import _do_query
from ._cli import _do_modify
from ._cli import _do_new
from ._cli import _convert_to_outputformat
from ._cli import _xmlrpc_converter
from ._cli import _bug_field_repl_cb

DEFAULT_BZ = 'https://bugzilla.redhat.com'

format_field_re = re.compile("%{([a-z0-9_]+)(?::([^}]*))?}")

log = logging.getLogger(bugzilla.__name__)

DEFAULT_BZ_LOG = os.getenv("__BUGZILLA_LOG_FILE") or os.path.join(
    os.path.abspath(__file__), datetime.datetime.now().strftime("../BZMI%y%m%d%H%M%S.log"))

FHEAD_PRE = "\n|v>"
FHEAD_SUF = "<v|\n"

FTAIL_PRE = "\n|^>"
FTAIL_SUF = "<^|\n"

FLAG_HEAD_EXCEPT = "{}EXCEPT{}".format(FHEAD_PRE,FHEAD_SUF)
FLAG_TAIL_EXCEPT = "{}EXCEPT{}".format(FTAIL_PRE,FTAIL_SUF)

FLAG_HEAD_STRING = "{}STRING{}".format(FHEAD_PRE,FHEAD_SUF)
FLAG_TAIL_STRING = "{}STRING{}".format(FTAIL_PRE,FTAIL_SUF)

FLAG_HEAD_FORMAT = "{}FORMAT{}".format(FHEAD_PRE,FHEAD_SUF)
FLAG_TAIL_FORMAT = "{}FORMAT{}".format(FTAIL_PRE,FTAIL_SUF)

FLAG_HEAD_ATTACH = "{}ATTACH{}".format(FHEAD_PRE,FHEAD_SUF)
FLAG_TAIL_ATTACH = "{}ATTACH{}".format(FTAIL_PRE,FTAIL_SUF)

FLAG_HEAD_ARGINF = "{}ARGINF{}".format(FHEAD_PRE,FHEAD_SUF)
FLAG_TAIL_ARGINF = "{}ARGINF{}".format(FTAIL_PRE,FTAIL_SUF)

FLAG_HEAD_ILOGIN = "{}ILOGIN{}".format(FHEAD_PRE,FHEAD_SUF)
FLAG_TAIL_ILOGIN = "{}ILOGIN{}".format(FTAIL_PRE,FTAIL_SUF)

swrite = sys.stdout.write
sflush = sys.stdout.flush
sreadl = sys.stdin.readline


################
# Patch output #
################

def _print_message_patched(self, message, file=None):
    """ A patch on an instance of `ArgumentParser`

    Prepare for Monkey Patch on an instance of
    `argparse.ArgumentParser` to fit MI.
    Later we would use this like
    `parser._print_message = types.MethodType(_print_message_patched, parser)`  or  
    `parser._print_message = _print_message_patched.__get__(parser, argparse.ArgumentParser)`
    """
    if message:
        swrite(FLAG_HEAD_ARGINF)
        swrite(message)
        swrite(FLAG_TAIL_ARGINF)
        sflush()

def exit_patched(self, status=0, message=None):
    """ A patch on an instance of `ArgumentParser`

    Prepare for Monkey Patch on an instance of
    `argparse.ArgumentParser` to fit MI.
    Later we would use just like `_print_message_patched` 
    """
    if message:
        emsg = message + \
            "\nArgumentParser exit with status {}".format(status)
        self._print_message(emsg)

class Bugzilla_patched(bugzilla.Bugzilla):
    """ Patch `bugzilla.Bugzilla` to fit MI

    Redirect interactive things output with our syntax
    """
    def interactive_save_api_key(self):
        """ @override """
        swrite(FLAG_HEAD_ILOGIN)
        swrite('API Key: ')
        swrite(FLAG_TAIL_ILOGIN)
        sflush()
        api_key = sreadl().strip()

        self.disconnect()
        self.api_key = api_key

        log.info('Checking API key... ')
        self.connect()

        if not self.logged_in:  # pragma: no cover
            raise bugzilla.BugzillaError("Login with API_KEY failed")
        log.info('API Key accepted')

        wrote_filename = self._rcfile.save_api_key(self.url, self.api_key)
        log.info("API key written to filename=%s", wrote_filename)

        swrite(FLAG_HEAD_ILOGIN)
        swrite("Login successful.")
        if wrote_filename:
            swrite(" API key written to %s" % wrote_filename)
        swrite(FLAG_TAIL_ILOGIN)
        sflush()

    def interactive_login(self, user=None, password=None, force=False,
                          restrict_login=None):
        """ @override """
        ignore = force
        log.debug('Calling interactive_login')

        if not user:
            swrite(FLAG_HEAD_ILOGIN)
            swrite('Bugzilla Username: ')
            swrite(FLAG_TAIL_ILOGIN)
            sflush()
            user = sreadl().strip()
        if not password:
            swrite(FLAG_HEAD_ILOGIN)
            swrite('Bugzilla Password: ')
            swrite(FLAG_TAIL_ILOGIN)
            sflush()
            password = getpass.getpass()

        log.info('Logging in... ')
        out = self.login(user, password, restrict_login)
        swrite("Login successful.")
        if "token" not in out:
            swrite(" However no token was returned.")
        else:
            if not self.tokenfile:
                swrite(" Token not saved to disk.")
            else:
                swrite(" Token cache saved to %s" % self.tokenfile)
            if self._get_version() >= 5.0:
                swrite("\nToken usage is deprecated. ")
                swrite("Consider using bugzilla API keys instead. ")
                swrite("See `man bugzilla` for more details.")
        sflush()


################
# Util helpers #
################

def setup_logging(debug, verbose):
    """ Patch for redirecting log into file

    Avoid interfering with the contents in 
    `stderr` and `stdout` as much as possible
    """
    handler = logging.FileHandler(DEFAULT_BZ_LOG, mode="a", encoding="utf-8", delay=False)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s,%(msecs)d %(filename)s:%(lineno)d %(levelname)s: %(message)s",
        datefmt="%y.%m.%d %H:%M:%S"))
    log.addHandler(handler)

    if debug:
        log.setLevel(logging.DEBUG)
    elif verbose:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARN)

    if _is_unittest_debug():
        log.setLevel(logging.DEBUG)  # pragma: no cover


##################
# Option parsing #
##################

def setup_parser():
    """ Apply monkey patch

    Redirect argparse output to stdout with our syntax
    """
    rootparser = _setup_root_parser()
    rootparser._print_message = types.MethodType(_print_message_patched, rootparser)#Monkey Patch
    rootparser.exit           = types.MethodType(exit_patched          , rootparser)#Monkey Patch
    subparsers = rootparser.add_subparsers(dest="command")
    subparsers.required = True
    _setup_action_new_parser(subparsers)
    _setup_action_query_parser(subparsers)
    _setup_action_info_parser(subparsers)
    _setup_action_modify_parser(subparsers)
    _setup_action_attach_parser(subparsers)
    _setup_action_login_parser(subparsers)
    return rootparser


####################
# Command routines #
####################

def _do_info(bz, opt):
    """ (Patched version)
    Handle the 'info' subcommand
    """
    # All these commands call getproducts internally, so do it up front
    # with minimal include_fields for speed
    def _filter_components(compdetails):
        ret = {}
        for k, v in compdetails.items():
            if v.get("is_active", True):
                ret[k] = v
        return ret

    productname = (opt.components or opt.component_owners or opt.versions)
    fastcomponents = (opt.components and not opt.active_components)

    include_fields = ["name", "id"]
    if opt.components or opt.component_owners:
        include_fields += ["components.name"]
        if opt.component_owners:
            include_fields += ["components.default_assigned_to"]
        if opt.active_components:
            include_fields += ["components.is_active"]

    if opt.versions:
        include_fields += ["versions"]

    bz.refresh_products(names=productname and [productname] or None,
            include_fields=include_fields)

    swrite(FLAG_HEAD_STRING)
    if opt.products:
        for name in sorted([p["name"] for p in bz.getproducts()]):
            swrite("%s\n" % name)

    elif fastcomponents:
        for name in sorted(bz.getcomponents(productname)):
            swrite("%s\n" % name)

    elif opt.components:
        details = bz.getcomponentsdetails(productname)
        for name in sorted(_filter_components(details)):
            swrite("%s\n" % name)

    elif opt.versions:
        proddict = bz.getproducts()[0]
        for v in proddict['versions']:
            swrite("%s\n" % str(v["name"] or ''))

    elif opt.component_owners:
        details = bz.getcomponentsdetails(productname)
        for c in sorted(_filter_components(details)):
            swrite("%s: %s\n" % (c, details[c]['default_assigned_to']))
    swrite(FLAG_TAIL_STRING)
    sflush()


def _format_output_json(buglist):
    """ (Patched version) """
    out = {"bugs": [b.get_raw_data() for b in buglist]}
    s = json.dumps(out, default=_xmlrpc_converter, indent=None, sort_keys=True)
    swrite(FLAG_HEAD_STRING)
    swrite(s)
    swrite(FLAG_TAIL_STRING)
    sflush()


def _format_output_raw(buglist):
    """ (Patched version) """
    swrite(FLAG_HEAD_STRING)
    for b in buglist:
        swrite("Bugzilla %s: \n" % b.bug_id)
        SKIP_NAMES = ["bugzilla"]
        for attrname in sorted(b.__dict__):
            if attrname in SKIP_NAMES:
                continue
            if attrname.startswith("_"):
                continue
            swrite("ATTRIBUTE[%s]: %s\n" % (attrname, b.__dict__[attrname]))
        swrite("\n*-*-*-*-*\n")
    swrite(FLAG_TAIL_STRING)
    sflush()


def _format_output(bz, opt, buglist):
    """ (Patched version) """
    if opt.output in ['raw', 'json']:
        include_fields = None
        exclude_fields = None
        extra_fields = None

        if opt.includefield:
            include_fields = opt.includefield
        if opt.excludefield:
            exclude_fields = opt.excludefield
        if opt.extrafield:
            extra_fields = opt.extrafield

        buglist = bz.getbugs([b.bug_id for b in buglist],
                include_fields=include_fields,
                exclude_fields=exclude_fields,
                extra_fields=extra_fields)
        if opt.output == 'json':
            _format_output_json(buglist)
        if opt.output == 'raw':
            _format_output_raw(buglist)
        return

    swrite(FLAG_HEAD_FORMAT)
    for b in buglist:
        # pylint: disable=cell-var-from-loop
        def cb(matchobj):
            return _bug_field_repl_cb(bz, b, matchobj)
        swrite(format_field_re.sub(cb, opt.outputformat))
        swrite("\n")
    swrite(FLAG_TAIL_FORMAT)
    sflush()


def _do_get_attach(bz, opt):
    """ (Patched version)
    Replace original print statement;
    Add close operation to avoid unreleased sth when running MI;
    """
    data = {}

    def _process_attachment_data(_attlist):
        for _att in _attlist:
            data[_att["id"]] = _att

    if opt.getall:
        for attlist in bz.get_attachments(opt.getall, None)["bugs"].values():
            _process_attachment_data(attlist)
    if opt.get:
        _process_attachment_data(
            bz.get_attachments(None, opt.get)["attachments"].values())

    swrite(FLAG_HEAD_ATTACH)
    for attdata in data.values():
        is_obsolete = attdata.get("is_obsolete", None) == 1
        if opt.ignore_obsolete and is_obsolete:
            continue

        att = bz.openattachment_data(attdata)
        outfile = open_without_clobber(att.name, "wb")
        data = att.read(4096)
        while data:
            outfile.write(data)
            data = att.read(4096)
        swrite("Wrote %s\n" % outfile.name)
        att.close()
        outfile.close()
    swrite(FLAG_TAIL_ATTACH)
    sflush()

def _do_set_attach(bz, opt, parser):
    """ (Patched version) 
    Replace original print statement;
    Remove invalid features when running MI;
    Add close operation to avoid unreleased sth when running MI;
    """
    if not opt.ids:
        parser.error("Bug ID must be specified for setting attachments")

    if sys.stdin.isatty():
        if not opt.file:
            parser.error("--file must be specified")
        fileobj = open(opt.file, "rb")
    else:
        # piped input on stdin
        parser.error("Unsupported operation because "
                     "`sys.stdin.isatty()` returns `False`")

    kwargs = {}
    if opt.file:
        kwargs["filename"] = os.path.basename(opt.file)
    if opt.type:
        kwargs["contenttype"] = opt.type
    if opt.type in ["text/x-patch"]:
        kwargs["ispatch"] = True
    if opt.comment:
        kwargs["comment"] = opt.comment
    if opt.private:
        kwargs["is_private"] = True
    desc = opt.desc or os.path.basename(fileobj.name)

    # Upload attachments
    swrite(FLAG_HEAD_ATTACH)
    for bugid in opt.ids:
        attid = bz.attachfile(bugid, fileobj, desc, **kwargs)
        swrite("Created attachment %i on bug %s\n" % (attid, bugid))
    swrite(FLAG_TAIL_ATTACH)
    sflush()
    fileobj.close()


#################
# Main handling #
#################

def _make_bz_instance(opt):
    """
    Build the Bugzilla instance we will use
    """
    if opt.bztype != 'auto':
        log.info("Explicit --bztype is no longer supported, ignoring")

    cookiefile = None
    tokenfile = None
    use_creds = False
    if opt.cache_credentials:
        cookiefile = opt.cookiefile or -1
        tokenfile = opt.tokenfile or -1
        use_creds = True

    return Bugzilla_patched(
        url=opt.bugzilla,
        cookiefile=cookiefile,
        tokenfile=tokenfile,
        sslverify=opt.sslverify,
        use_creds=use_creds,
        cert=opt.cert)


def _handle_login(opt, action, bz):
    """
    Handle all login related bits
    """
    is_login_command = (action == 'login')

    do_interactive_login = (is_login_command or
        opt.login or opt.username or opt.password)
    username = getattr(opt, "pos_username", None) or opt.username
    password = getattr(opt, "pos_password", None) or opt.password
    use_key = getattr(opt, "api_key", False)

    try:
        if use_key:
            bz.interactive_save_api_key()
        elif do_interactive_login:
            if bz.api_key:
                print("You already have an API key configured for %s" % bz.url)
                print("There is no need to cache a login token. Exiting.")
                sys.exit(0)
            print("Logging into %s" % urllib.parse.urlparse(bz.url)[1])
            bz.interactive_login(username, password,
                    restrict_login=opt.restrict_login)
    except bugzilla.BugzillaError as e:
        print(str(e))
        sys.exit(1)

    if opt.ensure_logged_in and not bz.logged_in:
        print("--ensure-logged-in passed but you aren't logged in to %s" %
            bz.url)
        sys.exit(1)

    if is_login_command:
        sys.exit(0)


def _main(unittest_bz_instance):
    parser = setup_parser()
    opt = parser.parse_args()
    action = opt.command
    setup_logging(opt.debug, opt.verbose)

    log.debug("Launched with command line: %s", " ".join(sys.argv))
    log.debug("Bugzilla module: %s", bugzilla)

    if unittest_bz_instance:
        bz = unittest_bz_instance
    else:
        bz = _make_bz_instance(opt)

    # Handle login options
    _handle_login(opt, action, bz)


    ###########################
    # Run the actual commands #
    ###########################

    if hasattr(opt, "outputformat"):
        if not opt.outputformat and opt.output not in ['raw', 'json', None]:
            opt.outputformat = _convert_to_outputformat(opt.output)

    buglist = []
    if action == 'info':
        _do_info(bz, opt)

    elif action == 'query':
        buglist = _do_query(bz, opt, parser)

    elif action == 'new':
        buglist = _do_new(bz, opt, parser)

    elif action == 'attach':
        if opt.get or opt.getall:
            if opt.ids:
                parser.error("Bug IDs '%s' not used for "
                    "getting attachments" % opt.ids)
            _do_get_attach(bz, opt)
        else:
            _do_set_attach(bz, opt, parser)

    elif action == 'modify':
        _do_modify(bz, parser, opt)
    else:  # pragma: no cover
        raise RuntimeError("Unexpected action '%s'" % action)

    # If we're doing new/query/modify, output our results
    if action in ['new', 'query']:
        _format_output(bz, opt, buglist)


def main(unittest_bz_instance=None):
    try:
        try:
            return _main(unittest_bz_instance)
        except (Exception, KeyboardInterrupt):
            log.debug("", exc_info=True)
            raise
    except KeyboardInterrupt:
        print("\nExited at user request.")
        sys.exit(1)
    except (xmlrpc.client.Fault, bugzilla.BugzillaError) as e:
        print("\nServer error: %s" % str(e))
        sys.exit(3)
    except requests.exceptions.SSLError as e:
        # Give SSL recommendations
        print("SSL error: %s" % e)
        print("\nIf you trust the remote server, you can work "
              "around this error with:\n"
              "  bugzilla --nosslverify ...")
        sys.exit(4)
    except (socket.error,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.InvalidURL,
            xmlrpc.client.ProtocolError) as e:
        print("\nConnection lost/failed: %s" % str(e))
        sys.exit(2)


def mi():
    main()
