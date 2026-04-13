```python
# Function Definition
def reverse_string(s: str) -> str:
    """
    Reverses the given string.

    Args:
        s (str): The input string to be reversed.

    Returns:
        str: The reversed version of the input string.
    """
    return s[::-1]

# Unit Tests
import unittest

class TestReverseString(unittest.TestCase):
    def test_reverse_string(self):
        self.assertEqual(reverse_string("hello"), "olleh")
        self.assertEqual(reverse_string(""), "")
        self.assertEqual(reverse_string("12345"), "54321")
        self.assertEqual(reverse_string("!@#$%"), "%$#@!")
        self.assertEqual(reverse_string("a b c d e"), "e d c b a")

if __name__ == "__main__":
    unittest.main()
```