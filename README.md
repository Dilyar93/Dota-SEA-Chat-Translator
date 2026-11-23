# Dota SEA Chat Translator

Dota SEA Chat Translator is a Windows tray utility that translates visible Dota 2
chat into Simplified Chinese. With Dota 2 in the foreground, press **F8** to
capture and translate the calibrated chat area once.

It does not read Dota 2 process memory, inject DLLs, modify game files, inspect
network packets, or automate input. It is designed to minimize anti-cheat
interaction by remaining a screen-only OCR application.

Dota 2 and related trademarks belong to Valve Corporation. This project is not
affiliated with or endorsed by Valve. Use third-party software at your own
discretion; no software can guarantee how future anti-cheat policies or
implementations may change.

- [Windows setup and testing guide (简体中文)](WINDOWS_SETUP_AND_ACCEPTANCE.zh-CN.md)
- [Design overview (简体中文)](description.md)
- [Development status and verification](DEVELOPMENT_PLAN.md)

## Current MVP

The application now provides:

- tray-only startup;
- strict foreground Dota 2 window detection through desktop window APIs;
- mouse ROI calibration stored as client-area ratios;
- on-demand `mss` ROI capture with **F8** and black-frame feedback;
- three OCR preprocessing presets;
- PaddleOCR PP-OCRv5 Latin recognition with a Thai fallback for uncertain or untranslatable text;
- OCR line reconstruction, speaker parsing and fuzzy deduplication within each snapshot;
- Thai and Chinese character checks followed by fastText `lid.176` language detection;
- local NLLB/CTranslate2 int8 translation with a runtime cache and Dota glossary;
- a focus-safe, click-through subtitle overlay with five-message expiry;
- background model loading at startup, with progress and empty-result feedback after F8;
- tray-based overlay positioning and a minimal settings dialog.

## Project story (STAR)

- **Situation** — SEA Dota matches mix several languages in a fast-moving chat,
  while existing translation approaches can introduce privacy or anti-cheat risk.
- **Task** — Build a responsive, fully local translator without reading game
  memory, injecting code, automating input, or sending chat data to a service.
- **Action** — Designed a screen-only pipeline that captures a calibrated region
  on demand and combines language-aware OCR with local int8 translation behind a
  focus-safe overlay.
- **Result** — Passed 64 automated tests and the security check on Windows and WSL.
  Windows checks covered screen capture, calibration at 175% display scaling, and
  translations from Indonesian and mixed Thai sample images. In-match accuracy and
  latency are tracked in the [development plan](DEVELOPMENT_PLAN.md).

## Windows setup

Use Windows 10 or 11 x64 with Python 3.11 or 3.12. Run these commands from the
project folder in Command Prompt. If you have Python 3.12, use `py -3.12`.

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-models.txt
```

Read the NLLB model license before downloading the models. Run the following
commands if you accept its CC BY-NC 4.0 terms for personal, non-commercial use.
[NLLB model license](https://huggingface.co/facebook/nllb-200-distilled-600M)

```bat
.venv\Scripts\python scripts\download_models.py --accept-nllb-license
run.bat
```

The setup script downloads the OCR and language-detection models and converts
the NLLB checkpoint to int8 in `models`. The application uses those local models
offline. `run.bat` creates `config.yaml` on the first launch.

## Run the application

1. Start Dota 2 in Borderless Window mode.
2. Run `run.bat`; the app starts in the Windows system tray.
3. Choose **Calibrate Chat Area** and drag around the visible chat messages.
4. Leave **Translation Enabled** checked. With the game in the foreground and
   chat visible, press **F8**. The overlay shows recognition progress, then
   translations or a message explaining why the snapshot produced none.
5. Use **Move Overlay** to drag the subtitles, then uncheck it to restore
   click-through.
6. Use **Settings**, **Debug ROI Preview**, or **Test OCR Image** as needed.

The default languages are Indonesian, Malay, Filipino, Thai and Vietnamese.
English and Chinese are skipped by default. Thai chat can trigger a second OCR
pass when the Latin model reads a plausible player prefix but yields no
translatable text. The player prefix may still contain misread brackets or labels.

Use this command to inspect OCR on a single image.

```bat
.venv\Scripts\python -m app.ocr.test_image path\to\chat-roi.png
```

If capture remains black, switch Dota 2 to Borderless Window mode. With
translation enabled, the app registers F8 while Dota 2 has focus and releases
the key when you switch away.

## Tests

```bat
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts\security_check.py
```

With Dota 2 in the foreground and a foreign chat line visible, measure the real
local pipeline (including model initialization on the first run):

```bat
.venv\Scripts\python scripts\benchmark.py
```

The benchmark exits with an error instead of printing placeholder values when
the window, chat text, or models are unavailable.

## Privacy and local models

Screenshots and chat text remain in memory by default. The application does not
save screenshots, save chat logs, upload pixels, upload OCR text, or require an
API key. Network access is only needed when local models are downloaded for the
first time.

The default NLLB translation model is intended for personal,
non-commercial use in this project under CC-BY-NC-4.0. Do not assume the model
license permits commercial redistribution; review and replace the model before
any commercial release.

The fastText language model is CC-BY-SA-3.0. PaddleOCR model repositories used
by the downloader identify their license as Apache-2.0. Review all model terms
before redistribution.

## In-match verification

The automated suite runs without Dota or a Windows desktop. The
[Windows testing guide](WINDOWS_SETUP_AND_ACCEPTANCE.zh-CN.md) covers
in-match checks for chat capture, F8 behavior, multilingual OCR, subtitles and
latency. In sample tests, the Latin OCR model missed some Vietnamese diacritics.

See the [development plan](DEVELOPMENT_PLAN.md) for completed and pending checks.
