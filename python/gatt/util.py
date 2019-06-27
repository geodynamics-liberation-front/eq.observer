#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

import argparse
import os
import re
import subprocess
import sys
import traceback

from functools import reduce


# TODO : mount without invoking the mount command
# import ctypes
# import ctypes.util
# libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
# libc.mount.argtypes = (ctypes.c_char_p,
#                        ctypes.c_char_p,
#                        ctypes.c_char_p,
#                        ctypes.c_ulong,
#                        ctypes.c_char_p)
#
# def mount(source, target, fs, options=''):
#   ret = libc.mount(source, target, fs, 0, options)
#   if ret < 0:
#     errno = ctypes.get_errno()
#     raise OSError(errno,
#                   "Error mounting {} ({}) on {} with options '{}': {}".
#      format(source, fs, target, options, os.strerror(errno)))

program_description =\
    "Modifies the raspbian image for use as an eq.Observer device"
boot_part = "boot"
rootfs_part = "rootfs"

fdisk_cmd = ["fdisk", "-l", "{image_file}"]
fdisk_patterns = [
        ("size", r"^Units:.*? = (\d*) (\w*)",
         lambda m: int(m.group(1) * {'bytes': 1}[m.group(2)])),
        ("diskid", r"^Disk identifier: 0x(.*)",
         lambda m: m.group(1)),
        ("partitions",
         r"({image_file}\d*)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.*)",
         lambda m: {"name": m.group(1),
                    "sector_offset": int(m.group(2)),
                    "sector_size": int(m.group(4))})
]

blkid_cmd = ["blkid", "--probe",
             "--offset", "{offset}",
             "--size", "{size}",
             "--output", "udev",
             "{image}"]
blkid_patterns = [
        ("label", "^ID_FS_LABEL=(.*)", lambda m: m.group(1)),
        ("fstype", "^ID_FS_TYPE=(.*)", lambda m: m.group(1))
]

mount_cmd = ["mount",
             "-t", "{fstype}",
             "-o", "loop,rw,offset={offset},sizelimit={size}",
             "{image}", "{mount_point}"]
mount_boot_cmd = ["mount", "--bind",
                  "{boot}", "{root}"]
umount_cmd = ["umount",  "{mount_point}"]


def match(patterns, lines):
    result = {}
    for line in lines:
        for pattern in patterns:
            name = pattern[0]
            regex = pattern[1]
            func = pattern[2]
            line_match = re.match(regex, line)
            if line_match:
                if name not in result:
                    result[name] = []
                result[name].append(func(line_match))
    return result


def cmd(args, format_args={}):
    args = [arg.format(**format_args) for arg in args]
    print("CMD: " + (" ".join(args)))
    result = subprocess.check_output(args).decode("UTF-8")
    for line in result.split("\n"):
        print("---> " + line)
    return result


def parse_cmd(args, patterns=[], format_args={}, update=False):
    """
Calls a subprocess using the arguments from args.  The output is matched
one line at a time against the patterns list.

patterns is a list of tuples of the form of (name, regex, function)
    name is used as the key for the result in the results dictionary
    regex is used to match the output line
    function is used process the match object

    Each of these parameters, if a string, will be formatted with the
    format_args dictionary.
"""
    patterns = [tuple((i.format(**format_args)
                if hasattr(i, "format") and callable(getattr(i, "format"))
                else i for i in pattern))
                for pattern in patterns]
    results = match(patterns, cmd(args, format_args).split("\n"))
    if update:
        format_args.update(results)
    return results


def group_cmd(args, groups=[], patterns=[], format_args={}, update=False):
    groups = [tuple((i.format(**format_args)
                     if hasattr(i, "format") and callable(getattr(i, "format"))
                     else i for i in group))
              for group in groups]
    patterns = [tuple((i.format(**format_args)
                if hasattr(i, "format") and callable(getattr(i, "format"))
                else i for i in pattern))
                for pattern in patterns]

    result = {}
    path = []
    lines = cmd(args, format_args).split("\n")
    for line in lines:
        for n, group in enumerate(groups):
            name = group[0]
            regex = group[1]
            func = group[2]
            line_match = re.match(regex, line)
            if line_match:
                path = path[:n]
                local_result = reduce(lambda d, key: d[key], path, result)
                group_name = func(line_match)
                path.append(group_name)
                if group_name not in local_result:
                    local_result[group_name] = {}
                print("Group match : " + repr(path))

        for pattern in patterns:
            name = pattern[0]
            regex = pattern[1]
            func = pattern[2]
            line_match = re.match(regex, line)
            if line_match:
                print(name + " match : " + repr(path))
                local_result = reduce(lambda d, key: d[key], path, result)
                if name in local_result:
                    local_result[name] = [local_result[name], func(line_match)]
                else:
                    local_result[name] = func(line_match)
    return result


