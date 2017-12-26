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
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except socket.error:
        return ''


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


def get_battery_percentage():
    return _strip_output('pmset -g batt | grep -Eo "\d+%"', shell=True)


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
\033[{color_3}m.MMMMMMMMMMMMMMMMMMMMMMMMX.       \033[{subtitles_color}mBattery\033[0m: {battery_percentage}
\033[{color_3}m kMMMMMMMMMMMMMMMMMMMMMMMMWd.
\033[{color_4}m .XMMMMMMMMMMMMMMMMMMMMMMMMMMk
\033[{color_4}m  .XMMMMMMMMMMMMMMMMMMMMMMMMK.
\033[{color_5}m    kMMMMMMMMMMMMMMMMMMMMMMd
\033[{color_5}m     ;KMMMMMMMWXXWMMMMMMMk.
\033[{color_5}m       .cooc,.    .,coo:.

                                  \033[30m███\033[0m\033[91m███\033[0m\033[92m███\033[0m\033[93m███\033[0m\033[94m███\
\033[0m\033[95m███\033[0m\033[96m███\033[0m\033[97m███\033[0m\
"""


def _add_color_argument(parser, name, default):
    value = int(os.environ.get('NEOFETCH_%s' % name.upper().replace('-', '_'), default))
    parser.add_argument('--%s' % name, type=int, default=value, help='Default: %d' % value)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group('colors')
    for name, default in (('title', 92), ('sub-title', 93), ('color-1', 92), ('color-2', 93), ('color-3', 91),
                         ('color-4', 95), ('color-5', 94)):
        _add_color_argument(group, name, default)

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
        battery_percentage=get_battery_percentage(),
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
