# -*- coding: utf-8 -*-

import argparse
import os
import socket
import subprocess
import sys


IS_PY3 = sys.version_info >= (3, 0)


_system_profiler_cache = {}


def _system_profiler(resource, name):
    global  _system_profiler_cache
    if resource not in _system_profiler_cache:
        proc = subprocess.Popen(["/usr/sbin/system_profiler", resource], stdout=subprocess.PIPE)
        stdout, _stderr = proc.communicate()
        if IS_PY3:
            stdout = str(stdout, "utf-8")
        res = {}
        for line in stdout.splitlines():
            line = line.strip().split(': ')
            if len(line) > 1:
                res[line[0]] = line[1]
        _system_profiler_cache[resource] = res
    return _system_profiler_cache[resource][name]


def _strip_output(*command, **kwargs):
    kwargs.setdefault('stdout', subprocess.PIPE)
    proc = subprocess.Popen(command, **kwargs)
    stdout, _stderr = proc.communicate()
    if IS_PY3:
        stdout = str(stdout, "utf-8")
    return stdout.strip()


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def get_hostname():
    return socket.gethostname()


def get_os_version():
    return _system_profiler("SPSoftwareDataType", "System Version")


def get_model():
    return _system_profiler("SPHardwareDataType", "Model Identifier")


def get_screen_size():
    return _system_profiler("SPDisplaysDataType", "Resolution")


def get_uptime():
    return _system_profiler("SPSoftwareDataType", "Time since boot")


def get_shell():
    return os.environ.get('SHELL', '')


def get_kernel():
    return _strip_output("uname", "-r")


def get_cpu_spec():
    return _strip_output("sysctl", "-n", "machdep.cpu.brand_string")


TEMPLATE = u"""\
\033[{color_1}m                    'c.           \033[{title_color}m{hostname}\033[0m
\033[{color_1}m                 ,xNMM.           \033[0m{hostname_sep}
\033[{color_1}m               .OMMMMo            \033[{subtitles_color}mOS\033[0m: {os_version}
\033[{color_1}m               OMMM0,             \033[{subtitles_color}mKernel\033[0m: {kernel}
\033[{color_1}m     .;loddo:' loolloddol;.       \033[{subtitles_color}mModel\033[0m: {model}
\033[{color_1}m   cKMMMMMMMMMMNWMMMMMMMMMM0:m    \033[{subtitles_color}mShell\033[0m: {shell}
\033[{color_2}m .KMMMMMMMMMMMMMMMMMMMMMMMWd.     \033[{subtitles_color}mUptime\033[0m: {uptime}
\033[{color_2}m XMMMMMMMMMMMMMMMMMMMMMMMX.       \033[{subtitles_color}mResolution\033[0m: {size}
\033[{color_3}m;MMMMMMMMMMMMMMMMMMMMMMMM:        \033[{subtitles_color}mCPU\033[0m: {cpu}
\033[{color_3}m:MMMMMMMMMMMMMMMMMMMMMMMM:        \033[{subtitles_color}mLocal IP\033[0m: {local_ip}
\033[{color_3}m.MMMMMMMMMMMMMMMMMMMMMMMMX.\033[0m
\033[{color_3}m kMMMMMMMMMMMMMMMMMMMMMMMMWd.\033[0m
\033[{color_4}m .XMMMMMMMMMMMMMMMMMMMMMMMMMMk\033[0m
\033[{color_4}m  .XMMMMMMMMMMMMMMMMMMMMMMMMK.\033[0m
\033[{color_5}m    kMMMMMMMMMMMMMMMMMMMMMMd\033[0m
\033[{color_5}m     ;KMMMMMMMWXXWMMMMMMMk.\033[0m
\033[{color_5}m       .cooc,.    .,coo:.\033[0m

                                  \033[30m███\033[0m\033[91m███\033[0m\033[92m███\033[0m\033[93m███\033[0m\033[94m███\
\033[0m\033[95m███\033[0m\033[96m███\033[0m\033[97m███\033[0m\
"""


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group('colors')
    group.add_argument('--title', type=int, default=92, help='Default: 92')
    group.add_argument('--sub-title', type=int, default=93, help='Default: 93')
    group.add_argument('--color-1', type=int, default=92, help='Default: 92')
    group.add_argument('--color-2', type=int, default=93, help='Default: 92')
    group.add_argument('--color-3', type=int, default=91, help='Default: 92')
    group.add_argument('--color-4', type=int, default=95, help='Default: 92')
    group.add_argument('--color-5', type=int, default=94, help='Default: 92')

    args = parser.parse_args()

    hostname = get_hostname()
    return TEMPLATE.format(
        hostname=hostname,
        hostname_sep="-" * len(hostname),
        os_version=get_os_version(),
        kernel=get_kernel(),
        model=get_model(),
        shell=get_shell(),
        uptime=get_uptime(),
        size=get_screen_size(),
        cpu=get_cpu_spec(),
        local_ip=get_local_ip(),
        title_color=args.title,
        subtitles_color=args.sub_title,
        color_1=args.color_1,
        color_2=args.color_2,
        color_3=args.color_3,
        color_4=args.color_4,
        color_5=args.color_5
    )


if __name__ == '__main__':
    print(main())
