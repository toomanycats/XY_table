import unittest

class TestMotorMethods(unittest.TestCase):

    def setUp(self):
        self.seq = [1,2,3,4]

    def test_move_relative(self):
        pass

    def test_test(self):
        element = 2
        self.assertTrue(element in self.seq)


if __name__ == '__main__':
    unittest.main()
