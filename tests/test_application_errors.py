import unittest

from b3_selic_pre.application.errors import CommunicationError


class CommunicationErrorTest(unittest.TestCase):
    def test_is_exception_with_message(self):
        error = CommunicationError("falha de rede")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "falha de rede")

    def test_can_be_raised_and_caught(self):
        with self.assertRaises(CommunicationError):
            raise CommunicationError("falha")


if __name__ == "__main__":
    unittest.main()
