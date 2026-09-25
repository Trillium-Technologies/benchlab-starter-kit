![](assets/SolarWindPredictionBanner.png)

### This repository contains the starter materials for those participating in the 2026 Benchlab Solar Wind Prediction Tournament.

---

Please see [`LICENSE`](LICENSE) for terms before using anything in this repository.

| Directory | What it's for |
|---|---|
| [`conformance_pack/`](conformance_pack/) | The frozen conformance test kit. Submit it unmodified to prove your access and upload path work, before you touch the real submission. See instructions [below](#conformance-do-this-first). |
| [`submission_pack/`](submission_pack/) | The real submission template. This is yours to edit: replace the model, keep the contract. See instructions [below](#submission). |

## Conformance (DO THIS FIRST)

### 1. Download
Download this repository.

### 2. Verify
From inside the `conformance_pack/` folder, run `bash verify.sh` to confirm your copy matches what's expected.

#### ATTENTION: If you are using MacOS 

`conformance_pack/verify.sh` calls `sha256sum`, which macOS doesn't ship by
default (it only has `shasum -a 256`). If you see `sha256sum: command not
found`, either install it (`brew install coreutils` gives you `gsha256sum`),
or run this once in the same shell before calling the script:

```bash
sha256sum() { shasum -a 256 "$@"; }
export -f sha256sum
cd conformance_pack/
bash ./verify.sh
```

`export -f` is required. A plain `alias` won't reach the script, since
`bash verify.sh` runs as a separate process and doesn't inherit aliases from
your interactive shell.

### 3. Upload

Prepare your submission by zipping `conformance_pack/` *without making any changes to it*.

   Zip its contents, not the folder itself:
   ```bash
   cd conformance_pack && zip -r ../kit.zip .
   ```

Then, get your portal link, which was emailed to you on Sept 25, and upload `kit.zip` exactly as it is.

## Submission

**Start with [`PARTICIPANT_CONTRACT.md`](PARTICIPANT_CONTRACT.md)**

It explains the execution contract, starter-package files, local development workflow, conformance, real-model qualification, and live execution process.

Then:

1. Run the supplied example in `submission_pack/` unchanged.
2. Adapt `submission_pack/` to your forecasting workflow.
3. Test locally as you develop.
4. **During the pre-deployment window**, submit your real workflow and iterate until it reaches **ELIGIBLE**.

---

</br> 

![](assets/SolarWindPredictionFooter.png)

</br> 

*Benchlab is an initiative of **Trillium Technologies Inc.**, hosting this competition in partnership with **Queen Mary University of London**, **CU Boulder** and the **Frontier Development Lab**. This work is supported by NASA Grant Number: 80NSSC25K7178.*

