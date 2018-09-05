#!/usr/bin/env python3


import os
import argparse
import tempfile
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--temp-file",
                        default=os.path.join(tempfile.gettempdir(), "monitor.tmp"))
    parser.add_argument("directories",
                        default=[os.getcwd()],
                        nargs='*',
                        )
    args = parser.parse_args()

    temp_file = args.temp_file
    if os.path.isfile(temp_file):
        with open(temp_file) as f:
            cached_directories = json.load(f)
        cached_directories = process_cached(cached_directories, args.directories)
        write_json_file(cached_directories, temp_file)

    else:
        cached_directories = dict()
        cached_directories = process_non_cached(cached_directories, args.directories)
        write_json_file(cached_directories, temp_file)
    print(cached_directories)


def write_json_file(dictionary, temp_file):
    cached_directories = dictionary
    with open(temp_file, "w") as f:

        for directory in cached_directories:
            # Convert list of processed files to a set
            cached_directories[directory][1] = list(cached_directories[directory][1])
        json.dump(cached_directories, f, indent=4, sort_keys=True)


def process_non_cached(cache_dictionary, directories):
    for directory in directories:
        cache_dictionary[directory] = [os.stat(directory).st_mtime, set()]
        cached_processed_files = cache_dictionary[directory][1]
        directory_files = (f for f in os.listdir(directory) if os.path.isfile(f))
        for file in directory_files:
            print("processing non cached", file)
            cached_processed_files.add(file)
            # TODO; add processing of file
    return cache_dictionary


def process_cached(cache_dictionary, directories):
    for directory in cache_dictionary:
        # Convert list of processed files to a set
        cache_dictionary[directory][1] = set(cache_dictionary[directory][1])
    for directory in directories:
        if directory in cache_dictionary:
            cached_processed_files = cache_dictionary[directory][1]
            cached_directory_time = cache_dictionary[directory][0]
            current_directory_time = os.stat(directory).st_mtime
            if current_directory_time > cached_directory_time:
                directory_files = (f for f in os.listdir(directory) if os.path.isfile(f))
                for file in directory_files:
                    print("processing cached", file)
                    if file not in cached_processed_files:
                        print("processing non cached", file)
                        cached_processed_files.add(file)
    return cache_dictionary


if __name__ == '__main__':
    main()
