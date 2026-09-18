# Make the built package work in a clean consumer

The package works from its source checkout but only files listed in `files` are
published. Make its declared CommonJS entry point self-contained. Change only
`package.json` and `dist/index.cjs`.
