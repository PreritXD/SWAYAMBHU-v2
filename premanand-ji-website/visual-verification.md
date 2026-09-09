# Visual verification — first pass

- Desktop 1280x720: hero reads as a premium saffron/charcoal devotional landing page. The lotus sits cleanly inside orbit lines with sufficient contrast; header, title, CTA, and footer line are legible.
- Mobile 390x844: layout is responsive and the menu trigger is in place, but the lotus overlaps the lower hero copy/buttons too aggressively. Next pass should push the art lower, reduce opacity slightly, and keep copy/actions above the art layer.
- Build and TypeScript checks passed before visual review.

## Final visual verification

The refined mobile hero keeps the headline and CTA readable while letting the lotus enter as a low, atmospheric visual. The full-page desktop review shows a complete rhythm from hero to darshan quote, teachings cards, Vrindavan pause, verse card, and footer. The overall hierarchy is intentionally quiet: saffron is reserved for emphasis, while cream sections create breathing room against the charcoal hero.

## Chat widget verification

The floating chat trigger appears at the lower-right of the desktop hero. Clicking it opens a compact dark-header/cream-body chat window with a visible assistant greeting, text input, send control, close control, and a clear disclaimer that it is a reflection space rather than a live guru chat. The live preview DOM exposes the expected input and buttons without errors.