def wifi_info():
    cmd_args = ["sudo", "iwlist", "scan"]
    patterns = [
        ("essid", "^\\s*ESSID:\"(.*)\"", lambda m: m.group(1)),
        ("mac_address", "^\\s+Cell \\S+ - Address: (\\S+)", lambda m:m.group(1)),
        ("encryption_key", "^\\s+Encryption key:(.+)", lambda m: m.group(1)),
        ("authentication_suites", "^\\s*Authentication Suites.*: (.+)", lambda m: m.group(1)),
        ("quality", "^\\s*Quality=(\\S+)", lambda m: m.group(1)),
        ("quality_value", "^\\s*Quality=(\\d+)/(\\d+)", lambda m: float(m.group(1))/float(m.group(2))),
        ("signal_level", "^\\s*Quality=\\S+\\s+Signal level=(\\S+)", lambda m: m.group(1))
    ]
    groups = [
        ("interface", "^(\\S+)", lambda m: m.group(1)),
        ("cell", "^\\s+(Cell \\S+)", lambda m:m.group(1))
    ]
    return group_cmd(cmd_args, groups, patterns)


def essids():
    info = wifi_info()
    essid_set = set()
    for cell in info.values():
        for properties in cell.values():
            essid_set.add(properties['essid'])
    return sorted(essid_set)

# ini_section_re=re.compile("^\[(.*)\]$")
# ini_comment_re=re.compile("^[;#]")
# ini_keyvalue_re=re.compile("^([^[;#].*?)=(.*)$")
# def read_ini(filename):
#     ini={}
#     section=ini
#     with open(filename) as ini_file:
#         for line in ini_file:
#             match = ini_comment_re.match(line) or
#                     ini_keyvalue_re.match(line) or
#                     ini_section_re.match(line)
#             if match:
#                 if match.re==ini_comment_re:
#                     # ignore comment
#                     pass
#                 elif match.re==ini_section_re:
#                     section={}
#                     ini[match.group(1)]=section
#                 elif match.re==ini_keyvalue_re:
#                     section[match.group(1)]=match.group(2)
#     return ini


def fdisk_info(image_file):
    return parse_cmd(fdisk_cmd, fdisk_patterns, {"image_file": image_file})


def mount_image(image_file, mount_dir):
    mount_points = []
    print("Mounting image %s" % image_file)
    fdisk_results = fdisk_info(image_file)
    sector_size = fdisk_results["size"][0]
    for part in fdisk_results["partitions"]:
        part["offset"] = sector_size * part["sector_offset"]
        part["size"] = sector_size * part["sector_size"]
        part["image"] = image_file
        # get the filesystem info
        parse_cmd(blkid_cmd, blkid_patterns, part, True)
        part["mount_point"] = os.path.join(mount_dir, part["label"][0])
        part["fstype"] = part["fstype"][0]
        # create the mount point
        os.mkdir(part["mount_point"])
        mount_points.append(part["mount_point"])
        print(cmd(mount_cmd, part))
    return mount_points


def setup(args):
    print("###: mkdir {}".format(args.mount))
    os.mkdir(args.mount)


def umount(args, vars):
    if os.path.exists(args.mount) and os.path.isdir(args.mount):
        children = os.listdir(args.mount)
        print(children)
        if "rootfs" in children:
            children.insert(0, os.path.join("rootfs", "boot"))
        print(children)

        for child in children:
            mount_point = os.path.join(args.mount, child)
            try:
                cmd(umount_cmd, {"mount_point": mount_point})
            except Exception:
                print("Couldn't unmount {mount_point}"
                      .format(mount_point=mount_point))
            try:
                os.rmdir(mount_point)
            except Exception:
                print("Couldn't remove {mount_point}"
                      .format(mount_point=mount_point))
        try:
            os.rmdir(args.mount)
        except Exception:
            print("Couldn't remove {mount_dir}".format(mount_dir=args.mount))


def mount(args, vars):
    if not args.image:
        sys.exit(1)
    mount_points = mount_image(args.image, args.mount)
    boot_mount = os.path.join(args.mount, boot_part)
    vars['boot'] = boot_mount
    root_mount = os.path.join(args.mount, rootfs_part)
    vars['rootfs'] = root_mount
    assert boot_mount in mount_points, "missing expected boot partition"
    assert root_mount in mount_points, "missing expected rootfs partition"
    cmd(mount_boot_cmd, {"boot": boot_mount,
                         "root": os.path.join(root_mount, "boot")})

    vars["mount_points"] = mount_points


def main():
    parser = argparse.ArgumentParser(description=program_description)
    parser.add_argument("commands", metavar="CMD", nargs="+",
                        help="One or more image tool commands")
    parser.add_argument(
        "-m", "--mount",
        dest="mount", default="mnt",
        help="The location under which the image partitions are mounted")
    parser.add_argument("-i", "--image",
                        dest="image",
                        help="The image to mount")
    parser.parse_args()
    args = parser.parse_args()
    if not args.image:
        image_list = [f for f in os.listdir() if f.endswith(".img")]
        if len(image_list) == 1:
            args.image = image_list[0]
#    image_file = args.image
#    mnt = args.mount
    commands = args.commands.copy()

    # get the name we were invoked with
    vars = {}
    try:
        while len(commands) > 0:
            command = commands.pop(0)
            if command == "mount":
                # mount needs an image file
                setup(args)
                try:
                    mount(args, vars)
                except SystemExit:
                    pass
            elif command == "umount":
                umount(args, vars)
            else:
                help("Unkown command {}".format(command))
    except SystemExit:
        pass
    except Exception:
        print("image-tool encountered an error")
        traceback.print_exc()


if __name__ == "__main__":
    results = wifi_info()
    essid_list = results['essid']
