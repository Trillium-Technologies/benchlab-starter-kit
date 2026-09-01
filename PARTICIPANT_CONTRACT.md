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

