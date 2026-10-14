# Internal verification harness - NOT part of the user documentation.
#
# A temporary working directory for one example, deleted only once Windows has
# finished letting go of it.
#
# ⚠ WHY THIS FILE EXISTS, MEASURED 2026-09-10. Both harnesses that run an example
# did the obvious thing:
#
#     with tempfile.TemporaryDirectory(prefix="prokon-example-") as scratch:
#         os.chdir(scratch)
#         runpy.run_path(script)
#
# and both failed intermittently - about one run in four - with
#
#     PermissionError: [WinError 32] The process cannot access the file because
#     it is being used by another process: '...\\prokon-example-XXXXXXXX'
#
# The example itself had already finished and printed correct results. The failure
# was the cleanup.
#
# WHO WAS HOLDING IT. An example calls prokon.v5.<engine>.analyse(), which spawns
# prokon-automation.exe. The child INHERITS the parent's working directory, and on
# Windows a process's current directory is an open handle on that directory. The
# child exits, subprocess.run returns - and the handle is not always released by
# the time the very next statement deletes the tree.
#
# Measured, three cells, each differing from the others in exactly one thing,
# twenty rounds apiece:
#
#   A  chdir into the scratch dir, spawn the engine (it inherits that cwd)   1 / 20 failed
#   B  chdir into the scratch dir, spawn the engine with an explicit cwd=    0 / 20 failed
#   C  chdir into the scratch dir, spawn nothing at all                      0 / 20 failed
#
# So the holder is a just-exited child that had the directory as its cwd, and
# nothing else.
#
# WHY THE FIX IS NOT "GIVE THE ENGINE A DIFFERENT cwd". Cell B is the tempting
# one-line fix, in the transport rather than here - and it would be WRONG. A
# caller who writes save_file(path="beam.C21") means a file beside THEIR working
# directory. An engine spawned with someone else's cwd would resolve every
# relative path against it, silently writing where nobody looked. Inheriting the
# caller's directory is correct behaviour; this harness simply has to cope with
# what it costs.
#
# WHY IT IS NOT ignore_errors=True EITHER. That converts a loud, understood,
# transient condition into a silent permanent leak - one scratch directory left in
# TEMP per affected run, forever. What is actually true is that process teardown on
# Windows is asynchronous, so the right thing to do is WAIT for the release, with a
# deadline, and still fail loudly if it never comes.
import os
import shutil
import tempfile
import time

# Generous, because it is never reached in the healthy case: the release is
# measured in milliseconds. It exists so that a directory held FOREVER - a file an
# example genuinely left open - is still reported rather than waited on for ever.
_RELEASE_DEADLINE_SECONDS = 30.0

_POLL_SECONDS = 0.05


def remove_when_released(folder, deadline_seconds=_RELEASE_DEADLINE_SECONDS):
    """Delete a directory tree, waiting for a transient Windows hold to clear.

    Raises the underlying OSError if the hold outlasts the deadline, because at
    that point it is no longer transient and something really is holding the file.
    """
    deadline = time.monotonic() + deadline_seconds

    while True:
        try:
            shutil.rmtree(folder)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise

            time.sleep(_POLL_SECONDS)
#--------------------------------------------------------------------


class scratch_directory(object):
    """Run a block with the working directory set to a fresh temporary folder.

    Restores the previous working directory, then removes the folder - the order
    matters, because this process must not be a holder while it waits for the
    others to let go.
    """

    def __init__(self, prefix):
        self._prefix = prefix
        self._folder = None
        self._previous = None
    #-----------------------------------------

    def __enter__(self):
        self._folder = tempfile.mkdtemp(prefix=self._prefix)
        self._previous = os.getcwd()
        os.chdir(self._folder)
        return self._folder
    #-------------------------------------

    def __exit__(self, kind, value, traceback):
        os.chdir(self._previous)
        remove_when_released(self._folder)
        return False
    #----------------------------------------------
