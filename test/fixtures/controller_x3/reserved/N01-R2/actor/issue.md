# Regenerate the wire header from its source schema

The source schema now defines version 3 and a trace identifier. The checked-in
C header and its generator still reflect version 2. Make the generator render
the schema it receives, regenerate the header from the current source, and
preserve the request identifier. A changed schema must produce a changed
header without a manual patch. Leave the JSON adapter and public check intact.
Report observed behaviour and a next check in report.json.
