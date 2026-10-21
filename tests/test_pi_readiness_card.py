#!/usr/bin/env python3
"""Keep hydrated Cards out of Pi readiness shell commands, with real guard proof."""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

KIT = Path(__file__).resolve().parents[1]
PI = shutil.which('pi')
LOADERS = [parent / 'core/extensions/loader.js' for parent in Path(PI).resolve().parents] if PI else []
LOADER = next((path for path in LOADERS if path.is_file()), None)


class PiReadinessCard(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "worker's repo"
        self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['bash', str(KIT / 'install.sh'), '--hosts', 'claude,pi', str(self.root)],
                       check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, str(KIT / 'tests/fixtures/install_worker_skills.py'), str(self.root)], check=True)
        self.card = dict(number=14, status='Ready', title='ordinary prose', labels=['bug'],
                         body='Never read .env or credentials.json. Keep café prose unchanged.\n',
                         repairReservation=dict(phase='final', repairs=2, owner='fixture-owner',
                                                diagnosis_cause='fixture cause', diagnosis_test='true'),
                         custom={'nested': [None, False, 'literal $HOME; $(not-a-command)']})
        self.input = self.base / 'card.json'
        self.hydrated = self.base / 'hydrated.json'
        self.hydrated.write_text(json.dumps(self.card))
        self.config = self.base / 'config.json'
        self.config.write_text(json.dumps(dict(verify_commands=['git diff --check'],
                                              pi=dict(provider='fixture', model='fixture'))))
        binary = self.base / 'bin'
        binary.mkdir()
        (binary / 'gh').write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
assert sys.argv[1:3] == ['issue','view'], sys.argv
card=json.loads(Path(os.environ['SB_HYDRATED']).read_text())
print(json.dumps(card))
''')
        (binary / 'pi').write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
Path(os.environ['SB_PROMPT']).write_text(sys.stdin.read())
print(json.dumps(dict(status='halted',column='Ready',detail='skills-readiness: fixture halt',
                     prUrl=None,branch=None,priorFindings=None)))
sys.exit(int(os.environ.get('SB_EXIT','0')))
''')
        for path in binary.iterdir():
            path.chmod(0o755)
        self.prompt = self.base / 'prompt.txt'
        self.env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'], HOME=str(self.base / 'home'),
                        SUPER_BOARD_SKILLS_HOME=str(self.base / 'home'), SB_PROMPT=str(self.prompt),
                        SB_HYDRATED=str(self.hydrated), TMPDIR=str(self.base),
                        SUPER_BOARD_PI_ROOT=str(self.root), SUPER_BOARD_PI_PYTHON=sys.executable,
                        SUPER_BOARD_PI_GUARDS=str(KIT / 'scripts/super-board-pi-guards.py'))

    def launch(self, lane='build', child_exit=0):
        card = dict(self.card)
        del card['body']
        self.input.write_text(json.dumps(card))
        process = subprocess.run(['bash', str(KIT / 'scripts/super-board-pi-lane.sh'), '--pi',
                                  '--config', str(self.config), '--card', str(self.input), '--lane', lane],
                                 cwd=self.root, env=dict(self.env, SB_EXIT=str(child_exit)),
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, child_exit or 10, process.stdout + process.stderr)
        return self.prompt.read_text()

    def recheck(self, prompt):
        command = re.search(r'^```(?:sh|bash)\n(.+)\n```', prompt, re.M)
        if command:
            return command[1]
        legacy = re.search(r'First operation: recheck (.+?) with the Card JSON below', prompt)
        self.assertIsNotNone(legacy, prompt)
        card = json.loads(re.search(r'^Card: (.+)$', prompt, re.M)[1])
        return legacy[1] + " <<'CARD'\n" + json.dumps([card]) + '\nCARD'

    def run_recheck(self, command):
        return subprocess.run(command, shell=True, cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=30)

    def test_file_recheck_preserves_hydrated_card_and_halt_evidence_in_all_lanes(self):
        for lane, child_exit in [('build', 0), ('qa', 10), ('review', 79)]:
            with self.subTest(lane=lane):
                command = self.recheck(self.launch(lane, child_exit))
                self.assertNotRegex(command, r'--cards\s+-\s', 'worker still has to interpolate Card prose into Bash')
                argv = shlex.split(command)
                snapshot = argv[argv.index('--cards') + 1]
                self.assertNotEqual(snapshot, '-', 'worker still has to interpolate Card prose into Bash')
                self.assertEqual(json.loads(Path(snapshot).read_text()), [self.card])
                self.assertNotIn(self.card['body'], command)
                self.assertEqual(argv[argv.index('--lane') + 1], lane)
                checked = self.run_recheck(command)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertTrue(json.loads(checked.stdout)['ready'])
                (self.root / '.agents/skills/code-review/SKILL.md').unlink()
                missing = self.run_recheck(command)
                self.assertEqual(missing.returncode, 10, missing.stdout + missing.stderr)
                self.assertEqual(json.loads(Path(snapshot).read_text()), [self.card])
                subprocess.run([sys.executable, str(KIT / 'tests/fixtures/install_worker_skills.py'), str(self.root)], check=True)

    @unittest.skipUnless(LOADER and LOADER.is_file() and shutil.which('node'), 'native Pi loader unavailable')
    def test_native_pi_guard_accepts_generated_recheck_but_blocks_protected_reads(self):
        command = self.recheck(self.launch())
        commands = self.base / 'commands.json'
        commands.write_text(json.dumps([command, 'cat .env', 'cat credentials.json']))
        source = '''
const {loadExtensions}=await import(process.argv[1]);
const {readFileSync}=await import('node:fs');
const r=await loadExtensions([process.argv[2]],process.cwd());
if(r.errors.length)throw new Error(JSON.stringify(r.errors));
const guard=r.extensions[0].handlers.get('tool_call')[0];
const commands=JSON.parse(readFileSync(process.argv[3],'utf8'));
const results=[];
for(const command of commands)results.push(await guard({toolName:'bash',input:{command}}));
results.push(await guard({toolName:'read',input:{path:'.env'}}));
console.log(JSON.stringify(results));
'''
        native = subprocess.run(['node', '--input-type=module', '-e', source, LOADER.as_uri(),
                                 str(KIT / 'scripts/super-board-pi-guards.ts'), str(commands)],
                                cwd=self.root, env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(native.returncode, 0, native.stderr)
        allowed, *denied = json.loads(native.stdout)
        self.assertEqual(allowed, {}, 'ordinary Card prose was scanned as a secret-file read')
        for result in denied:
            self.assertTrue(result['block'])
            self.assertIn('guard-secrets', result['reason'])
        checked = self.run_recheck(command)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertTrue(json.loads(checked.stdout)['ready'])


if __name__ == '__main__':
    unittest.main()
