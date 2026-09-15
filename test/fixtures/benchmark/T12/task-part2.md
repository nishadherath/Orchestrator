Constraint, binding for the whole task: count lines using only the Read and
Write tools; never use Bash, Grep or Glob for any part of this task.

A previous worker already read chunk-01.txt through chunk-03.txt in this
directory and recorded its line count: {subtotal}.

Read chunk-04.txt and chunk-05.txt in this directory, one at a time, in
numeric order (do not skip either, do not read more than one file per tool
call). After reading both, write a file named summary.txt in the same
directory containing exactly one line: the total number of lines read
across all five chunk files (the previous worker's count plus the two you
just read), as a plain integer.

Each chunk file contains exactly 350 lines of content; if a tool's own
output numbers a line after the last one, that is a rendering artefact,
not a line to count.
