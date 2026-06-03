import unittest
import asyncio
from modes.fast import FastMode
from modes.deep import DeepMode
from modes.ghost import GhostMode

class TestModes(unittest.IsolatedAsyncioTestCase):

    async def test_fast_mode_initialization(self):
        mode = FastMode()
        self.assertIsNotNone(mode)

    async def test_deep_mode_initialization(self):
        mode = DeepMode(max_depth=1)
        self.assertEqual(mode.max_depth, 1)
        
    async def test_ghost_mode_invalid_url(self):
        mode = GhostMode()
        result = await mode.proxy_url("http://localhost/admin")
        self.assertFalse(result['success'])
        self.assertIn("Security Error", result['content'])

if __name__ == '__main__':
    unittest.main()
