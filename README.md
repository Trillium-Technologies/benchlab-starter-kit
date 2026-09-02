![](assets/SolarWindPredictionBanner.png)

### This repository contains the starter materials for those participating in the 2026 Benchlab Solar Wind Prediction Tournament.

---

Please see [`LICENSE`](LICENSE) for terms before using anything in this repository.

**New participants: Start with [`PARTICIPANT_CONTRACT.md`](PARTICIPANT_CONTRACT.md)**

It explains the execution contract, starter-package files, local development workflow, conformance, real-model qualification, and live execution process.

Then:

1. Run the supplied example in `submission_pack/` unchanged.
2. Adapt `submission_pack/` to your forecasting workflow.
3. Test locally as you develop.
4. Complete the separate `conformance_pack/` exercise when Benchlab issues your team access.
5. During pre-deployment, submit your real workflow and iterate until it reaches ELIGIBLE .

## What's here

| Directory | What it's for |
|---|---|
| [`conformance_pack/`](conformance_pack/) | The frozen conformance test kit. Submit it unmodified to prove your access and upload path work, before you touch the real submission. See its own [README](conformance_pack/README.md). |
| [`submission_pack/`](submission_pack/) | The real submission template. This is yours to edit: replace the model, keep the contract. See its own [README](submission_pack/README.md). |

## Order of operations

1. Conformance first. Get your portal link (emailed Sept 15 after final registration/selection),
   download this repo, and submit `conformance_pack/` exactly as it is.
   Zip its contents, not the folder:
   ```bash
   cd conformance_pack && zip -r ../kit.zip .
   ```
   Run `bash verify.sh` inside `conformance_pack/` first to confirm your copy
   matches what's expected. See below if that fails on macOS.
2. Then build your real submission from `submission_pack/`, following its
   own README.

## `verify.sh` and macOS

`conformance_pack/verify.sh` calls `sha256sum`, which macOS doesn't ship by
default (it only has `shasum -a 256`). If you see `sha256sum: command not
found`, either install it (`brew install coreutils` gives you `gsha256sum`),
or run this once in the same shell before calling the script:

```bash
sha256sum() { shasum -a 256 "$@"; }
export -f sha256sum
bash conformance_pack/verify.sh
```

`export -f` is required. A plain `alias` won't reach the script, since
`bash verify.sh` runs as a separate process and doesn't inherit aliases from
your interactive shell.

---

</br> 

![](assets/SolarWindPredictionFooter.png)

</br> 

*Benchlab is an initiative of **Trillium Technologies Inc.**, hosting this competition in partnership with **Queen Mary University of London**, **CU Boulder** and the **Frontier Development Lab**. This work is supported by NASA Grant Number: 80NSSC25K7178.*

