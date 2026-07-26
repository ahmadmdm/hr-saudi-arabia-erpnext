# Saudi HR Design System

## Direction

Arabic-first enterprise HR, calm and evidence-oriented. Use a light, high-density operating surface with clear risk semantics. The experience should feel trustworthy, not decorative.

## Tokens

- Font: `Noto Sans Arabic`, `Tajawal`, system sans-serif fallback.
- Ink: `#0F172A`; muted: `#475569`; surface: `#FFFFFF`; canvas: `#F8FAFC`; border: `#CBD5E1`.
- Primary: `#166534`; primary hover: `#14532D`; primary soft: `#DCFCE7`.
- Critical: `#B91C1C`; warning: `#B45309`; success: `#15803D`; information: `#0369A1`.
- Radius: 10px cards and fields; 999px only for badges.
- Shadows: subtle and sparse; use borders for structure.
- Spacing: 4px base, with 8/12/16/24/32px steps.

## Interaction

- Minimum control height 44px and visible `:focus-visible` ring.
- No color-only status; pair color with Arabic text and an icon or count.
- Use loading skeletons or explicit progress, helpful empty states, and retry actions.
- Use logical CSS properties and `dir="rtl"` when the active language is Arabic.
- Respect `prefers-reduced-motion`; do not animate critical alerts or loading forever.
- Buttons use a verb and object: “راجع المخالفة”, “أرفق الإثبات”, “أنشئ مهمة”.
- Error text states what failed, why when known, and the next recovery action.

## Responsive layout

- 1440+: command center with a 12-column grid.
- 1024: two-column summaries and stacked detail tables.
- 768: single-column panels with horizontally scrollable data tables.
- 375: one primary action per row, no clipped Arabic, 16px body text where reading is primary.

## Accessibility acceptance

- WCAG 2.2 AA contrast for text and controls.
- Keyboard order follows visual order; dialogs restore focus to their trigger.
- Search and filters have visible labels, not placeholder-only meaning.
- Charts repeat their values in a table or accessible list.
- Icons are decorative unless they carry an accessible name.
