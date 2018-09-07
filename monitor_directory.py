#!/usr/bin/env python3


import argparse
import json
import os
import tempfile
import time
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--daemon",
                        action="store_true",
                        )
    parser.add_argument("--temp-file",
                        default=os.path.join(tempfile.gettempdir(), "monitor.tmp"),
                        )
    parser.add_argument("script",
                        nargs=1)
    parser.add_argument("directories",
                        default=[os.getcwd()],
                        nargs='*',
                        )
    args = parser.parse_args()

    script_file = os.path.abspath(args.script[0])
    temp_file = args.temp_file
    args.directories = [os.path.abspath(directory) for directory in args.directories]

    if os.path.isfile(temp_file):
        with open(temp_file) as f:
            cached_directories = json.load(f)

            non_existing_directories = list()
            for directory in cached_directories:
                if directory not in args.directories:
                    non_existing_directories.append(directory)
            for directory in non_existing_directories:
                cached_directories.pop(directory)
    else:
        cached_directories = dict()

    update_json = False
    if args.daemon is True:
        while True:
            try:
                result_cached_directories = process_files(script_file, cached_directories, temp_file, args.directories)
                if result_cached_directories[0] is True:
                    write_json_file(result_cached_directories[1], temp_file)
            except KeyboardInterrupt:
                exit()
            except FileNotFoundError as e:
                print(e, "was not found, removing from tested entries")
                # args.directories.remove()
    else:
        result_cached_directories = process_files(script_file, cached_directories, temp_file, args.directories)
        if result_cached_directories[0] is True:
            update_json = True
        if update_json is True:
            write_json_file(result_cached_directories[1], temp_file)


def process_files(command, cached_directories, temp_file, directories):
    if os.path.isfile(temp_file):
        result = process_cached(command, cached_directories, directories)
    else:
        result = process_non_cached(command, cached_directories, directories)
    return (result, cached_directories)


def process_non_cached(command, cache_dictionary, directories):
    for directory in directories:
        cache_dictionary[directory] = [os.stat(directory).st_mtime, set()]
        directory_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for file in directory_files:
            print("processing non cached", file)
            subprocess.run([command, os.path.join(directory, file)])
            # TODO; add processing of file
            cache_dictionary[directory][1].add(file)
    return True


def process_cached(command, cache_dictionary, directories):
    for directory in cache_dictionary:
        # Convert list of processed files to a set
        cache_dictionary[directory][1] = set(cache_dictionary[directory][1])
    for directory in directories:
        if directory in cache_dictionary:
            cached_directory_time = cache_dictionary[directory][0]
            current_directory_time = os.stat(directory).st_mtime
            if current_directory_time > cached_directory_time:
                directory_files = (f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)))
                cache_dictionary[directory][0] = current_directory_time
                for file in directory_files:
                    if file not in cache_dictionary[directory][1]:
                        print("processing", file)
                        subprocess.run([command, os.path.join(directory, file)])
                        cache_dictionary[directory][1].add(file)
                return True
        else:
            cache_dictionary[directory] = [os.stat(directory).st_mtime, set()]
            directory_files = (f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)))
            for file in directory_files:
                print([command, os.path.join(directory, file)])
                print("processing", file)
                subprocess.run([command, os.path.join(directory, file)])
                cache_dictionary[directory][1].add(file)
            return True


def write_json_file(dictionary, temp_file):
    cached_directories = dictionary
    with open(temp_file, "w") as f:

        for directory in cached_directories:
            # Convert list of processed files to a set
            cached_directories[directory][1] = list(cached_directories[directory][1])
        json.dump(cached_directories, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
