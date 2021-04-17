import paml
import pytest
import unittest


class TestLocationUtilities(unittest.TestCase):
    def test_merge_adjacent_coordinates(self):
        # Check correct merges
        assert paml.merge_adjacent_coordinates('A1','A2') == 'A1:A2'
        assert paml.merge_adjacent_coordinates('A2','A1') == 'A1:A2'
        assert paml.merge_adjacent_coordinates('C1:C5','C6') == 'C1:C6'
        assert paml.merge_adjacent_coordinates('D3:G6','D7:G7') == 'D3:G7'
        assert paml.merge_adjacent_coordinates('A2:F4','G2:K4') == 'A2:K4'
        # Check for expected failures
        with pytest.raises(Exception):
            assert paml.merge_adjacent_coordinates('A1','A3') == 'A1:A2'
        with pytest.raises(Exception):
            assert paml.merge_adjacent_coordinates('A2','A2') == 'A1:A2'
        with pytest.raises(Exception):
            assert paml.merge_adjacent_coordinates('C1:C5','D6') == 'C1:C6'
        with pytest.raises(Exception):
            assert paml.merge_adjacent_coordinates('D3:G7','D7:G7') == 'D3:G7'
        with pytest.raises(Exception):
            assert paml.merge_adjacent_coordinates('A2:F4','G3:K4') == 'A2:K4'

    def test_range_reduction(self):
        assert paml.reduce_range_set({}) == {}
        assert paml.reduce_range_set({'A1'}) == {'A1'}
        assert paml.reduce_range_set({'A1','A2'}) == {'A1:A2'}
        assert paml.reduce_range_set({'A2','A4','A1','A5','A3'}) == {'A1:A5'}
        assert paml.reduce_range_set({'A2:B3','A4:D6','C2:D2','C3','D3'}) == {'A2:D6'}


if __name__ == '__main__':
    unittest.main()
