## Start here: how your submission works

Benchlab provides a starter submission package that contains the small
amount of infrastructure needed to run your forecasting workflow in the
competition environment.

At a high level, your submission works like this:

    Dockerfile
        ↓
    builds a reproducible Linux environment containing your model
        ↓
    Benchlab starts a fresh container every 6 hours
        ↓
    run.sh receives the inference timestamp (`t0`)
        ↓
    your model runs
        ↓
    your workflow produces 72 hourly solar-wind-speed predictions
        ↓
    forecast.json
        ↓
    upload.sh returns that forecast to Benchlab

You are free to implement the scientific forecasting workflow however you
choose. Python is provided only as an example. R, Julia, compiled binaries,
hybrid physics–ML workflows, and other approaches are all acceptable as
long as the final container obeys the interface described below.

### Build once, run many times

There are two different stages to understand:

**Build stage**

Docker reads your `Dockerfile` and creates a Docker image containing your
operating system, software dependencies, model code, model weights, and
supporting scripts.

**Inference stage**

Benchlab starts a fresh container from that frozen image for every inference
cycle. The container receives the cycle timestamp, runs your forecasting
workflow, uploads its forecast, and then terminates.

The image is therefore frozen during live evaluation, but the data your
workflow retrieves at each inference timestamp may change.

Every run is stateless: do not assume that files, memory, downloaded data,
or other state from an earlier run will still exist.

## What's in the submission package?

The starter package contains both the Benchlab interface and a minimal example forecasting workflow.

| File | What it does | What you should do |
|---|---|---|
| `Dockerfile` | The recipe Docker uses to build the Linux environment in which your workflow runs. It installs required software and copies your model/code into the image. | Edit the marked participant section to install your runtime, dependencies, model code, weights, and other required assets. Keep the Benchlab interface requirements intact. |
| `model.py` | A minimal example forecasting program. The supplied version simply returns 420 km/s for all 72 forecast hours. | Replace this with your own forecasting logic, or replace it entirely if you use another language/framework. |
| `requirements.txt` | Lists the Python packages installed when the example Docker image is built. | Add your Python dependencies here. Delete/replace it if you do not use Python. |
| `run.sh` | The bridge between Benchlab and your forecasting workflow. Benchlab supplies `t0`; this script launches your model, creates `forecast.json`, and calls the output uploader. | Usually only the marked model-execution line needs changing. |
| `upload.sh` | Sends the completed `forecast.json` to the temporary output location supplied by Benchlab for that run. | Normally leave this unchanged. You may reimplement the same behavior in another language. |
| `submission.json` | Declares the compute resources and basic configuration your submission requires. | Set your team information, CPU, memory, and declared external domains. |
| `README.md` | Documentation describing **your submitted model/workflow**. Benchlab requires this file to exist at the root of your final submission. | Replace the placeholder with documentation of your own approach, inputs, dependencies, weights/assets, external data sources, and reproducibility information. |
| `local_tests/` | A local simulation of the basic Benchlab execution contract. It builds your Docker image, launches it with a test timestamp, receives the forecast using a mock Benchlab endpoint, and validates the output. | Run this repeatedly while developing your submission. |

## Recommended workflow

### 1. Run the supplied example unchanged

Before editing anything, confirm that Docker and the Benchlab interface work
on your machine:

    cd submission_pack/local_tests
    ./test_local.sh 20261111T060000Z

A successful run ends with:

    PASS — out/forecast.json is valid

The supplied example predicts a constant 420 km/s for all 72 forecast hours.
It demonstrates the interface only; it is not intended to be a competitive
forecasting model.

### 2. Replace the example forecasting logic

Adapt `model.py`, or replace it with your own program.

Your workflow receives an inference timestamp `t0` and must ultimately
produce exactly 72 hourly solar-wind-speed predictions representing:

    t0 + 1 hour
    ...
    t0 + 72 hours

### 3. Add your dependencies and model assets

Update the editable region of the `Dockerfile` and, where applicable,
`requirements.txt`.

Include any trained model weights or other files required for inference in
the Docker image unless your workflow obtains them from an approved public
source at runtime.

### 4. Configure resources

Edit `submission.json` to specify the CPU and memory your workflow requires
and declare the external domains it expects to contact.

### 5. Test locally again

Run `local_tests/test_local.sh` until the complete container builds,
executes, uploads a forecast, and passes output validation.

Passing the local test proves interface compatibility on your own machine.
It does **not** mean your model is yet eligible for the live tournament.

### 6. Complete Benchlab conformance

When access is issued, follow the separate conformance instructions using
the fixed organizer-provided conformance package.

Conformance tests your access to the Benchlab submission/build/run pathway.
It does not test or qualify your scientific model.

### 7. Submit your real workflow during pre-deployment

Package your completed submission and upload it using your team-specific
Benchlab access instructions.

Benchlab will build the submitted Docker image and execute a real dry run.
Only a submission that builds and completes a valid dry run becomes
`ELIGIBLE` for live evaluation.

### 8. Review the result of the real dry run

After you upload your real competition submission, Benchlab handles the
qualification process automatically.

The platform will:

1. validate the submitted package
2. build the Docker image for `linux/amd64`
3. check the resulting image against the competition limits
4. launch a real inference dry run
5. validate the uploaded forecast output 
6. mark the submission `ELIGIBLE` only if the complete pathway succeeds

A successful Docker build by itself is **not** enough to qualify.

Your actual forecasting workflow must start successfully, complete within
the runtime limit, return a valid forecast, and exit successfully.

### 9. Fix and resubmit if necessary

