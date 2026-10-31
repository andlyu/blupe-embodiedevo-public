"""Inspect real worker prerequisites without starting physics, models or jobs."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess

from core import verify_pins


def command(args, timeout=30):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{args[0]} exited {result.returncode}')
    return result.stdout.strip()


def inspect_gpu(lock):
    output = command(['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader,nounits'])
    rows = [line.split(',') for line in output.splitlines()]
    index = int(os.environ.get('EMBODIEDEVO_GPU', '0'))
    selected = rows[index]
    branch = int(selected[1].strip().split('.')[0])
    if branch != lock['required_driver_branch']:
        raise RuntimeError(f"Isaac Sim {lock['isaacsim']} requires NVIDIA driver branch {lock['required_driver_branch']}; found {selected[1].strip()}")
    if int(selected[2].strip()) < 16000:
        raise RuntimeError('At least 16 GB GPU memory is required')
    return ','.join(selected).strip() + '; renderer compatibility still requires native smoke'


def inspect_runtime(root, *, model=True):
    checks = []

    def check(name, fn):
        try:
            detail = fn()
            checks.append({'name': name, 'ok': True, 'detail': detail})
        except Exception as exc:
            checks.append({'name': name, 'ok': False, 'detail': str(exc)[:300]})

    lock = json.loads((root / 'worker-agent/runtime-lock.json').read_text())
    upstream = root / 'upstream/EmbodiedEvo'
    native = upstream / 'vendor/robodojo'
    interpreter = upstream / '.venv-robodojo/bin/python'

    def host():
        if platform.system() != 'Linux' or platform.machine() not in {'x86_64', 'AMD64'}:
            raise RuntimeError('RoboDojo requires a Linux x86_64 NVIDIA host')
        return platform.platform()

    def simulator():
        if not interpreter.is_file():
            raise RuntimeError('Missing upstream/EmbodiedEvo/.venv-robodojo/bin/python')
        code = ('import importlib.util as u, importlib.metadata as m, json; '
                'from packaging.version import Version; '
                'assert Version(m.version("isaacsim"))==Version("5.1.0"); '
                'assert u.find_spec("isaaclab") and u.find_spec("curobo"); '
                'print(json.dumps({"isaacsim":m.version("isaacsim")}))')
        return json.loads(command([str(interpreter), '-c', code]))

    def sources():
        marker = json.loads((native / '.embodiedevo-provisioned.json').read_text())
        if marker.get('commit') != lock['robodojo'] or marker.get('assets_revision') != lock['assets']['revision']:
            raise RuntimeError('Native source/assets provenance differs from runtime-lock.json')
        if command(['git', '-C', str(native), 'rev-parse', 'HEAD']) != lock['robodojo']:
            raise RuntimeError('RoboDojo source HEAD differs from runtime lock')
        command(['git', '-C', str(native), 'diff', '--quiet', 'HEAD', '--'])
        for sub, revision in lock['submodules'].items():
            path = native / sub
            if command(['git', '-C', str(path), 'rev-parse', 'HEAD']) != revision:
                raise RuntimeError('Native submodule differs: ' + sub)
            command(['git', '-C', str(path), 'diff', '--quiet', 'HEAD', '--'])
        for name in ['Robots', 'Object', 'Material', 'Eval_Layout']:
            if not (native / 'Assets' / name).is_dir():
                raise RuntimeError('Missing Assets/' + name)
        return {'robodojo': lock['robodojo'], 'assets': lock['assets']['revision']}

    def dependencies():
        return {name: importlib.metadata.version(name) for name in
                ['gymnasium', 'numpy', 'pillow', 'pyyaml', 'cloudpickle', 'psutil']}

    def image():
        return command(['docker', 'image', 'inspect', 'embodiedevo-agent:latest', '--format', '{{.Id}}'])

    def login():
        home = Path(os.environ.get('EMBODIEDEVO_CODEX_HOME', str(Path.home() / '.codex'))).expanduser()
        if not (home / 'config.toml').is_file() or not (home / 'auth.json').is_file():
            raise RuntimeError('Complete operator login on this host with deploy/login.sh')
        command(['docker', 'run', '--rm', '--network', 'none', '-e', 'CODEX_HOME=/auth',
                 '-v', str(home.resolve()) + ':/auth:ro', 'embodiedevo-agent:latest', 'codex', 'login', 'status'])
        return 'Stored login recognized; live model access requires a real bounded job'

    check('pinned_method_sources', lambda: verify_pins(root) or 'Match website pins')
    check('host', host)
    check('gpu', lambda: inspect_gpu(lock))
    check('host_dependencies', dependencies)
    check('simulator_interpreter', simulator)
    check('native_source_and_assets', sources)
    check('agent_image', image)
    if model:
        check('operator_login', login)
    return {'ready': all(c['ok'] for c in checks), 'checks': checks,
            'physics_started': False, 'model_called': False, 'physical_execution_supported': False}
