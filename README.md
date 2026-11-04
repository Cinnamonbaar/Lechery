# Lechery

An isekai transformation RPG, text first, made to be played on a phone.

## Size budget

The whole game stays under **10 KB gzipped**. CI fails if it goes over.
The limit can be raised — but only if we both truly, wholeheartedly agree.
See `CLAUDE.md`.

## Running

```sh
npm install
npm run dev      # local server
npm test         # unit tests
npm run build    # type-check and build into dist/
npm run size     # measure against the budget
npm run smoke    # play it in a real browser, writing screenshots
```
