# Dota SEA Chat Translator

Dota SEA Chat Translator is an independent accessibility/translation utility.
It only captures a user-selected region of visible screen pixels.

It does not read Dota 2 process memory, inject DLLs, modify game files, inspect
network packets, or automate input. It is designed to minimize anti-cheat
interaction by remaining a screen-only OCR application.

Dota 2 and related trademarks belong to Valve Corporation. This project is not
affiliated with or endorsed by Valve. Use third-party software at your own
discretion; no software can guarantee how future anti-cheat policies or
implementations may change.

Development status and the exact resume point are tracked in
[`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md).
Chinese Windows startup and final acceptance steps are in
[`WINDOWS_SETUP_AND_ACCEPTANCE.zh-CN.md`](WINDOWS_SETUP_AND_ACCEPTANCE.zh-CN.md).

## Current MVP

The application now provides:

- tray-only startup;
- strict foreground Dota 2 window detection through desktop window APIs;
- mouse ROI calibration stored as client-area ratios;
- `mss` ROI capture, black-frame warning, change detection and debounce;
- three OCR preprocessing presets;
- PaddleOCR PP-OCRv5 Latin recognition with low-confidence Thai fallback;
- OCR line reconstruction, speaker parsing and 15-second fuzzy deduplication;
- Unicode-first Thai/Chinese detection and lazy fastText `lid.176` detection;
- lazy local NLLB/CTranslate2 int8 translation with a runtime cache and Dota glossary;
- a focus-safe, click-through subtitle overlay with five-message expiry;
- bounded capture, OCR and translation queues that discard stale work;
- tray-based overlay positioning and a minimal settings dialog.

## Project story (STAR)

- **Situation:** SEA Dota matches mix several languages in a fast-moving chat,
  while existing translation approaches can introduce privacy or anti-cheat risk.
- **Task:** Build a responsive, fully local translator without reading game
  memory, injecting code, automating input, or sending chat data to a service.
- **Action:** Designed a screen-only pipeline that limits capture to a calibrated
  region, avoids redundant OCR through change detection and deduplication, drops
  stale work with bounded queues, and combines language-aware OCR with local
  int8 translation behind a focus-safe overlay.
- **Result:** Delivered the end-to-end MVP with 57 automated tests and a passing
  security scan. Screenshots and chat stay in memory, and real Windows/Dota
  accuracy and latency are explicitly tracked as the remaining acceptance work.

## Development setup

Target: Windows 10/11 x64 and Python 3.11 or 3.12.

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy config.example.yaml config.yaml
run.bat
```

Install the download/conversion dependencies, accept the NLLB license notice,
and fetch all local models once:

```bat
.venv\Scripts\python -m pip install -r requirements-models.txt
.venv\Scripts\python scripts\download_models.py --accept-nllb-license
```

The large source NLLB checkpoint is downloaded into a temporary directory and
removed after int8 conversion. Normal application runtime does not download or
upload anything.

PaddleOCR currently uses its v3 `predict()` API with
`latin_PP-OCRv5_mobile_rec` first and `th_PP-OCRv5_mobile_rec` only as a
fallback.

Language detection uses the official `lid.176.bin` file at
`models\lid.176.bin`. Missing models safely fall back to `unknown`.

## Run the application

1. Start Dota 2 in Borderless Window mode.
2. Run `run.bat`; the app starts in the Windows system tray.
3. Choose **Calibrate Chat Area** and drag around the visible chat messages.
4. Leave **Translation Enabled** checked. New supported-language chat is
   translated on a background worker and appears in the subtitle overlay.
5. Use **Move Overlay** to temporarily disable click-through and drag the
   subtitles, then uncheck it before playing.
6. Use **Settings**, **Debug ROI Preview**, or **Test OCR Image** as needed.

The one-shot console command is also available:

```bat
.venv\Scripts\python -m app.ocr.test_image path\to\chat-roi.png
```

If capture remains black, switch Dota 2 to Borderless Window mode. The app does
not attempt a DirectX hook or another bypass. Capture and OCR pause while Dota
2 is not the foreground window.

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

## Still requiring target-machine validation

The automated suite runs without Dota or a Windows desktop. Before calling the
first delivery stable, verify on Windows 10/11 with real Dota chat that:

- tray actions and DPI-scaled ROI selection align correctly;
- `mss` captures Borderless Window pixels without black frames;
- Latin, Vietnamese accents and Thai are readable with the downloaded models;
- one visible message produces one console event after remaining on screen.

Record results in `DEVELOPMENT_PLAN.md` under Phase 7.3.
