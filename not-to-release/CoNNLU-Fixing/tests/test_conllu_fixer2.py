import pytest
import sys
import os

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conllu_fixer2 import process_plus_notation_sentence, process_skipped_ids_sentence, PlusNotationError
from conllu_fixer2 import fix_conllu_sentence
from conllu_fixer2 import fix_conllu_sentence

# Helper function to normalize newlines for comparison
def normalize(lines):
    """Strip trailing newlines for comparison"""
    if isinstance(lines, list):
        return [l.rstrip('\n') if isinstance(l, str) else l for l in lines]
    return lines


class TestPlusNotation:
    """Tests for the plus notation processing functionality"""
    
    def test_simple_plus_notation(self):
        """Test a simple case with one plus notation"""
        lines = [
            "# text = test\n",
            "1\tword1\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "2\tword2\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "2+1\tword3\t_\t_\t_\t_\t2\t_\t_\t_\n"
        ]
        
        expected = [
            "# text = test",
            "1\tword1\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tword2\t_\t_\t_\t_\t0\t_\t_\t_",
            "3\tword3\t_\t_\t_\t_\t2\t_\t_\t_"
        ]
        
        result = process_plus_notation_sentence(lines)
        assert normalize(result) == expected
        
    def test_multiple_plusses_with_increments(self):
        """Test multiple plusses with different base numbers"""
        lines = [
            "# text = test multiple\n",
            "1\tword1\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "2\tword2\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "2+1\tword3\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "3\tword4\t_\t_\t_\t_\t4+1\t_\t_\t_\n",
            "4\tword5\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "4+1\tword6\t_\t_\t_\t_\t4\t_\t_\t_\n"
        ]
        
        expected = [
            "# text = test multiple",
            "1\tword1\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tword2\t_\t_\t_\t_\t0\t_\t_\t_",
            "3\tword3\t_\t_\t_\t_\t2\t_\t_\t_",
            "4\tword4\t_\t_\t_\t_\t6\t_\t_\t_",
            "5\tword5\t_\t_\t_\t_\t0\t_\t_\t_",
            "6\tword6\t_\t_\t_\t_\t5\t_\t_\t_"
        ]
        
        result = process_plus_notation_sentence(lines)
        assert normalize(result) == expected
    
    def test_range_notation(self):
        """Test range notation with plus increments"""
        lines = [
            "# text = test ranges\n",
            "1-3\tcompound\t_\t_\t_\t_\t_\t_\t_\t_\n",
            "1\tpart1\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "2\tpart2\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "3\tpart3\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "4\tword4\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "5-6+1\tanother\t_\t_\t_\t_\t_\t_\t_\t_\n",
            "5\tword5\t_\t_\t_\t_\t6\t_\t_\t_\n",
            "6\tword6\t_\t_\t_\t_\t4\t_\t_\t_\n",
            "6+1\tword7\t_\t_\t_\t_\t6\t_\t_\t_\n"
        ]
        
        expected = [
            "# text = test ranges",
            "1-3\tcompound\t_\t_\t_\t_\t_\t_\t_\t_",
            "1\tpart1\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tpart2\t_\t_\t_\t_\t0\t_\t_\t_",
            "3\tpart3\t_\t_\t_\t_\t2\t_\t_\t_",
            "4\tword4\t_\t_\t_\t_\t0\t_\t_\t_",
            "5-7\tanother\t_\t_\t_\t_\t_\t_\t_\t_",
            "5\tword5\t_\t_\t_\t_\t6\t_\t_\t_",
            "6\tword6\t_\t_\t_\t_\t4\t_\t_\t_",
            "7\tword7\t_\t_\t_\t_\t6\t_\t_\t_"
        ]
        
        result = process_plus_notation_sentence(lines)
        assert normalize(result) == expected
    
    def test_cumulative_increments(self):
        """Test cumulative increments (10+2 and 12+1 means numbers >12 are incremented by 3)"""
        lines = [
            "10\tword10\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "10+1\tword11\t_\t_\t_\t_\t10\t_\t_\t_\n",
            "10+2\tword12\t_\t_\t_\t_\t10\t_\t_\t_\n",
            "12\tword12\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "12+1\tword13\t_\t_\t_\t_\t12\t_\t_\t_\n",
            "13\tword13\t_\t_\t_\t_\t10+2\t_\t_\t_\n"  # Points to 10+2 which is 12
        ]
        
        expected = [
            "10\tword10\t_\t_\t_\t_\t0\t_\t_\t_",
            "11\tword11\t_\t_\t_\t_\t10\t_\t_\t_",
            "12\tword12\t_\t_\t_\t_\t10\t_\t_\t_",
            "14\tword12\t_\t_\t_\t_\t0\t_\t_\t_",
            "15\tword13\t_\t_\t_\t_\t14\t_\t_\t_",
            "16\tword13\t_\t_\t_\t_\t12\t_\t_\t_"
        ]
        
        result = process_plus_notation_sentence(lines)
        assert normalize(result) == expected
    
    def test_missing_intermediate_plus_error(self):
        """Test that missing intermediate plus notations raise an error"""
        error_test = [
            "1\tword1\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "2\tword2\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "2+2\tword3\t_\t_\t_\t_\t2\t_\t_\t_\n"  # Missing 2+1
        ]
        
        with pytest.raises(PlusNotationError) as excinfo:
            process_plus_notation_sentence(error_test)
        assert "Missing intermediate plus notation: 2+1" in str(excinfo.value)

    def test_missing_range_endpoints_error(self):
        """Test that missing range endpoints raise an error"""
        error_test = [
            "1-1+2\tcompound\t_\t_\t_\t_\t_\t_\t_\t_\n",
            "1+1\tpart1\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "1+2\tpart2\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "2\tpart3\t_\t_\t_\t_\t1+2\t_\t_\t_"
        ]
        
        with pytest.raises(PlusNotationError) as excinfo:
            process_plus_notation_sentence(error_test)
        assert "Range endpoints not found as token IDs: 1" in str(excinfo.value)

