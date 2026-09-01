# Solar Wind Prediction Competition — submission template

This is your starting point. Replace what needs replacing, keep the contract,
and this README, intact. `README.md` at the zip root is one of three files
the platform checks for before it will even attempt a build (the others are
`Dockerfile` and `submission.json`) — so leaving one out fails the build
before your model ever runs. Once you've read this, replace the prose below
with a description of your own model; the file just needs to exist.

## The contract

| | |
|---|---|
| **Base** | Linux. Anything you can `docker build`. Python is an example, not a requirement. |
| **Architecture** | `linux/amd64`. The build forces this. |
| **Entrypoint** | The platform runs `<your ENTRYPOINT> <timestamp>`. The timestamp is **argv[1]**. |
| **Timestamp** | e.g. `20261111T060000Z` — the cycle time, `t0`. Also available as `$INFERENCE_TIMESTAMP`. |
| **Forecast** | 72 hourly values, km/s, for `t0+1h … t0+72h`. |
| **Output** | JSON, POSTed to the one-time URL in `$OUTPUT_POST`. Max 1 MiB. |
| **Time limit** | 15 minutes wall clock from launch, **including image pull**. |
| **Resources** | As declared in `submission.json`, up to 8 vCPU / 32 GB / 20 GB usable disk. |
| **Network** | Any protocol, any public source. 20 GB per run fair use. |
| **State** | None. Every run starts fresh from the image. |
| **Success** | Exit code 0 **and** a valid forecast at the upload URL. Either alone is a failure. |

Every one of these is enforced by the platform's infrastructure, not by code
in this template.  Nothing you edit here can escape any of them, which is exactly why the template is otherwise yours to gut and rebuild.

## Layout

```
submission/
├── Dockerfile           # edit the marked region
├── run.sh               # edit the marked line
├── upload.sh            # provided — or reimplement in your language
├── submission.json      # required
├── README.md            # required — this file
├── requirements.txt     # example — delete if you don't use Python
├── model.py             # example — replace with anything
└── local_tests/         # run test_local.sh from here before you submit
    ├── test_local.sh
    └── mock_platform.py
```

Only `Dockerfile`, `submission.json`, and `README.md` are structurally
required — the platform's upload check looks for exactly those three.
Everything else is here to make the contract easy to meet:

- **`Dockerfile`** — builds your image. The top and bottom (image pull helper,
  user setup, entrypoint) are load-bearing; the middle is yours to replace
  with any language or runtime.
- **`run.sh`** — the entrypoint. One line to edit: whatever command produces
  your forecast. Everything around it (argument handling, upload call) is
  plumbing you shouldn't need to touch.
- **`upload.sh`** — sends your forecast to the platform. Reads `$OUTPUT_POST`
  (a presigned, one-time S3 upload URL the platform injects per run) and
  POSTs your output file to it. Reimplement it in your own language if you
  like; the 1 MiB cap and one-key scope are enforced by S3 regardless of
  what does the POSTing.
- **`submission.json`** — declares your team and your resource request (see
  below). Read once, at build time.
- **`requirements.txt`** — an example Python dependency list. If you're not
  using Python, delete it.
- **`model.py`** — an example model. It returns a flat 420 km/s forecast —
  a floor, not a baseline. Replace it with anything that honours the
  contract above.
- **`local_tests/`** — not required at submission time, but the fastest way
  to catch a packaging mistake before it costs you a build cycle.
  `test_local.sh` builds and runs your image exactly as the platform will;
  `mock_platform.py` stands in for the real presigned-upload endpoint so the
  upload path actually gets exercised, not skipped. Run it before every
  submission:
  ```
  cd local_tests && bash test_local.sh
  ```

## `submission.json`

```json
{
  "team_name": "Team Corona",
  "contact_email": "lead@example.edu",
  "cpu_units": 4096,
  "memory_mib": 16384,
  "declared_domains": ["services.swpc.noaa.gov", "cdaweb.gsfc.nasa.gov"]
}
```

`cpu_units` / `memory_mib` must be one of the valid Fargate combinations
below — anything else is **rounded up**, and you're billed at the rounded
tier:

| `cpu_units` | vCPU | `memory_mib` range | Step |
|---|---|---|---|
| 1024 | 1 | 2048 – 8192 | 1024 |
| 2048 | 2 | 4096 – 16384 | 1024 |
| 4096 | 4 | 8192 – 30720 | 1024 |
| 8192 | 8 | 16384 – 32768 | 4096 |

Note the 4-vCPU tier tops out at **30720 MiB (30 GB), not 32 GB** — "4 cores
and 32 GB" isn't a real Fargate shape. Requesting it gets you promoted to
8 vCPU automatically. Your portal page always shows what you were actually
granted.

## Output schema

The platform only reads `forecast_speed_kms`. Everything else in the object
is yours to use or ignore.

```json
{
  "t0": "2026-11-11T06:00:00Z",
  "valid_from": "2026-11-11T07:00:00Z",
  "forecast_speed_kms": [418.2, 419.9, "... 72 values total ..."]
}
```

## Two mistakes worth avoiding up front

**A plain `FROM ubuntu:22.04` or `FROM python:3.11-slim` will eventually hit
a Docker Hub rate limit** during the build (shared build infrastructure,
shared outbound IPs). Use the ECR Public Gallery mirrors instead —
`public.ecr.aws/ubuntu/ubuntu:22.04`, `public.ecr.aws/docker/library/python:3.11-slim` —
already what this template uses. Browse [gallery.ecr.aws](https://gallery.ecr.aws)
for others.

**If you use PyTorch, keep the CPU wheel.** Deleting `--extra-index-url
https://download.pytorch.org/whl/cpu` and `+cpu` from `requirements.txt`
pulls the CUDA build — about 2.5 GB of NVIDIA libraries onto hardware with
no GPU. That's 2.3 GB you store in the registry for six months and re-pull
inside your 15-minute budget on every run. `tensorflow-cpu` has the same
trap and the same fix.