The pre-deployment period is intended to give you time to identify and fix
integration problems before live evaluation begins.

A real submission may fail for reasons such as:

- a package-layout or configuration error
- a Docker build failure
- a missing dependency
- a container startup or runtime error
- failure to retrieve required input data
- exceeding the runtime limit
- producing an invalid or missing forecast

Review the available status information and logs, correct the problem
locally, rerun the local compatibility test, and submit a revised version.

**Important:** a replacement upload becomes your latest submission and must
qualify in its own right. Do not assume that an earlier eligible version
will automatically remain available as a fallback if a replacement fails.

Near the live-start deadline, leave enough time for the complete
build-and-dry-run process and for any corrections that may be required.

### 10. Reach `ELIGIBLE`

A submission becomes `ELIGIBLE` only after its real Benchlab dry run has
successfully completed and produced a valid forecast.

Only `ELIGIBLE` submissions can take part in live evaluation.

Once your intended competition version has reached `ELIGIBLE`, avoid making
unnecessary last-minute changes. Any replacement submission must pass the
qualification pathway again.

### 11. Live execution begins

Once live evaluation starts, participants do not manually trigger
forecasts.

Every 6 hours, Benchlab automatically:

1. selects the qualified submission
2. starts a fresh container from its built image
3. supplies the new inference timestamp `t0`
4. gives the container its one-time forecast output destination
5. runs the forecasting workflow
6. receives and validates the forecast 
7. terminates the container

The next inference cycle starts again from a fresh container.

Your submitted image is therefore the reproducible forecasting system being
evaluated. Your model may retrieve new permitted observations at each cycle,
but its code, packaged model assets, and software environment come from the
qualified image.

---

## The inference timestamp and data cut-off

For every live run, Benchlab supplies an inference timestamp called `t0`.

It is passed as the first command-line argument to the container entrypoint,
for example:

    20261111T060000Z

The same value is also exposed as:

    $INFERENCE_TIMESTAMP

Your forecast is initialized at this time.

The required 72 values represent:

    forecast[0]  → t0 + 1 hour
    forecast[1]  → t0 + 2 hours
    ...
    forecast[71] → t0 + 72 hours

### No future data

Your workflow may use historical and live public data, but every piece of
information used for an inference at `t0` must have been available at or
before `t0`.

This remains true even if your container starts or retrieves the data a few
minutes after the nominal inference timestamp.

For example, for:

    t0 = 2026-11-11 12:00 UTC

a product that was already available at:

    11:55 UTC

may be used, even if your container retrieves it at 12:03 UTC.

A product that first became available at:

    12:01 UTC

must **not** be used for the 12:00 forecast. It may be used in a later
inference cycle.

A useful rule to remember is:

> **The fetch may happen after `t0`; the information may not.**

Your workflow is responsible for respecting this cut-off.

---

## Data access and responsibility

Benchlab does not provide or forward-fill the scientific input data required
by each participant's model.

Your submitted workflow is responsible for retrieving and handling its own
permitted input data at inference time.

You should design for realistic operational conditions, including:

- data latency
- missing observations
- temporary upstream-service failures
- changes in response time
- incomplete input products

Do not assume that every external source will always respond immediately or
contain every expected observation.

Public internet access is available to the running container, subject to
the published competition rules and a 20 GB-per-run network fair-use limit.

List the external domains your workflow expects to use in
`submission.json`.

If your workflow needs pretrained weights or other model assets, the most
reliable approach is generally to package them into the image. Runtime
retrieval is possible only where it remains compatible with the competition
data rules, network limits, image/runtime design, and the 15-minute
execution budget.

---

## Required forecast output

Each inference must produce one forecast containing exactly **72 hourly
solar-wind-speed predictions**, in kilometres per second.

The starter package uses the following JSON structure:

```json
{
  "t0": "2026-11-11T06:00:00Z",
  "valid_from": "2026-11-11T07:00:00Z",
  "forecast_speed_kms": [
    418.2,
    419.9
  ]
}
```

The `forecast_speed_kms` array must contain exactly 72 values, ordered from
`t0 + 1 hour` through `t0 + 72 hours`.


\section*{Quick pre-submission checklist}

Before uploading a real competition submission, confirm that:
\begin{itemize}
\item[-] □ the supplied example worked locally before you began modifying it;
\item[-] □ your complete adapted workflow passes local_tests/test_local.sh ;
\item[•] □ your image builds for linux/amd64;
\item[-] □ your workflow accepts the supplied t0;
\item[-] □ your live-data logic respects the t0 data cut-off;
\item[-] □ your forecast contains exactly 72 hourly speed predictions;
\item[•] □ your workflow returns the forecast through the required output path;
\item[•] □ your CPU and memory request is a supported combination;
\item[•] □ required runtime domains are declared in submission.json;
\item[-] □ required model weights/assets are available at inference time;
\item[•] □ your Docker image remains below the published size limit;
\item[•] □ the workflow completes comfortably within the 15-minute budget;
\item[•] □ Dockerfile, submission.json, and README.md are at the ZIP root;
\item[-] □ your README.md documents the actual submitted workflow; and
\item[-] □ you have left enough time to review a failed cloud qualification and resubmit if necessary.
\end{itemize}
The complete output object must be no larger than **1 MiB**.

The running container receives a one-time output specification through:
```bash
$OUTPUT_POST
```

The supplied `upload.sh` uses that value to return the completed forecast to Benchlab. Your container does not need AWS credentials.

A successful run requires both the forecasting workflow to exit successfully and Benchlab to receive a valid forecast output. One without the other does not constitute a successful inference.
