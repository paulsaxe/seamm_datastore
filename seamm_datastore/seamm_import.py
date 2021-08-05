#!/usr/bin/env/python

"""CLI for importing jobs to seamm datastore"""

import argparse

import getpass


class PasswordPromptAction(argparse.Action):
    def __init__(
        self,
        option_strings,
        dest=None,
        nargs="?",
        default=None,
        required=False,
        type=None,
        metavar=None,
        help=None,
    ):
        super(PasswordPromptAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            default=default,
            required=required,
            metavar=metavar,
            type=type,
            help=help,
        )

    def __call__(self, parser, args, values, option_string=None):

        if not values:
            values = getpass.getpass()

        setattr(args, self.dest, values)


def run():
    parser = argparse.ArgumentParser(
        description="Command-line utility for importing jobs to the SEAMM datastore."
    )
    parser.add_argument(
        "job_location", help="The location where you would like to import a job from."
    )
    parser.add_argument(
        "-p", dest="password", action=PasswordPromptAction, type=str, required=True
    )
    args = parser.parse_args()
    print(args)


if __name__ == "__main__":
    run()
