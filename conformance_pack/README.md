# Solar Wind Prediction Competition — conformance test kit

**Do not modify any file in this kit.** It is byte-checked on upload; any
change is rejected before the build runs, and the rejection names what you
changed. Its only job is to prove your team can build, submit, run inside
the time limit, and land a valid forecast object — *before* the real
competition, when there is still time to fix your setup.

## What it does

`run.sh` fetches nothing it depends on (the egress check is reported, never
fatal), emits a constant 72-value forecast (420 km/s), and uploads it via
`upload.sh` — the same uploader the real submission template ships. Passing
sets `conformance = PASSED`; it does **not** make you eligible to compete
(that needs a real model, submitted during pre-deploy week).

## Before you upload

Run the local check to confirm you have not accidentally touched anything
(a stray `.DS_Store`, an edited line):

```bash
bash verify.sh
```

It must print `OK — kit is unmodified`. If it prints `MODIFIED`, re-download
the kit and submit it unchanged.

## Uploading

Get your upload URL from your portal link (emailed at pre-registration),
then submit the whole kit as a zip. Zip the **contents**, not the folder:

```bash
cd swp-conformance-test && zip -r ../kit.zip .
```
