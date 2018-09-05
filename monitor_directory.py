#!/usr/bin/env python3


import os
import heapq
import argparse
import time
import tempfile



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directories",
                        [os.getcwd()],
                        nargs='*'
                        )
    parser.add_argument("--temp-dir",
                        default=tempfile.TemporaryDirectory)




if __name__ == '__main__':
    main()
