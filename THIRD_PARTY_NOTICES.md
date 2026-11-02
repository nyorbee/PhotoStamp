# Third-party notices

PhotoStamp itself is released under the MIT License (see `LICENSE`).
The Windows executable (`PhotoStamp.exe`, built with Nuitka) bundles the following
third-party components. Each one remains under its own license.

| Component | Used for | License |
|---|---|---|
| [Python](https://www.python.org/) runtime and standard library (incl. `tkinter`) | interpreter, GUI | PSF License |
| [Tcl/Tk](https://www.tcl.tk/) | GUI toolkit used by `tkinter` | Tcl/Tk License (BSD-style) |
| [Pillow](https://python-pillow.github.io/) | image loading, drawing, saving | HPND License |
| [piexif](https://github.com/hMatoba/Piexif) | reading and writing EXIF | MIT License |

Pillow's Windows wheels include further libraries, among them FreeType (FreeType License, also offered under GPLv2),
libjpeg-turbo / IJG libjpeg (IJG/BSD-style), zlib (zlib License), libpng (PNG Reference Library License),
libtiff (libtiff License), libwebp (BSD-style), Little CMS (MIT), OpenJPEG (BSD-2-Clause), HarfBuzz (MIT),
Brotli (MIT), bzip2 (BSD-style) and liblzma (public domain / 0BSD). FreeType is used under the terms of the FreeType License.
The full texts are shipped with each package: in Pillow's `LICENSE` file
(<https://github.com/python-pillow/Pillow/blob/main/LICENSE>) and in the license files installed alongside each package.

The place search in the GPS tab uses the public [Nominatim](https://nominatim.org/) service.
Data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the ODbL.

## Example photos in `docs/`

The screenshots and style examples use sample images shipped with [scikit-image](https://scikit-image.org/) (`skimage.data`):

- Falcon 9 / DSCOVR launch at Cape Canaveral – photo by SpaceX, released into the public domain.
- Coffee cup – photo by Rachel Michetti (courtesy of Pikolo Espresso Bar), CC0.
- Chelsea the cat – photo by Stefan van der Walt, CC0.
- Hubble eXtreme Deep Field – NASA, public domain.
