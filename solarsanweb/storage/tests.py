"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


from .models import Pool
import nose.tools as nt

ZFS_TEST_POOL = 'rpool'
ZFS_TEST_DATASET = ''


class TestPool(object):
    def setup(self):
        self.p = Pool('rpool')

    def test_name(self):
        nt.assert_equal(self.p.name, ZFS_TEST_POOL)

"""
class TestFruit(object):

    def setup(self):
    self.fruit = Fruit()
        self.fruit.set_name("Papaya")
        self.fruit.set_color("orange")

    def test_color(self):
        nt.assert_equal(self.fruit.name, "Papaya")
    nt.assert_equal(self.fruit.color, "orange")

    def test_yumminess(self):
    nt.assert_true(self.fruit.is_yummy())

    def test_color_change(self):
    self.fruit.become_brown()
        nt.assert_equal(self.fruit.color, "brown")

    def teardown(self):
    self.fruit.disappear()
"""