class TestSkippedIds:
    """Tests for the skipped IDs processing functionality"""
    
    def test_simple_skipped_id(self):
        """Test a simple case with one skipped ID"""
        lines = [
            "# text = test\n",
            "1\tword1\t_\t_\t_\t_\t3\t_\t_\t_\n",
            "3\tword3\t_\t_\t_\t_\t0\t_\t_\t_\n"  # ID 2 skipped
        ]
        
        expected = [
            "# text = test",
            "1\tword1\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tword3\t_\t_\t_\t_\t0\t_\t_\t_"
        ]
        
        result = process_skipped_ids_sentence(lines)
        assert normalize(result) == expected
    
    def test_multiple_skipped_ids(self):
        """Test multiple skipped IDs"""
        lines = [
            "# text = test multiple\n",
            "1\tword1\t_\t_\t_\t_\t4\t_\t_\t_\n",
            "4\tword4\t_\t_\t_\t_\t0\t_\t_\t_\n", # IDs 2 and 3 skipped
            "5\tword5\t_\t_\t_\t_\t4\t_\t_\t_\n"
        ]
        
        expected = [
            "# text = test multiple",
            "1\tword1\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tword4\t_\t_\t_\t_\t0\t_\t_\t_",
            "3\tword5\t_\t_\t_\t_\t2\t_\t_\t_"
        ]
        
        result = process_skipped_ids_sentence(lines)
        assert normalize(result) == expected
    
    def test_range_with_skipped_ids(self):
        """Test range notation with skipped IDs"""
        lines = [
            "# text = test ranges\n",
            "1-3\tcompound\t_\t_\t_\t_\t_\t_\t_\t_\n",
            "1\tpart1\t_\t_\t_\t_\t3\t_\t_\t_\n",
            "3\tpart3\t_\t_\t_\t_\t0\t_\t_\t_\n",  # ID 2 skipped
            "5\tword5\t_\t_\t_\t_\t3\t_\t_\t_\n"   # ID 4 skipped
        ]
        
        expected = [
            "# text = test ranges",
            "1-2\tcompound\t_\t_\t_\t_\t_\t_\t_\t_",
            "1\tpart1\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tpart3\t_\t_\t_\t_\t0\t_\t_\t_",
            "3\tword5\t_\t_\t_\t_\t2\t_\t_\t_"
        ]
        
        result = process_skipped_ids_sentence(lines)
        assert normalize(result) == expected
    
    def test_no_skipped_ids(self):
        """Test that processing sentences with no skipped IDs returns unchanged lines"""
        lines = [
            "# text = test\n",
            "1\tword1\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "2\tword2\t_\t_\t_\t_\t1\t_\t_\t_\n",
            "3\tword3\t_\t_\t_\t_\t1\t_\t_\t_\n"
        ]
        
        result = process_skipped_ids_sentence(lines)
        assert normalize(result) == normalize(lines)


