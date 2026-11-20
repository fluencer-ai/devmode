# Code-smell baseline (Standards axis)

Pass this list in full to every Standards reviewer. It applies even when the
repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it
  endorses something a smell would flag, suppress the smell.
- **Always a judgement call.** Report a smell as a labelled heuristic ("possible
  Feature Envy") and quote the hunk, never as a hard violation. Skip anything
  tooling already enforces.

Each entry reads *what it is* → *how to fix*. Match it against the diff only.

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal
  what it does or holds. → Rename it; if no honest name comes, the design is
  murky.
- **Duplicated Code**: the same logic shape in more than one hunk or file of the
  change. → Extract the shared shape and call it from both.
- **Feature Envy**: a method that reaches into another object's data more than
  its own. → Move it onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together. →
  Bundle them into one type and pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain
  concept. → Give the concept its own small type (name it in the
  `ubiquitous-language`).
- **Repeated Switches**: the same `switch` or `if` cascade on the same type
  recurs across the change. → Replace with polymorphism, or one map both sites
  share.
- **Shotgun Surgery**: one logical change forces scattered edits across many
  files. → Gather what changes together into one module.
- **Divergent Change**: one file or module edited for several unrelated reasons.
  → Split it so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks for needs the
  spec doesn't have. → Delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't
  depend on. → Hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → Cut
  it and call the real target directly.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most
  of what it inherits. → Drop the inheritance; use composition.
