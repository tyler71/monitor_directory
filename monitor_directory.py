#!/usr/bin/env python3


import argparse
import pathlib
import json
import os
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--daemon",
                        action="store_true",
                        )
    parser.add_argument("--temp-file",
                        default=os.path.join(tempfile.gettempdir(), "monitor.tmp"),
                        help="Location of cache file, default {}".format(tempfile.gettempdir())
                        )
    parser.add_argument("--trim-cache",
                        action="store_true",
                        help="Remove irrelevant directories from the cache")
    parser.add_argument("--include",
                        action="append",
                        help="glob file matching, can be invoked multiple times",
                        )
    parser.add_argument("--exclude",
                        action="append",
                        help="glob file matching, can be invoked multiple times",
                        )
    parser.add_argument("command",
                        nargs=1,
                        help="Run command or script on each file: ./script file_foobar",
                        )

    parser.add_argument("directories",
                        default=[os.getcwd()],
                        nargs='*',
                        )
    args = parser.parse_args()

    # If is file, treat it as a script. If not, run as a command
    # Get scripts absolute path
    if os.path.isfile(os.path.abspath(args.command[0])):
        command = os.path.abspath(args.command[0])
    else:
        command = args.command[0]

    temp_file = args.temp_file
    args.directories = [os.path.abspath(directory) for directory in args.directories]

    # Manage loading of cache_directories.
    # Used to know when things have been processed or not.
    # If it doesn't exist, create one
    if os.path.isfile(temp_file):
        with open(temp_file) as f:
            cached_directories = json.load(f)

            if args.trim_cache is True:
                non_existing_directories = list()
                for directory in cached_directories:
                    if directory not in args.directories:
                        non_existing_directories.append(directory)
                for directory in non_existing_directories:
                    cached_directories.pop(directory)
    else:
        cached_directories = dict()

    # Decide to run as daemon or script.
    # Having updated values will trigger a write to the temporary file
    if args.daemon is True:
        while True:
            try:
                result_cached_directories = files_command_process(command,
                                                                  cached_directories,
                                                                  args.directories,
                                                                  include=args.include,
                                                                  exclude=args.exclude)
                if result_cached_directories is True:
                    write_json_file(cached_directories, temp_file)
                time.sleep(1)
            except KeyboardInterrupt:
                break
    else:
        result_cached_directories = files_command_process(command,
                                                          cached_directories,
                                                          args.directories,
                                                          include=args.include,
                                                          exclude=args.exclude)
        if result_cached_directories is True:
            write_json_file(cached_directories, temp_file)


def files_command_process(command, cache_dictionary, directories, include=None, exclude=None):
    for directory in cache_dictionary:
        # Convert list of processed files to a set
        cache_dictionary[directory][1] = set(cache_dictionary[directory][1])
    for directory in directories:
        if directory in cache_dictionary:
            cached_directory_time = cache_dictionary[directory][0]
            current_directory_time = os.stat(directory).st_mtime
            if current_directory_time > cached_directory_time:
                if include or exclude:
                    directory_files = file_include_exclude(directory=directory, include=include, exclude=exclude)
                else:
                    directory_files = (f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)))
                cache_dictionary[directory][0] = current_directory_time
                for file in directory_files:
                    if file not in cache_dictionary[directory][1]:
                        print("processing", file)
                        subprocess.run(command.split(" ") + [os.path.join(directory, file)])
                        cache_dictionary[directory][1].add(file)
                return True
        else:
            cache_dictionary[directory] = [os.stat(directory).st_mtime, set()]
            if include or exclude:
                directory_files = file_include_exclude(directory=directory, include=include, exclude=exclude)
            else:
                directory_files = (f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)))
            for file in directory_files:
                print([command, os.path.join(directory, file)])
                print("processing", file)
                subprocess.run(command.split(" ") + [os.path.join(directory, file)])
                cache_dictionary[directory][1].add(file)
            return True


def write_json_file(dictionary, temp_file):
    cached_directories = dictionary
    with open(temp_file, "w") as f:

        for directory in cached_directories:
            # Convert list of processed files to a set
            cached_directories[directory][1] = list(cached_directories[directory][1])
        json.dump(cached_directories, f, indent=4, sort_keys=True)


def file_include_exclude(*, directory, include, exclude):
    files = [file for file in os.listdir(directory)]
    if include:
        included_filenames = {file for glob_match in include
                              for file in files
                              if pathlib.PurePath(file).match(glob_match)}
    else:
        included_filenames = set()
    if exclude:
        excluded_filenames = {file for glob_match in exclude
                              for file in files
                              if pathlib.PurePath(file).match(glob_match)}
    else:
        excluded_filenames = set()

    for file in files:
        if file in included_filenames:
            yield file
        elif file not in excluded_filenames and len(excluded_filenames) > 0:
            yield file


if __name__ == '__main__':
    main()
