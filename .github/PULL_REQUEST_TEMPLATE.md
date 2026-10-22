Closes #

## What changed

<!-- Two or three sentences. If it adds a spec element type, say which of the four places it touches: build.py, lint.py, references/spec-format.md, tests. -->

## How it was tested

- [ ] `python3 -m unittest discover -s tests` passes locally (say the count)
- [ ] every example still builds and lints: `for f in ../assets/examples/*.spec.json; do python3 build.py $f /tmp/x.excalidraw && python3 lint.py /tmp/x.excalidraw; done` from `skills/prettier-excalidraw/scripts`
- [ ] new behaviour has a test; new lint rules have a row in `references/style-guide.md`

## Before you open this

- [ ] I commented on the issue (or assigned myself) before starting, so nobody else was working on it
- [ ] this branch is rebased on the latest `main`
- [ ] docs updated where the behaviour is user-visible (`spec-format.md`, `SKILL.md`, README) and a line added under Unreleased in `CHANGELOG.md`
- [ ] scripts stay standard-library only (Python 3.10+)
