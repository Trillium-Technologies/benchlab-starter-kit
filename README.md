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
From the top folder of this repository (the one containing `conformance_pack/` and `submission_pack/`), run `(cd conformance_pack && bash verify.sh)` to confirm your copy matches what's expected. It must print `OK — kit is unmodified`.

#### ATTENTION: If you are using MacOS 

`conformance_pack/verify.sh` calls `sha256sum`, which macOS doesn't ship by
default (it only has `shasum -a 256`). If you see `sha256sum: command not
found`, either install it (`brew install coreutils` gives you `gsha256sum`),
or run this once in the same shell before calling the script:

```bash
sha256sum() { shasum -a 256 "$@"; }
export -f sha256sum
(cd conformance_pack && bash ./verify.sh)
```

`export -f` is required. A plain `alias` won't reach the script, since
`bash verify.sh` runs as a separate process and doesn't inherit aliases from
your interactive shell.

### 3. Upload

Run these from the top folder of the repository.

Prepare your submission by zipping `conformance_pack/` *without making any changes to it*. Zip its contents, not the folder itself:

```bash
(cd conformance_pack && zip -r ../kit.zip .)
```

This creates `kit.zip` in the top folder.

Next, get your upload form from the portal. Open the portal link that was emailed to you in a browser, or run `curl -s 'YOUR_PORTAL_LINK'` (keep the quotes). Your link contains a secret token, so don't share it. You will see JSON, and its `upload` section holds what you need:

- `url`: the storage bucket address. This is **not** the portal link.
- `fields`: five values (`key`, `AWSAccessKeyId`, `x-amz-security-token`, `policy`, `signature`) that act as a one-hour upload pass.

Copy each value into the command below in place of the `...`, and use `url` as the final address. Keep `file` last:

```bash
curl -sS -o resp.txt -w 'HTTP status: %{http_code}\n' -F 'key=...' -F 'AWSAccessKeyId=...' -F 'x-amz-security-token=...' -F 'policy=...' -F 'signature=...' -F 'file=@kit.zip' 'https://...s3.amazonaws.com/'
```

`HTTP status: 204` means your file reached the upload bucket. Any other status: run `cat resp.txt` to see why. The usual cause is an expired form. They last one hour, so fetch the portal page again and retry.

To check your result, reload the portal page and look at `eligibility`, `conformance` and `failure_reason`. `conformance: PASSED` means you are done, and `eligibility` staying `REGISTERED` at this stage is correct. Your build logs are listed under `logs`.

> The `README.md` inside `conformance_pack/` mentions a different folder name in its zip command. Ignore it and use the instructions here.

#### Optional: let a script do the copy and paste

If you have `curl`, `jq` and `zip` installed (bash on macOS or Linux, or Git Bash / WSL on Windows), one script does the checking, zipping, form fetching and uploading:

```bash
cp .team.example .team              # then open .team and paste your portal link inside the quotes
bash submit_conformance.sh          # check, zip, upload
bash submit_conformance.sh status   # later: your status and build log links
```

`.team` contains your secret token, so don't commit or share it (`.gitignore` already excludes it).

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

