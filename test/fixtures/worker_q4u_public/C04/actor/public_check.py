"""Public smoke checks for label normalisation."""
from labels import normalise_label


assert normalise_label("  HELLO\tworld  ") == "hello world"
assert normalise_label("Straße") == "strasse"
assert normalise_label("ＡＢＣ") == "abc"
