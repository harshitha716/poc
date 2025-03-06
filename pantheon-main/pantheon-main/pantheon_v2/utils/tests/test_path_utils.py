from pantheon_v2.utils.path_utils import sanitize_filename
import os


class TestPathUtils:
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization"""
        test_cases = [
            {"input": "test.txt", "expected": "test_transformed.txt"},
            {"input": "simple_file.pdf", "expected": "simple_file_transformed.pdf"},
            {"input": "document.docx", "expected": "document_transformed.docx"},
        ]

        for test_case in test_cases:
            input_filename = test_case["input"]
            extension = os.path.splitext(input_filename)[1]
            result = sanitize_filename(input_filename, extension)
            assert result == test_case["expected"]

    def test_sanitize_filename_special_chars(self):
        """Test sanitization of filenames with special characters"""
        test_cases = [
            {"input": "test!@#$%^&*.txt", "expected": "test_transformed.txt"},
            {
                "input": "file(with)special{chars}.pdf",
                "expected": "file_with_special_chars_transformed.pdf",
            },
            {
                "input": "doc~!@#$%^&*()_+-=[]{}|;:,.<>?.docx",
                "expected": "doc_transformed.docx",
            },
        ]

        for test_case in test_cases:
            input_filename = test_case["input"]
            extension = os.path.splitext(input_filename)[1]
            result = sanitize_filename(input_filename, extension)
            assert result == test_case["expected"]

    def test_sanitize_filename_spaces(self):
        """Test sanitization of filenames with spaces"""
        test_cases = [
            {"input": "my file.txt", "expected": "my_file_transformed.txt"},
            {
                "input": "document with spaces.pdf",
                "expected": "document_with_spaces_transformed.pdf",
            },
            {
                "input": "  leading trailing spaces  .docx",
                "expected": "leading_trailing_spaces_transformed.docx",
            },
        ]

        for test_case in test_cases:
            input_filename = test_case["input"]
            extension = os.path.splitext(input_filename)[1]
            result = sanitize_filename(input_filename, extension)
            assert result == test_case["expected"]

    def test_sanitize_filename_consecutive_special_chars(self):
        """Test sanitization of filenames with consecutive special characters"""
        test_cases = [
            {"input": "test!!!file###.txt", "expected": "test_file_transformed.txt"},
            {
                "input": "multiple___underscores.pdf",
                "expected": "multiple_underscores_transformed.pdf",
            },
            {
                "input": "consecutive   spaces.docx",
                "expected": "consecutive_spaces_transformed.docx",
            },
        ]

        for test_case in test_cases:
            input_filename = test_case["input"]
            extension = os.path.splitext(input_filename)[1]
            result = sanitize_filename(input_filename, extension)
            assert result == test_case["expected"]

    def test_sanitize_filename_leading_trailing_special_chars(self):
        """Test sanitization of filenames with leading/trailing special characters"""
        test_cases = [
            {
                "input": "_leading_underscore.txt",
                "expected": "leading_underscore_transformed.txt",
            },
            {
                "input": "trailing_underscore_.pdf",
                "expected": "trailing_underscore_transformed.pdf",
            },
            {"input": "__both_sides__.docx", "expected": "both_sides_transformed.docx"},
        ]

        for test_case in test_cases:
            input_filename = test_case["input"]
            extension = os.path.splitext(input_filename)[1]
            result = sanitize_filename(input_filename, extension)
            assert result == test_case["expected"]

    def test_sanitize_filename_mixed_case(self):
        """Test sanitization of filenames with mixed case"""
        test_cases = [
            {"input": "MixedCase.txt", "expected": "MixedCase_transformed.txt"},
            {"input": "UPPERCASE.pdf", "expected": "UPPERCASE_transformed.pdf"},
            {"input": "lowercase.docx", "expected": "lowercase_transformed.docx"},
            {
                "input": "Mixed_CASE_file.txt",
                "expected": "Mixed_CASE_file_transformed.txt",
            },
        ]

        for test_case in test_cases:
            input_filename = test_case["input"]
            extension = os.path.splitext(input_filename)[1]
            result = sanitize_filename(input_filename, extension)
            assert result == test_case["expected"]

    def test_sanitize_filename_numbers(self):
        """Test sanitization of filenames with numbers"""
        test_cases = [
            {"input": "file123.txt", "expected": "file123_transformed.txt"},
            {
                "input": "123_start_with_number.pdf",
                "expected": "123_start_with_number_transformed.pdf",
            },
            {
                "input": "end_with_numbers_456.docx",
                "expected": "end_with_numbers_456_transformed.docx",
            },
            {
                "input": "mix3d_numb3rs_1n_f1l3.txt",
                "expected": "mix3d_numb3rs_1n_f1l3_transformed.txt",
            },
        ]

        for test_case in test_cases:
            input_filename = test_case["input"]
            extension = os.path.splitext(input_filename)[1]
            result = sanitize_filename(input_filename, extension)
            assert result == test_case["expected"]
