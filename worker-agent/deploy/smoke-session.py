"""Correct the pinned no-model fixture's newline, then run its Docker checks."""
from pathlib import Path
import sys


def fixed_client(client):
    # EmbodiedEvo 470278c scripts/smoke_session.py:49 embeds a real newline
    # inside the generated client's quoted step program, causing SyntaxError.
    broken = '"' + "step({k: v for k, v in obs['state'].items() if k.endswith('joint_state')})" + '\n"'
    if client.count(broken) != 1:
        raise ValueError('Pinned diagnostic fixture changed; review its compatibility correction')
    corrected = client.replace(broken, broken.replace('\n', '\\n'), 1)
    compile(corrected, 'fixed-no-model-client', 'exec')
    return corrected


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'upstream/EmbodiedEvo'))
    from scripts import smoke_session
    smoke_session.CLIENT = fixed_client(smoke_session.CLIENT)
    return smoke_session.main()


if __name__ == '__main__':
    raise SystemExit(main())
