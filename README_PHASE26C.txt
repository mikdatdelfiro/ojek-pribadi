PHASE 26C — INSTALL FILES

Copy:
- manifest.webmanifest -> static/manifest.webmanifest
- static/icons/*       -> static/icons/
- static/splash/*      -> static/splash/
- base.html            -> templates/base.html

Android splash:
- Generated automatically by the installed PWA from manifest
  background_color, theme_color, and maskable icon.

iPhone splash:
- Uses apple-touch-startup-image entries in base.html.
