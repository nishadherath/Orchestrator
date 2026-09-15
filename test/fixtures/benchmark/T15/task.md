Read chunk-01.txt through chunk-12.txt in this directory, one at a time, in
numeric order (do not skip any, do not read more than one file per tool
call). After reading all twelve, write a file named summary.txt in the same
directory containing exactly one line: the total number of lines read
across all twelve chunk files, as a plain integer.

Each chunk file contains exactly 350 lines of content; if a tool's own
output numbers a line after the last one, that is a rendering artefact,
not a line to count.
