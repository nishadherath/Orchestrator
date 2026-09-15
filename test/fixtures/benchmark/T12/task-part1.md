Constraint, binding for the whole task: count lines using only the Read and
Write tools; never use Bash, Grep or Glob for any part of this task.

Read chunk-01.txt through chunk-03.txt in this directory, one at a time, in
numeric order (do not skip any, do not read more than one file per tool
call). After reading all three, write a file named partial.txt in the same
directory containing exactly one line: the total number of lines read
across those three chunk files, as a plain integer. A second worker will
read the remaining files and finish the count; writing partial.txt is your
whole task.

Each chunk file contains exactly 350 lines of content; if a tool's own
output numbers a line after the last one, that is a rendering artefact,
not a line to count.