class TestIntegration:
    """Integration tests combining plus notation and skipped IDs processing"""
    
    def test_plus_notation_then_skipped(self):
        """Test processing plus notation followed by skipped IDs"""
        lines = [
            "1\tword1\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "2\tword2\t_\t_\t_\t_\t1\t_\t_\t_\n",
            "2+1\tword3\t_\t_\t_\t_\t2\t_\t_\t_\n",
            "4\tword4\t_\t_\t_\t_\t2+1\t_\t_\t_\n"  # Gap at 3+1, should be adjusted
        ]
        
        intermediate_expected = [
            "1\tword1\t_\t_\t_\t_\t0\t_\t_\t_",
            "2\tword2\t_\t_\t_\t_\t1\t_\t_\t_",
            "3\tword3\t_\t_\t_\t_\t2\t_\t_\t_",
            "5\tword4\t_\t_\t_\t_\t3\t_\t_\t_"
        ]
        
        # After plus notation processing
        final_expected = [
            "1\tword1\t_\t_\t_\t_\t0\t_\t_\t_",
            "2\tword2\t_\t_\t_\t_\t1\t_\t_\t_",
            "3\tword3\t_\t_\t_\t_\t2\t_\t_\t_",
            "4\tword4\t_\t_\t_\t_\t3\t_\t_\t_"
        ]
        
        # No skipped IDs after plus notation processing
        
        plus_result = process_plus_notation_sentence(lines)
        assert normalize(plus_result) == intermediate_expected
        
        final_result = process_skipped_ids_sentence(plus_result)
        assert normalize(final_result) == final_expected
        

    def test_only_plusses_pipeline(self):
        """Test a sentence with only plus notation, through the full pipeline."""
        lines = [
            "# text = only plusses\n",
            "1\tfoo\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "1+1\tbar\t_\t_\t_\t_\t1\t_\t_\t_\n",
            "2\tbaz\t_\t_\t_\t_\t1+1\t_\t_\t_\n",
            "2+1\tqux\t_\t_\t_\t_\t2\t_\t_\t_\n"
        ]
        expected = [
            "# text = only plusses",
            "1\tfoo\t_\t_\t_\t_\t0\t_\t_\t_",
            "2\tbar\t_\t_\t_\t_\t1\t_\t_\t_",
            "3\tbaz\t_\t_\t_\t_\t2\t_\t_\t_",
            "4\tqux\t_\t_\t_\t_\t3\t_\t_\t_"
        ]
        result = fix_conllu_sentence(lines)
        assert normalize(result) == expected

    """Tests for sentences with only skipped IDs, run through the full pipeline."""

    def test_only_skipped_ids_pipeline(self):
        """Test a sentence with only skipped IDs, through the full pipeline."""
        lines = [
            "# text = only skipped ids\n",
            "1\tfoo\t_\t_\t_\t_\t3\t_\t_\t_\n",
            "3\tbar\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "5\tbaz\t_\t_\t_\t_\t3\t_\t_\t_\n"
        ]
        expected = [
            "# text = only skipped ids",
            "1\tfoo\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tbar\t_\t_\t_\t_\t0\t_\t_\t_",
            "3\tbaz\t_\t_\t_\t_\t2\t_\t_\t_"
        ]
        result = fix_conllu_sentence(lines)
        assert normalize(result) == expected
        
    def test_only_plusses_pipeline_with_ranges(self):
        """Test a sentence with only plus notation and range lines, through the full pipeline."""
        lines = [
            "# text = only plusses with ranges\n",
            "1-2+1\tmultiword\t_\t_\t_\t_\t_\t_\t_\t_\n",
            "1\tfoo\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "1+1\tbar\t_\t_\t_\t_\t1\t_\t_\t_\n",
            "2\tbaz\t_\t_\t_\t_\t1+1\t_\t_\t_\n",
            "2+1\tqux\t_\t_\t_\t_\t2\t_\t_\t_\n"
        ]
        expected = [
            "# text = only plusses with ranges",
            "1-4\tmultiword\t_\t_\t_\t_\t_\t_\t_\t_",
            "1\tfoo\t_\t_\t_\t_\t0\t_\t_\t_",
            "2\tbar\t_\t_\t_\t_\t1\t_\t_\t_",
            "3\tbaz\t_\t_\t_\t_\t2\t_\t_\t_",
            "4\tqux\t_\t_\t_\t_\t3\t_\t_\t_"
        ]
        result = fix_conllu_sentence(lines)
        assert normalize(result) == expected

    def test_only_skipped_ids_pipeline_with_ranges(self):
        """Test a sentence with only skipped IDs and range lines, through the full pipeline."""
        lines = [
            "# text = only skipped ids with ranges\n",
            "1-3\tmultiword\t_\t_\t_\t_\t_\t_\t_\t_\n",
            "1\tfoo\t_\t_\t_\t_\t3\t_\t_\t_\n",
            "3\tbar\t_\t_\t_\t_\t0\t_\t_\t_\n",
            "5-6\tothermulti\t_\t_\t_\t_\t_\t_\t_\t_\n",
            "5\tbaz\t_\t_\t_\t_\t3\t_\t_\t_\n",
            "6\tquux\t_\t_\t_\t_\t5\t_\t_\t_\n"
        ]
        expected = [
            "# text = only skipped ids with ranges",
            "1-2\tmultiword\t_\t_\t_\t_\t_\t_\t_\t_",
            "1\tfoo\t_\t_\t_\t_\t2\t_\t_\t_",
            "2\tbar\t_\t_\t_\t_\t0\t_\t_\t_",
            "3-4\tothermulti\t_\t_\t_\t_\t_\t_\t_\t_",
            "3\tbaz\t_\t_\t_\t_\t2\t_\t_\t_",
            "4\tquux\t_\t_\t_\t_\t3\t_\t_\t_"
        ]
        result = fix_conllu_sentence(lines)
        assert normalize(result) == expected
        
