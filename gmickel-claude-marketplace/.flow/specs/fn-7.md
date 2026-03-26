# fn-7 TUI: Search overlay

## Overview
`/` opens search overlay for filtering output buffer. Incremental search with match highlighting and n/N navigation.

## Scope
- `/` opens modal overlay
- Incremental search as user types
- `n` next match, `N` previous match
- Current match highlighted (inverse video)
- Match count displayed
- Enter closes at match, Esc cancels

## Approach
Uses pi-tui's `TUI.showOverlay()` for modal rendering.

```typescript
class SearchOverlay implements Component {
  query: string = '';
  matches: number[] = [];  // line indices
  currentMatch: number = 0;

  handleInput(key: string) {
    if (key === 'n') this.nextMatch();
    if (key === 'N') this.prevMatch();
    if (key === 'Enter') this.confirm();
    if (key === 'Escape') this.cancel();
  }
}
```

UI:
```
┌─ Search ────────────────────────────────────────────┐
│ > error                                    3/17     │
└─────────────────────────────────────────────────────┘
```

## Quick commands
- `bun test`

## Acceptance
- [ ] `/` opens search overlay
- [ ] Typing filters incrementally
- [ ] Match count shows (3/17)
- [ ] `n` jumps to next match
- [ ] `N` jumps to previous match
- [ ] Current match highlighted
- [ ] Enter closes at match position
- [ ] Esc closes and returns to original position

## References
- flow-next-tui spec: `plans/flow-next-tui-spec.md`
- Depends on MVP output buffer and overlay system
