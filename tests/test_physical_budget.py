import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('physical_budget',Path(__file__).resolve().parents[1]/'worker-agent/physical_budget.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class PhysicalBudget(unittest.TestCase):
 def test_home_and_startup_do_not_extend_lease(self):
  self.assertEqual(module.native_seconds({'run_started_at':1000,'run_duration_s':180},180,1015),145)
 def test_requested_cap_and_cleanup_reserve(self):
  self.assertEqual(module.native_seconds({'run_started_at':1000,'run_duration_s':600},180,1015),180)
  with self.assertRaises(TimeoutError):module.native_seconds({'run_started_at':1000,'run_duration_s':60},60,1040)
 def test_unknown_lease_is_not_a_new_timer(self):
  for status in ({},{'run_started_at':None,'run_duration_s':180},{'run_started_at':float('nan'),'run_duration_s':180}):
   with self.assertRaises(ValueError):module.native_seconds(status,180,1000)
