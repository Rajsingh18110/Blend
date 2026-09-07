import unittest
from unittest.mock import patch
import pathlib
from blend.blend_core.answerers._core import AnswerStorage

class TestAnswerersFrozen(unittest.TestCase):
    def test_load_builtins_frozen_environment(self):
        """
        Test that load_builtins does not crash when pathlib.Path.iterdir() 
        raises FileNotFoundError, simulating a PyInstaller frozen environment 
        where pure Python directories are not extracted to disk.
        """
        storage = AnswerStorage()
        
        # We patch pathlib.Path.iterdir to raise FileNotFoundError
        # Because we guarded the backwards compatibility block with .exists() and .is_dir(),
        # those should also be patched to return False to fully simulate frozen environment.
        with patch.object(pathlib.Path, 'exists', return_value=False), \
             patch.object(pathlib.Path, 'is_dir', return_value=False), \
             patch.object(pathlib.Path, 'iterdir', side_effect=FileNotFoundError("Mocked frozen environment")):
            
            # This should NOT crash
            storage.load_builtins()
            
            # Since pkgutil.iter_modules does not depend on pathlib.Path.iterdir,
            # it should successfully load the built-in answerers
            self.assertGreater(len(storage.answerer_list), 0, "Should have loaded at least one answerer via pkgutil")
            
            # Verify that one of the known built-in answerers is present
            answerer_names = [a.__class__.__name__ for a in storage.answerer_list]
            self.assertTrue(any("Random" in name or "BlendAnswerer" in name or "Statistics" in name for name in answerer_names), 
                            f"Known builtin answerer not found. Found: {answerer_names}")

if __name__ == '__main__':
    unittest.main()
