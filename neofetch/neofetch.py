# -*- coding: utf-8 -*-

import argparse
import multiprocessing
import os
import socket
import subprocess
import sys

IS_PY3 = sys.version_info >= (3, 0)


class CommandProcessor(object):
    def __init__(self, *commands):
        self.commands = [c() for c in commands]

    def parse(self):
        result = {}
        for c in self.commands:
            result.update(c.run())
        return result


class BaseCommand(object):
    def run(self):
        raise NotImplementedError()


class BaseMultiprocessingCommand(BaseCommand):
    def __init__(self):
        self.parent_conn, self.child_conn = multiprocessing.Pipe()
        self.proc = multiprocessing.Process(
            target=self.target, args=(self.child_conn, ))
        self.proc.start()

    def target(self, conn):
        res = self.func()
        conn.send(res)

    def run(self):
        self.proc.join()
        return self.parent_conn.recv()

    def func(self):
        raise NotImplementedError()


class BaseSubprocessCommand(BaseCommand):
    command = None
    shell = False

    def __init__(self):
        self.proc = subprocess.Popen(
            self.command, shell=self.shell, stdout=subprocess.PIPE)

    @staticmethod
    def strip_output(output):
        if IS_PY3:
            output = str(output, "utf-8")
        return output.strip()

    @staticmethod
    def parse(output):
        raise NotImplementedError()

    def run(self):
        output, _ = self.proc.communicate()
        output = self.strip_output(output)
        return self.parse(output)


class SystemProfilerBase(BaseSubprocessCommand):
    @staticmethod
    def parse(output):
        res = {}
        for line in output.splitlines():
            line = line.strip().split(': ')
            if len(line) > 1:
                res[line[0]] = line[1]
        return res


class SystemProfilerSoftware(SystemProfilerBase):
    command = ["/usr/sbin/system_profiler", "SPSoftwareDataType"]

    @staticmethod
    def parse(output):
        res = super(SystemProfilerSoftware,
                    SystemProfilerSoftware).parse(output)
        return {
            "os_version": res["System Version"],
            "uptime": res["Time since boot"]
        }


class SystemProfilerHardware(SystemProfilerBase):
    command = ["/usr/sbin/system_profiler", "SPHardwareDataType"]

    @staticmethod
    def parse(output):
        res = super(SystemProfilerHardware,
                    SystemProfilerHardware).parse(output)
        return {"model": res["Model Identifier"]}


class SystemProfilerDisplays(SystemProfilerBase):
    command = ["/usr/sbin/system_profiler", "SPDisplaysDataType"]

    @staticmethod
    def parse(output):
        res = super(SystemProfilerDisplays,
                    SystemProfilerDisplays).parse(output)
        return {"size": res["Resolution"]}


class Kernel(BaseSubprocessCommand):
    command = ["uname", "-r"]

    @staticmethod
    def parse(output):
        return {"kernel": output}


class CPU(BaseSubprocessCommand):
    command = ["sysctl", "-n", "machdep.cpu.brand_string"]

    @staticmethod
    def parse(output):
        return {"cpu": output}


class BatteryPercentage(BaseSubprocessCommand):
    command = 'pmset -g batt | grep -Eo "\d+%"'
    shell = True

    @staticmethod
    def parse(output):
        return {"battery_percentage": output}


class LocalIP(BaseMultiprocessingCommand):
    def func(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return {"local_ip": s.getsockname()[0]}
        except socket.error:
            return {"local_ip": ""}


class HostName(BaseCommand):
    def run(self):
        return {"hostname": socket.gethostname()}


class Shell(BaseCommand):
    def run(self):
        return {"shell": os.environ.get('SHELL', '')}


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
    value = int(
        os.environ.get('NEOFETCH_%s' % name.upper().replace('-', '_'),
                       default))
    parser.add_argument(
        '--%s' % name, type=int, default=value, help='Default: %d' % value)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group('colors')
    for name, default in (('title', 92), ('sub-title', 93), ('color-1', 92),
                          ('color-2', 93), ('color-3', 91), ('color-4', 95),
                          ('color-5', 94)):
        _add_color_argument(group, name, default)

    args = parser.parse_args()

    cp = CommandProcessor(
        BatteryPercentage,
        CPU,
        HostName,
        Kernel,
        LocalIP,
        Shell,
        SystemProfilerSoftware,
        SystemProfilerDisplays,
        SystemProfilerHardware,
    )
    params = cp.parse()
    params.update(
        dict(
            hostname_sep="-" * len(params["hostname"]),
            title_color=args.title,
            subtitles_color=args.sub_title,
            color_1=args.color_1,
            color_2=args.color_2,
            color_3=args.color_3,
            color_4=args.color_4,
            color_5=args.color_5))
    return TEMPLATE.format(**params)


if __name__ == '__main__':
    print(main())
