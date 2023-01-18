"""pre-commit-msg hook."""
import argparse
import re
import sys
from typing import List


RESULT_SUCCESS = 0
RESULT_FAIL = 1


class Colors:
    LBLUE = "\033[00;34m"
    LRED = "\033[01;31m"
    RESTORE = "\033[0m"
    YELLOW = "\033[00;33m"


DEFAULT_TYPES = [
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
]


def validate(message: List[str], commit_types: List[str]):

    commit_type = ""
    commit_title = ""
    commit_extra_description = ""
    jira_ticket = ""
    errors: List[str] = []

    commit_txt_lines = message.splitlines()
    commit_txt_lines = [line.strip() for line in commit_txt_lines]
    commit_txt_lines = commit_txt_lines[0:-1] if commit_txt_lines[-1] == "" else commit_txt_lines

    line1_pattern = rf"({'|'.join(commit_types)})!?:\s(.*)"
    line1_match = re.match(line1_pattern, commit_txt_lines[0])
    if line1_match is not None and len(line1_match.groups()) == 2:
        commit_type = line1_match.group(1).strip()
        commit_title = line1_match.group(2).strip()
    else:
        errors.append("Error on line 1 of commit message")

    if len(commit_txt_lines) > 1 and commit_txt_lines[1] != "":
        errors.append("Error on line 2 of commit message: should be empty")

    if len(commit_txt_lines) > 1 and commit_txt_lines[-2] != "":
        line_err = len(commit_txt_lines) - 1
        errors.append(f"Error on line {line_err} of commit message: should be empty")

    last_line_pattern = r"^Refs:\s(\D+\-\d+)$"
    last_line_match = re.match(last_line_pattern, commit_txt_lines[-1])
    if last_line_match is not None and len(last_line_match.groups()) == 1:
        jira_ticket = last_line_match.group(1).strip()
    else:
        line_err = len(commit_txt_lines)
        errors.append(f"Error on line {line_err} of commit message: footer should include references like other commits or jira tickets. For example: 'Refs: #ABCD-123'")

    commit_extra_description = None
    if len(commit_txt_lines) > 3:
        middle_lines = commit_txt_lines[2:-2]
        commit_extra_description = "\n".join(middle_lines)

    good_commit = all([commit_type != "", commit_title != "", commit_extra_description != "", jira_ticket != ""])
    if good_commit and len(errors) == 0:
        return True

    errors_msg = "\n> "+ "\n> ".join(errors)
    print(f"""
        {Colors.LRED}[Bad Commit message] >>{Colors.RESTORE} {message}

        {Colors.LRED}{errors_msg}{Colors.RESTORE}

        {Colors.YELLOW}Your commit message does not follow Conventional Commits formatting
        {Colors.LBLUE}https://www.conventionalcommits.org/{Colors.YELLOW}

        Conventional Commits start with one of the below types, followed by a colon,
        followed by the commit message:{Colors.RESTORE}

            {" ".join(commit_types)}

        {Colors.YELLOW}Example commit message adding a feature:{Colors.RESTORE}

            feat: implement new API

        {Colors.YELLOW}Example commit message fixing an issue:{Colors.RESTORE}

            fix: remove infinite loop""",
    )
    return False

def main(argv=[]):
    parser = argparse.ArgumentParser(
        prog="conventional-pre-commit", description="Check a git commit message for Conventional Commits formatting."
    )
    parser.add_argument("types", type=str, nargs="*", default=DEFAULT_TYPES, help="Optional list of types to support")
    parser.add_argument("input", type=str, help="A file containing a git commit message")

    if len(argv) < 1:
        argv = sys.argv[1:]

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return RESULT_FAIL

    with open(args.input) as f:
        message = f.read()

    if validate(message, args.types) is True:
        return RESULT_SUCCESS
    return RESULT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
