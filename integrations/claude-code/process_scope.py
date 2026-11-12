"""Own a local process tree; never search for or kill unrelated agent processes."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import os
import signal
import subprocess


class ProcessScope:
    """Windows Job Object / POSIX process group. Not a filesystem sandbox.

    A small Python bootstrap waits on stdin until it has joined the Job Object.
    The actual CLI cannot start before assignment. Closing the Windows job also
    terminates ordinary descendants after a controller crash. WMI/remote jobs
    are outside this guarantee and must not be launched by this workflow.
    """

    def __init__(self):
        self.proc = None
        self.job = None
        if os.name == "nt":
            self.k = ctypes.WinDLL("kernel32", use_last_error=True)
            self.k.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
            self.k.CreateJobObjectW.restype = w.HANDLE
            self.k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
            self.k.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
            self.k.QueryInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p]
            self.k.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
            self.k.CloseHandle.argtypes = [w.HANDLE]

            class Limits(ctypes.Structure):
                _fields_ = [("per_process", ctypes.c_longlong), ("per_job", ctypes.c_longlong),
                            ("flags", w.DWORD), ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t),
                            ("active_limit", w.DWORD), ("affinity", ctypes.c_size_t),
                            ("priority", w.DWORD), ("scheduling", w.DWORD)]

            class Extended(ctypes.Structure):
                _fields_ = [("basic", Limits), ("io", ctypes.c_ulonglong * 6),
                            ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                            ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]

            self.job = self.k.CreateJobObjectW(None, None)
            if not self.job:
                raise ctypes.WinError(ctypes.get_last_error())
            limits = Extended()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not self.k.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                self.close()
                raise ctypes.WinError(ctypes.get_last_error())

    def start(self, command, cwd, env):
        import json
        import sys
        bootstrap = ("import sys,json,subprocess; "
                     "spec=json.loads(sys.stdin.buffer.readline()); "
                     "p=subprocess.Popen(spec['argv'],stdin=subprocess.PIPE); "
                     "p.communicate(sys.stdin.buffer.read()); sys.exit(p.returncode)")
        self.proc = subprocess.Popen([sys.executable, "-u", "-c", bootstrap], cwd=cwd, env=env,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                                     start_new_session=os.name != "nt")
        if self.job and not self.k.AssignProcessToJobObject(self.job, w.HANDLE(int(self.proc._handle))):
            error = ctypes.get_last_error()
            self.proc.kill()
            self.proc.wait()
            for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
                stream.close()
            raise ctypes.WinError(error)
        # The bootstrap cannot spawn a descendant before this write.
        self.proc.stdin.write((json.dumps({"argv": command}) + "\n").encode("utf-8"))
        self.proc.stdin.flush()
        return self.proc

    def active(self):
        if self.job:
            class Accounting(ctypes.Structure):
                _fields_ = [("times", ctypes.c_longlong * 4), ("faults", w.DWORD),
                            ("total", w.DWORD), ("active", w.DWORD), ("terminated", w.DWORD)]
            data = Accounting()
            if not self.k.QueryInformationJobObject(self.job, 1, ctypes.byref(data), ctypes.sizeof(data), None):
                raise ctypes.WinError(ctypes.get_last_error())
            return data.active
        if self.proc:
            try:
                os.killpg(self.proc.pid, 0)
                return 1
            except ProcessLookupError:
                return 0
        return 0

    def stop(self):
        if self.job:
            if not self.k.TerminateJobObject(self.job, 125):
                raise ctypes.WinError(ctypes.get_last_error())
        elif self.proc:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def close(self):
        if self.job:
            self.k.CloseHandle(self.job)
            self.job = None


def alive(pid):
    if os.name == "nt":
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        k.OpenProcess.restype = w.HANDLE
        k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
        k.CloseHandle.argtypes = [w.HANDLE]
        h = k.OpenProcess(0x1000, False, pid)
        if not h:
            return ctypes.get_last_error() != 87  # access denied is not proof of death
        try:
            code = w.DWORD()
            return not k.GetExitCodeProcess(h, ctypes.byref(code)) or code.value == 259
        finally:
            k.CloseHandle(h)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
