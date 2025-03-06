import unittest
import pandas as pd
from pantheon_v2.tools.common.pandas.helpers.island_detection import (
    _merge_wrapped_rows,
    detect_tables_and_metadata,
    transform_float,
    find_true_header,
    merge_tables,
    merge_metadata,
)


class TestIslandDetection(unittest.TestCase):
    def test_merge_wrapped_rows(self):
        # Test case 1: Basic row merging
        data1 = [
            ["Balance", "", "", ""],
            ["", "100", "200", "300"],
        ]
        df1 = pd.DataFrame(data1)
        result1 = _merge_wrapped_rows(df1)
        expected1 = pd.DataFrame([["Balance", "100", "200", "300"]])
        pd.testing.assert_frame_equal(result1, expected1)

        # Test case 2: No merging needed
        data2 = [["A", "B", "C", "D"], ["1", "2", "3", "4"]]
        df2 = pd.DataFrame(data2)
        result2 = _merge_wrapped_rows(df2)
        pd.testing.assert_frame_equal(result2, df2)

        # Test case 3: Conflict case - should not merge
        data3 = [
            ["Header", "Value", "", ""],
            ["Header", "Different", "Extra", ""],
        ]
        df3 = pd.DataFrame(data3)
        result3 = _merge_wrapped_rows(df3)
        pd.testing.assert_frame_equal(result3, df3)

    def test_transform_float(self):
        # Test valid float inputs
        self.assertEqual(transform_float("123.45"), 123.45)
        self.assertEqual(
            transform_float("-123.45"), 123.45
        )  # Should return absolute value
        self.assertEqual(transform_float("$123.45"), 123.45)
        self.assertEqual(transform_float("123"), 123.0)

        # Test invalid inputs
        self.assertEqual(transform_float("abc"), "")
        self.assertEqual(transform_float(""), "")
        self.assertEqual(transform_float("12.34.56"), "")  # Multiple decimal points
        self.assertEqual(
            transform_float("12 45"), ""
        )  # Multiple numbers separated by spaces

    def test_find_true_header(self):
        # Test case 1: Clear header followed by numeric data
        data1 = [
            ["Column1", "Column2", "Column3"],
            ["100", "200", "300"],
            ["400", "500", "600"],
        ]
        df1 = pd.DataFrame(data1)
        header_idx1, cleaned_df1 = find_true_header(df1)
        self.assertIsNone(header_idx1)  # All rows contain numbers, so no clear header
        pd.testing.assert_frame_equal(cleaned_df1, df1)

        # Test case 2: No clear header (all numeric)
        data2 = [["100", "200", "300"], ["400", "500", "600"]]
        df2 = pd.DataFrame(data2)
        header_idx2, cleaned_df2 = find_true_header(df2)
        self.assertIsNone(header_idx2)
        pd.testing.assert_frame_equal(cleaned_df2, df2)

        # Test case 3: Empty rows before header
        data3 = [
            ["Fake Header", "Fake Header", "Fake Header"],
            ["Column1", "Column2", "Column3"],
            ["100", "200", "300"],
        ]
        df3 = pd.DataFrame(data3)
        header_idx3, cleaned_df3 = find_true_header(df3)

        self.assertEqual(header_idx3, 0)
        self.assertEqual(len(cleaned_df3), 3)

        # Test case 4: Empty DataFrame
        with self.assertRaises(ValueError) as context:
            find_true_header(pd.DataFrame())
        self.assertEqual(str(context.exception), "Input DataFrame is empty")

    def test_merge_tables(self):
        # Test case 1: Matching tables
        data1 = [
            ["Column1", "Column2", "Column3"],
            ["100", "200", "300"],
            ["400", "500", "600"],
        ]
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data1)
        result1 = merge_tables([df1, df2])
        expected1_data = [
            ["Column1", "Column2", "Column3"],
            ["100", "200", "300"],
            ["400", "500", "600"],
            ["100", "200", "300"],
            ["400", "500", "600"],
        ]
        expected1 = pd.DataFrame(expected1_data)
        pd.testing.assert_frame_equal(result1, expected1)

        # Test case 2: Single table
        result2 = merge_tables([df1])
        pd.testing.assert_frame_equal(result2, df1)

        # Test case 3: Empty list
        result3 = merge_tables([])
        self.assertTrue(result3.empty)

        # Test case 4: Non-matching tables
        df3 = pd.DataFrame({"C": [1, 2], "D": [3, 4]})
        result4 = merge_tables([df1, df3])
        pd.testing.assert_frame_equal(result4, df1)

    def test_merge_metadata(self):
        # Test case 1: Basic metadata merging
        meta1 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        meta2 = pd.DataFrame({"A": [5, 6], "B": [7, 8]})
        result1 = merge_metadata([meta1, meta2])
        expected1 = pd.DataFrame({"A": [1, 2, 5, 6], "B": [3, 4, 7, 8]})
        pd.testing.assert_frame_equal(result1, expected1)

        # Test case 2: Duplicate rows
        meta3 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        meta4 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result2 = merge_metadata([meta3, meta4])
        pd.testing.assert_frame_equal(result2, meta3)

        # Test case 3: Empty metadata
        result3 = merge_metadata([])
        self.assertTrue(result3.empty)

        # Test case 4: Single metadata
        result4 = merge_metadata([meta1])
        pd.testing.assert_frame_equal(result4, meta1)

    def test_detect_tables_and_metadata(self):
        # Test case 1: Simple table with metadata
        data1 = [
            ["Report Date:", "2023-01-01", "", ""],
            ["Company:", "Test Corp", "", ""],
            ["", "", "", ""],
            ["Column1", "Column2", "Column3", "Column4"],
            ["100", "200", "300", "400"],
            ["500", "600", "700", "800"],
        ]
        df1 = pd.DataFrame(data1)
        table_df1, metadata_df1 = detect_tables_and_metadata(df1)

        self.assertEqual(len(table_df1), 3)  # Header + 2 data rows
        self.assertIsNotNone(metadata_df1)  # Should have metadata
        self.assertEqual(len(metadata_df1), 3)  # 2 metadata rows

        # Test case 2: Table without metadata
        data2 = [
            ["Column1", "Column2", "Column3"],
            ["100", "200", "300"],
            ["400", "500", "600"],
        ]
        df2 = pd.DataFrame(data2)
        table_df2, metadata_df2 = detect_tables_and_metadata(df2)

        self.assertEqual(len(table_df2), 3)
        self.assertIsNone(metadata_df2)

        # Test case 3: Empty DataFrame
        with self.assertRaises(ValueError) as context:
            find_true_header(pd.DataFrame())
        self.assertEqual(str(context.exception), "Input DataFrame is empty")

        # # Test case 4: Multiple tables with metadata
        # data4 = [
        #     ["Report 1:", "2023-01-01", "", ""],
        #     ["Table1", "Col1", "Col2", ""],
        #     ["", "100", "200", ""],
        #     ["", "", "", ""],
        #     ["Report 2:", "2023-01-02", "", ""],
        #     ["Table2", "Col1", "Col2", ""],
        #     ["", "300", "400", ""],
        # ]
        # df4 = pd.DataFrame(data4)
        # table_df4, metadata_df4 = detect_tables_and_metadata(df4)

        # raise ValueError(f"table_df4: {table_df4}, metadata_df4: {metadata_df4}")

        # self.assertTrue(len(table_df4) > 0)
        # self.assertIsNotNone(metadata_df4)  # Should have metadata
        # self.assertTrue(len(metadata_df4) > 0)  # Should have at least one metadata row


if __name__ == "__main__":
    unittest.main()
