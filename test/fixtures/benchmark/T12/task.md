Constraint, binding for the whole task: count lines using only the Read and
Write tools; never use Bash, Grep or Glob for any part of this task.

Read chunk-01.txt through chunk-05.txt in this directory, one at a time, in
numeric order (do not skip any, do not read more than one file per tool
call). After reading all five, write a file named summary.txt in the same
directory containing exactly one line: the total number of lines read
across all five chunk files, as a plain integer.

Each chunk file contains exactly 350 lines of content; if a tool's own
output numbers a line after the last one, that is a rendering artefact,
not a line to count.
