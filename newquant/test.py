import unittest

from .qrange import resolve_qrangespec


class QuantSpecResolverTest(unittest.TestCase):

    def test_tuplequantspec(self):
        """Test tuple-based explicit enumerations."""

        # ordered, non-equally-spaced range
        tuple_ = (1, 2, 3, 5)
        self.assertRaises(ValueError, lambda: resolve_qrangespec(tuple_))  # Why am I using a lambda expression here? See here: https://stackoverflow.com/a/6103930

        # ordered range with step greater than one
        tuple_ = (-4, -2, 0, 2)
        self.assertRaises(ValueError, lambda: resolve_qrangespec(tuple_))

        # ordered special range (-1, 1)
        reference = (-1, 1)
        tuple_ = reference
        qrange = resolve_qrangespec(tuple_)
        self.assertTrue(reference == qrange.range)

        # ordered range with step one
        reference = (1, 2, 3, 4)
        tuple_ = reference
        qrange = resolve_qrangespec(tuple_)
        self.assertTrue(reference == qrange.range)

        # unordered range with step one
        reference = (1, 2, 3, 4)
        tuple_ = (2, 1, 3, 4)
        qrange = resolve_qrangespec(tuple_)
        self.assertTrue(reference == qrange.range)

    def test_dictquantspec(self):
        """Test dictionary-based (compact) specifications."""

        # unsupported key
        dict_ = {'n_levels': 16, 'offset': -2, 'step': 2}
        self.assertRaises(ValueError, lambda: resolve_qrangespec(dict_))

        # ambiguous number of levels specification
        dict_ = {'n_levels': 16, 'bitwidth': 3, 'offset': -2}
        self.assertRaises(ValueError, lambda: resolve_qrangespec(dict_))

        # ambiguous offset specification
        dict_ = {'n_levels': 4, 'offset': -3, 'signed': True}
        self.assertRaises(ValueError, lambda: resolve_qrangespec(dict_))

        # number of levels, offset
        reference = tuple(range(-2, -2 + 16 * 1, 1))
        dict_ = {'n_levels': 16, 'offset': -2}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # number of levels, signedness (sub-range of signed int)
        reference = tuple(range(-8, -8 + 16 * 1, 1))
        dict_ = {'n_levels': 16, 'signed': True}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # number of levels, signedness (sub-range of unsigned int)
        reference = tuple(range(0, 0 + 15 * 1, 1))
        dict_ = {'n_levels': 15, 'signed': False}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # bitwidth, offset
        reference = tuple(range(-10, -10 + (2 ** 4) * 1, 1))
        dict_ = {'bitwidth': 4, 'offset': -10}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # bitwidth, signedness (signed int)
        reference = tuple(range(-2 ** (4 - 1), -2 ** (4 - 1) + (2 ** 4) * 1, 1))
        dict_ = {'bitwidth': 4, 'signed': True}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # bitwidth, signedness (unsigned int)
        reference = tuple(range(0, 0 + (2 ** 4) * 1, 1))
        dict_ = {'bitwidth': 4, 'signed': False}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # limp bitwidth, offset
        reference = tuple(range(5, 5 + ((2 ** 3) - 1) * 1, 1))
        dict_ = {'limpbitwidth': 3, 'offset': 5}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # limp bitwidth, signedness (signed "limp" int)
        reference = tuple(range(-2 ** (3 - 1) + 1, -2 ** (3 - 1) + 1 + ((2 ** 3) - 1) * 1, 1))
        dict_ = {'limpbitwidth': 3, 'signed': True}
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

        # limp bitwidth, signedness (unsigned "limp" int)
        dict_ = {'limpbitwidth': 3, 'signed': False}
        reference = tuple(range(0, 0 + ((2 ** 3) - 1) * 1, 1))
        qrange = resolve_qrangespec(dict_)
        self.assertTrue(reference == qrange.range)

    def test_strquantspec(self):
        """Test the string-based (syntactic sugar) specifications."""

        # binary range
        reference = (-1, 1)
        qrange = resolve_qrangespec('binary')
        self.assertTrue(reference == qrange.range)

        # ternary range
        reference = (-1, 0, 1)
        qrange = resolve_qrangespec('ternary')
        self.assertTrue(reference == qrange.range)

        # non-supported string
        self.assertRaises(ValueError, lambda: resolve_qrangespec('quaternary'))
