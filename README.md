# Fashion Prompt Studio

A bilingual (Chinese/English) fashion prompt generator for AI image generation models. Select from 1000+ fashion attributes across 10+ categories to build detailed outfit descriptions, or use the curated random generator for quick inspiration.

Built with **PyWebView** (desktop) and **Flutter** (Android).

## Features

- **10+ fashion categories**: Style direction, person description, hair, makeup, tops, necklines, sleeves, fabrics, structural details, bottoms, dresses, outerwear, shoes, bags, accessories, colors, patterns
- **1000+ bilingual entries**: Every option includes Chinese (`zh`), English (`en`), and description (`desc`) for prompt generation
- **3 AI model outputs**: Supports Z-Image (weighted Chinese prompt), Qwen-Image (natural Chinese), and Flux (English)
- **Curated random generator**: Smart zone-based selection (style → person → hair → makeup → outfit → shoes → accessories → color → pattern) with weighted probabilities for common/popular items
- **Lock/zone controls**: Freeze specific attributes and toggle entire categories on/off for precise control
- **Z-Image-Turbo quick link**: One-click launch of the Z-Image-Turbo web frontend from the sidebar

## Desktop (Windows)

### Requirements

- Python 3.8+
- [PyWebView](https://github.com/r0x0r/pywebview) (`pip install pywebview`)

### Run from source

```bash
cd build
python app.py
```

### Build standalone exe

```bash
pip install pyinstaller
pyinstaller FashionPromptGenerator.spec
```

The built exe will be at `dist/FashionPromptGenerator.exe`.

## Android

### Download

Download the latest APK from [Releases](https://github.com/lvqunx/Fashion-Prompt-Studio/releases) (or build from source below).

### Build from source

```bash
cd fashion_prompt_flutter
flutter build apk --release
```

APK at `build/app/outputs/flutter-apk/app-release.apk`.

### Requirements

- Flutter SDK
- Android SDK (API 21+)

## Project Structure

```
├── build/                          # Desktop app (Python + PyWebView)
│   ├── app.py                      # Entry point, API, prompt generators
│   ├── index.html                  # Web UI (sidebar, selection panels, preview)
│   ├── fashion_data.py             # 1000+ bilingual fashion options
│   ├── FashionPromptGenerator.spec # PyInstaller config
│   └── dist/FashionPromptGenerator.exe
│
├── fashion_prompt_flutter/         # Flutter mobile app
│   ├── lib/                        # Dart source code
│   ├── assets/fashion_data.json    # Bilingual fashion data
│   └── pubspec.yaml
│
└── README.md
```

## License

MIT
