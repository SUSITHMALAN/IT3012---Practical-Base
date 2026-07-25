import unittest

from visual_grid_game import VisualGridHuntGame


class TestVisualGridHuntGameTraps(unittest.TestCase):
    def test_toxic_traps_are_generated_safely(self):
        env = VisualGridHuntGame(width=8, height=8, num_food=4, num_opponents=0)

        self.assertTrue(hasattr(env, 'toxic_traps'))
        self.assertIsInstance(env.toxic_traps, set)

        for trap in env.toxic_traps:
            self.assertIsInstance(trap, tuple)
            self.assertEqual(len(trap), 2)
            self.assertNotEqual(trap, (0, 0))
            self.assertGreaterEqual(trap[0], 0)
            self.assertGreaterEqual(trap[1], 0)
            self.assertLess(trap[0], env.width)
            self.assertLess(trap[1], env.height)
            self.assertNotIn(trap, env.walls)
            self.assertNotIn(trap, env.food_positions)


if __name__ == '__main__':
    unittest.main()
