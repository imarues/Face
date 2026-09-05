# MultiFace

MultiFace is an iKiraPlus multi-tweak controller for Facebook.

## Panel
- Open with a three-finger touch/hold (0.05 s) anywhere in Facebook.
- Arabic is the default language.
- Supported UI languages: Arabic, English, French, Spanish, Chinese, Turkish, Persian, Russian, Vietnamese, Indonesian.
- Changing language saves it and closes Facebook; reopen to apply.
- Tweak switches are staged in the panel and are saved only when **Done** is tapped.
- Includes the same iKiraPlus / certificate / ipaStore cards and direct links as MultiTele.

## Stability safeguards
- Selected tweaks are applied after Facebook becomes active instead of directly in the dylib constructor.
- A startup guard marks tweak activation as pending. If Facebook crashes before startup stabilizes, the next launch automatically disables all managed tweaks so the app does not remain in a crash loop.
- Wolf's non-lazy Firebase `APMScreenClassName` analytics category is neutralized while Wolf is disabled, preventing its `+load` from swizzling every `UIViewController` before Wolf is selected.

## Managed tweaks
- iQFace
- Glow
- Wolf

All three supplied tweaks are arm64 and depend on CydiaSubstrate/ElleKit compatibility. The final Feather package should include `CydiaSubstrate.dylib` alongside the four tweak dylibs.
