import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'worker-agent'))
import doctor
spec = importlib.util.spec_from_file_location('polling_worker', ROOT / 'worker-agent/run.py')
polling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(polling)


class RuntimeTests(unittest.TestCase):
    def test_cuda_capable_595_driver_is_rejected_for_isaac_51(self):
        lock = json.loads((ROOT / 'worker-agent/runtime-lock.json').read_text())
        with patch.object(doctor, 'command', return_value='NVIDIA L4, 595.91.07, 23034'):
            with self.assertRaisesRegex(RuntimeError, 'requires NVIDIA driver branch 580'):
                doctor.inspect_gpu(lock)
        with patch.object(doctor, 'command', return_value='NVIDIA L4, 580.196.07, 23034'):
            self.assertIn('580.196.07', doctor.inspect_gpu(lock))

    def test_missing_runtime_never_claims_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'worker-agent').mkdir()
            (root / 'worker-agent/runtime-lock.json').write_text((ROOT / 'worker-agent/runtime-lock.json').read_text())
            with patch.object(doctor, 'verify_pins', side_effect=ValueError('missing sources')), \
                 patch.object(doctor, 'command', side_effect=RuntimeError('missing executable')), \
                 patch.object(doctor.platform, 'system', return_value='Darwin'):
                result = doctor.inspect_runtime(root)
            self.assertFalse(result['ready'])
            self.assertFalse(result['physics_started'])
            self.assertFalse(result['model_called'])
            failed = {c['name'] for c in result['checks'] if not c['ok']}
            self.assertTrue({'host', 'gpu', 'simulator_interpreter', 'operator_login'} <= failed)

    def test_yam_runtime_does_not_require_simulator_or_gpu(self):
        calls = []

        def fake_command(args, timeout=30):
            calls.append(args)
            return 'runtime-ok'

        with patch.object(doctor, 'verify_pins'), \
             patch.object(doctor.platform, 'system', return_value='Linux'), \
             patch.object(doctor.platform, 'machine', return_value='x86_64'), \
             patch.object(doctor.importlib.metadata, 'version', return_value='1.0'), \
             patch.object(doctor, 'command', side_effect=fake_command):
            result = doctor.inspect_yam_runtime(ROOT, model=False)

        self.assertTrue(result['ready'])
        self.assertTrue(result['physical_execution_supported'])
        self.assertFalse(result['physics_started'])
        self.assertFalse(result['robot_motion_started'])
        self.assertFalse(result['station_checked'])
        self.assertFalse({'gpu', 'simulator_interpreter', 'native_source_and_assets'} &
                         {check['name'] for check in result['checks']})
        self.assertFalse(any(args[0] == 'nvidia-smi' for args in calls))

    def test_yam_runtime_rejects_unsupported_host_without_claiming_readiness(self):
        with patch.object(doctor, 'verify_pins'), \
             patch.object(doctor.platform, 'system', return_value='Windows'), \
             patch.object(doctor.platform, 'machine', return_value='AMD64'), \
             patch.object(doctor.importlib.metadata, 'version', return_value='1.0'), \
             patch.object(doctor, 'command', return_value='runtime-ok'):
            result = doctor.inspect_yam_runtime(ROOT, model=False)
        self.assertFalse(result['ready'])
        self.assertFalse(result['physical_execution_supported'])
        self.assertFalse(result['robot_motion_started'])

    def test_service_access_has_one_bearer_prefix_and_no_url_secret(self):
        for access in ['private-service-token', 'Bearer private-service-token']:
            client = polling.Client('https://example.com', 'x' * 32, 'worker-1', access)
            class Response:
                def __enter__(self):
                    import io
                    return io.StringIO(json.dumps({'ok': True}))
                def __exit__(self, *_):
                    pass
            requests = []
            def send(request, **_):
                requests.append(request)
                return Response()
            client.open = send
            client.post('probe', {})
            request = requests[0]
            self.assertEqual(request.get_header('Oai-sites-authorization'), 'Bearer private-service-token')
            self.assertEqual(request.full_url, 'https://example.com/api/worker/probe')


if __name__ == '__main__':
    unittest.main()
