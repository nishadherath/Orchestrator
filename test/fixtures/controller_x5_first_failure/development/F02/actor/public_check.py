"""Public styled-width checks for the Click F02 development case."""

import unittest

from click.formatting import HelpFormatter, wrap_text


class StyledWidthTests(unittest.TestCase):
    def test_styled_word_wraps_by_visible_width(self):
        text = "\x1b[31mred\x1b[0m blue green"
        self.assertEqual("\x1b[31mred\x1b[0m blue\ngreen",
                         wrap_text(text, width=8))

    def test_styled_indent_uses_visible_width(self):
        indent = "\x1b[32m>\x1b[0m "
        self.assertEqual(f"{indent}alpha\n{indent}beta\n{indent}gamma",
                         wrap_text("alpha beta gamma", width=10,
                                   initial_indent=indent,
                                   subsequent_indent=indent))

    def test_styled_usage_keeps_short_prefix_on_first_line(self):
        formatter = HelpFormatter(width=35)
        formatter.write_usage("\x1b[35mtool\x1b[0m", "[OPTIONS] FILE [EXTRA]")
        self.assertEqual("Usage: \x1b[35mtool\x1b[0m [OPTIONS] FILE [EXTRA]\n",
                         formatter.getvalue())


if __name__ == "__main__":
    unittest.main()
