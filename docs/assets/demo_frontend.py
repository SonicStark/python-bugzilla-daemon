################################################
import os, signal
if ("nt" == os.name):
    raise RuntimeError("CANNOT RUN ON WINDOWS "
    "https://pexpect.readthedocs.io/en/stable/"
             "overview.html#pexpect-on-windows")
_S_ = 300
__GOTOWORKDIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
__OPENTHISLOG = os.path.join(__GOTOWORKDIR,
            "docs/assets/demo_frontend.logger")
__OPENTHISOUT = os.path.join(__GOTOWORKDIR,
            "docs/assets/demo_frontend.stdout")
__LOADTHISENV = dict(os.environ, **{
  "PYTHONBUGZILLA_LOG_FILE" : __OPENTHISLOG,
  "PYTHONBUGZILLA_REQUESTS_TIMEOUT" : str(_S_)})
try:
    import pexpect
except ImportError as e:
    raise RuntimeError("missing pexpect "
    "https://github.com/pexpect/pexpect") from e
################################################
FHEAD = lambda E,W : E.expect_exact("\n|v>{}<v|".format(W))
FTAIL = lambda E,W : E.expect_exact("\n|^>{}<^|".format(W))
FDATA = lambda E,W : [FHEAD(E,W), FTAIL(E,W), bytes.decode(E.before, encoding="utf-8").strip()][2]
MIPET = pexpect.spawn("/usr/bin/env python3 ./bugzilla-mi", cwd=__GOTOWORKDIR, env=__LOADTHISENV, maxread=1, timeout=_S_)
MIOUT = open(__OPENTHISOUT, mode="w", encoding="utf-8")
################################################

''' bugzilla.mozilla.org '''
D = "Catch being wait mozilla ----->{}<-----".format(
    FDATA(MIPET, "ARGINF"))
print(D); MIOUT.write(D)

MIPET.sendline("very wrong arguments")
D = "Catch argparse error ----->{}<-----".format(
    FDATA(MIPET, "ARGINF"))
print(D); MIOUT.write(D)

MIPET.sendline("--bugzilla https://bugzilla.mozilla.org/rest --verbose info --products")
D = "Catch output products ----->{}<-----".format(
    FDATA(MIPET, "STRING"))
print(D); MIOUT.write(D)

D = "Catch being wait again ----->{}<-----".format(
    FDATA(MIPET, "ARGINF"))
print(D); MIOUT.write(D)

MIPET.sendline("--bugzilla https://bugzilla.mozilla.org/rest --debug query --json --bug_id 255606")
D = "Catch json output query 255606 ----->{}<-----".format(
    FDATA(MIPET, "STRING"))
print(D); MIOUT.write(D)

''' bugs.documentfoundation.org '''
D = "Catch being wait libreoffce ----->{}<-----".format(
    FDATA(MIPET, "ARGINF"))
print(D); MIOUT.write(D)

MIPET.sendline("--bugzilla https://bugs.documentfoundation.org/rest --debug info --products")
D = "Catch output bugzilla with `--products` ----->{}<-----".format(
    FDATA(MIPET, "STRING"))
print(D); MIOUT.write(D)

D = "Catch being wait again ----->{}<-----".format(
    FDATA(MIPET, "ARGINF"))
print(D); MIOUT.write(D)

MIPET.sendline("--bugzilla https://bugs.documentfoundation.org/rest --debug query --json --from-url "
"'buglist.cgi?chfield=rep_platform&chfieldto=Now&component=LibreOffice&product=LibreOffice"
"&query_format=advanced&resolution=---&short_desc=overflow&short_desc_type=allwordssubstr'")
D = "Catch json output with `--from-url` ----->{}<-----".format(
    FDATA(MIPET, "STRING"))
print(D); MIOUT.write(D)

################################################
print("WILL SEND SIGKILL")
MIPET.kill(signal.SIGKILL)
MIOUT.close()
print("END")
################################################