import pytest
import unittest

import paml_convert


class TestLocationUtilities(unittest.TestCase):
    @pytest.mark.skip(reason="module 'paml_convert' has no submodule 'markdown'")
    def test_range_reduction(self):
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1'}) == {'A1'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1', 'A2'}) == {'A1:A2'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A2', 'A4', 'A1', 'A5', 'A3'}) == {'A1:A5'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A2:B3', 'A4:D6', 'C2:D2', 'C3', 'D3'}) == {'A2:D6'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1:C3', 'D1:F3', 'A4:C7'}) == {'A1:F3', 'A4:C7'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1:C3', 'D1:F3', 'A4:C7', 'D4:F7'}) == {'A1:F7'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1:C3', 'D1:F3', 'A4:C7', 'D4:D7'}) == {'A1:F3', 'A4:D7'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1:C3', 'A4:C7'}) == {'A1:C7'}
        assert paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1:C3', 'D4:F7'}) == {'A1:C3', 'D4:F7'}
        with pytest.raises(AssertionError):
            paml_convert.markdown.protocol_to_markdown.reduce_range_set({'A1:C3', 'B3:F7'}) # overlapping ranges not allowed
        with pytest.raises(AssertionError):
            paml_convert.markdown.protocol_to_markdown.reduce_range_set({}) # must have at least one range

if __name__ == '__main__':
    unittest.main()
