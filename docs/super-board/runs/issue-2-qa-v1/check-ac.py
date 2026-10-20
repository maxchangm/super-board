#!/usr/bin/env python3
"""Issue #2 documentation checks. Run from the repository root."""
import argparse
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--ref', default='HEAD')
parser.add_argument('--base', default='origin/codex/pi-pilot-20261020')
args = parser.parse_args()


def git(*parts):
    return subprocess.check_output(['git', *parts], text=True)


def source(ref, path):
    return git('show', f'{ref}:{path}')


def installation_contract(text):
    before, rest = text.split('## Installation contract\n', 1)
    contract, after = rest.split('## Board shape', 1)
    return before, contract, after


install = source(args.ref, 'install.sh')
claude = source(args.ref, 'CLAUDE.md')
base_install = source(args.base, 'install.sh')
base_claude = source(args.base, 'CLAUDE.md')
failures = []


def check(name, condition):
    print(f'{"PASS" if condition else "FAIL"}: {name}')
    if not condition:
        failures.append(name)


check('AC1: usage names all four supported hosts',
      '#   ./install.sh [--no-hooks] [--protect-main] '
      '[--hosts claude,codex,pi,opencode] [target-project-dir]' in install)
if args.ref == 'HEAD':
    help_text = subprocess.check_output(['bash', 'install.sh', '--help'], text=True)
    check('AC1: actual --help exposes Pi',
          '[--hosts claude,codex,pi,opencode]' in help_text)

before, contract, after = installation_contract(claude)
base_before, _, base_after = installation_contract(base_claude)
check('AC2: installation contract names all four supported hosts',
      '[--hosts claude,codex,pi,opencode]' in contract)
check('AC2: .pi/ shares the existing optional-host conditions',
      'always linked; `.codex/`, `.pi/` and `.opencode/` only when that folder already exists, a config `host`\n'
      'key names it, `super-board-host.sh` reports it, or `--hosts` asks.' in contract)

paths = git('diff', '--name-only', f'{args.base}...{args.ref}').splitlines()
evidence = 'docs/super-board/runs/issue-2-qa-v1/'
check('AC3: diff contains only the two documentation locations and QA evidence',
      all(p in {'install.sh', 'CLAUDE.md'} or p.startswith(evidence) for p in paths))
noncomments = lambda text: '\n'.join(line for line in text.splitlines()
                                     if not line.lstrip().startswith('#'))
check('AC3: installer non-comment content is byte-for-byte unchanged',
      noncomments(install) == noncomments(base_install))
check('AC3: authoring rules outside the installation contract are unchanged',
      (before, after) == (base_before, base_after))
check('AC3: whitespace check succeeds',
      subprocess.run(['git', 'diff', '--check', f'{args.base}...{args.ref}']).returncode == 0)
print(f'Result: {len(failures)} failed checks')
sys.exit(bool(failures))
