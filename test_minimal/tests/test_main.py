import unittest
import sys
from pathlib import Path

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import hello


class TestHello(unittest.TestCase):
    def test_hello(self):
        """Test that hello() returns exactly 'Hello, World!'"""
        self.assertEqual(hello(), "Hello, World!")


if __name__ == "__main__":
    unittest.main()