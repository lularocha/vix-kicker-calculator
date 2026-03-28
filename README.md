# VIX Call Strike Calculator

Small browser-based calculator for estimating a VIX call strike using the matching VX futures month instead of spot VIX.

## What It Does

- Derives a target date from an as-of date and target DTE
- Selects the nearest standard monthly VIX expiration
- Maps that expiration to the matching VX futures contract
- Auto-fills the latest available official Cboe daily settlement when served locally
- Calculates:
  - theoretical strike from `VX quote × multiplier`
  - rounded listed strike
  - distance above VX
  - estimated total option cost

## Run Locally

From the project directory:

```bash
python3 run.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Files

- `vix-kicker-calculator.html`: main app UI and calculator logic
- `run.py`: local HTTP server and Cboe settlement proxy endpoint
- `favicon.png`: site favicon

## Notes

- The calculator is a workflow helper, not trading advice.
- VX settlements come from Cboe daily settlement data.
- If you want an intraday quote, enter the VX price manually.
