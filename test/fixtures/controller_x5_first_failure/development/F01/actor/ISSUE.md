# Attribute metadata and validator state regressions

A field transformer that inspects an Attribute's constructor alias now sees
an unset alias for an ordinary private field, even though the generated
constructor later accepts the stripped name. Explicit aliases still reach
the constructor. Keep the metadata seen by the transformer consistent with
the actual constructor, including whether an alias was supplied or generated.

The validator-disabling context also loses the surrounding state. Leaving an
inner disabled context enables validators while the outer context is still
active, and entering it while validation was already disabled enables it on
exit. Preserve the previous state through nesting and exceptions. Keep the
documented global, non-thread-safe API and ordinary validation behaviour.

The local check is `python3 -B public_check.py`. Repair only `attr/_make.py`
and `attr/validators.py`. Do not edit the issue, public check, licence or other
package modules. The evaluation includes inherited fields, transformer-added
fields, explicit aliases and validation state after an exception.
