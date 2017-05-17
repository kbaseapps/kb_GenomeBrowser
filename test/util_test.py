import unittest

from GenomeBrowser.util import (
    check_reference,
    check_reference_type
)

class GBUtilTest(unittest.TestCase):
    def test_check_ref(self):
        good_refs = [
            '11/22/33', '11/22', '11/22/33;44/55', '11/22;44/55', '11/22;44/55/66'
        ]
        bad_refs = [
            'not_a_ref', '1', '11/', '11/22/', '11/22;'
        ]
        for ref in good_refs:
            self.assertTrue(check_reference(ref))
        for ref in bad_refs:
            self.assertFalse(check_reference(ref))

    def test_check_ref_type(self):
        pass
