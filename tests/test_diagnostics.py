import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('diagnostic_client', ROOT / 'worker-agent/deploy/smoke-session.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


class DiagnosticTests(unittest.TestCase):
    def test_pinned_client_and_all_generated_programs_compile_after_newline_correction(self):
        source = ROOT / 'upstream/EmbodiedEvo/scripts/smoke_session.py'
        tree = ast.parse(source.read_text())
        client = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'CLIENT' for t in n.targets))
        with self.assertRaisesRegex(SyntaxError, 'unterminated string literal'):
            compile(client, 'original-pinned-client', 'exec')
        corrected = diagnostic.fixed_client(client)
        programs = [ast.literal_eval(n.args[0]) for n in ast.walk(ast.parse(corrected))
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == 'write_text']
        self.assertEqual(len(programs), 4)
        for program in programs:
            compile(program, 'generated-submission', 'exec')
        self.assertTrue(any("k.endswith('joint_state')" in program for program in programs))

    def test_unrecognized_fixture_is_not_silently_changed(self):
        with self.assertRaisesRegex(ValueError, 'fixture changed'):
            diagnostic.fixed_client("print('different source')")


if __name__ == '__main__':
    unittest.main()
