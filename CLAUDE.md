# Lechery — working rules

## The size budget

The shipped game must stay **under 10 KB, gzip-compressed** — the total of
every file in the build, measured the way a phone downloads it.

`npm run size` measures it, and CI fails the build if it is over.

**The limit may be raised, but only if both of us — the project owner and
Claude — truly, wholeheartedly agree to it.** Not because a feature would be
easier with more room, not quietly, and never by editing the check to pass.
If a change does not fit, the default answer is to make it smaller. If it
truly cannot be made smaller, stop and make the case to the owner, and
raise the limit only after a clear yes.

## The goal

Something easy to play on a phone, that is fun. Every decision answers to
that: tap-driven, no precise input, text first, pixel art where pictures
help, and a first five minutes — intro and character creation — that feels
good enough to linger in.

## Privacy

Never commit personal information: no real names, email addresses, local
paths, tokens or keys. Commit as the GitHub noreply identity.

## References before invention

Look for real references and templates before designing something from
scratch — art technique, UI conventions, writing, game design. Established
practice usually beats a first guess, and it is cheaper to borrow a proven
answer than to rediscover it. Say which reference a decision came from.
