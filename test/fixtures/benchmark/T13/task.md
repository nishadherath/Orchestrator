Constraint, binding for the whole task: write the total to results/count.txt,
spelled out in words (for example, "one thousand seven hundred fifty"), never
as digits; do not create or write to any file named summary.txt anywhere in
this directory.

Read chunk-01.txt through chunk-05.txt in this directory, one at a time, in
numeric order (do not skip any, do not read more than one file per tool
call). After reading all five, create the results directory if it does not
exist and write results/count.txt containing exactly one line: the total
number of lines read across all five chunk files, spelled out in words as
the constraint above states.

Each chunk file contains exactly 350 lines of content; if a tool's own
output numbers a line after the last one, that is a rendering artefact,
not a line to count.
