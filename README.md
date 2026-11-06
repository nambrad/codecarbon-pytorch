# PyTorch Emissions Tracking with CodeCarbon

We measure the energy use and CO2 emissions of our PyTorch training runs with
[CodeCarbon](https://github.com/mlco2/codecarbon) and keep the results here.

## Setup (once)

```bash
git clone <this-repo-url>
cd <repo-folder>
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r codecarbon/requirements.txt -r rot/requirements.txt
```

For an NVIDIA GPU, install the CUDA build of PyTorch from https://pytorch.org/get-started/locally/
before running `pip install -r codecarbon/requirements.txt`. CodeCarbon picks up the GPU automatically.

Check what hardware CodeCarbon can see:

```bash
codecarbon detect
```

## Run an experiment

Run these from inside `codecarbon/`, where `train.py`, `summarize.py` and `.codecarbon.config` live:

```bash
cd codecarbon
python train.py --epochs 3 --tag baseline --who yourname
```

- `--tag` names the experiment (e.g. `baseline`, `mixed-precision`, `batch-256`) so runs can be compared.
- `--who` picks your results file, `codecarbon/results/emissions_<who>.csv`. Each person has their own file,
  so pushing results never causes merge conflicts.

To plug in a real model, edit `build_model()` and `get_data()` in `codecarbon/train.py`.

To track any other script without editing it:

```bash
codecarbon monitor --offline --country-iso-code USA -- python my_script.py
```

## Share results

```bash
python summarize.py              # rebuilds results/SUMMARY.md from everyone's CSVs
git pull
git add results/
git commit -m "Add <tag> run"
git push
```

Open `codecarbon/results` on GitHub to see a table of all runs.

## Settings

Shared settings live in `codecarbon/.codecarbon.config`. If you're somewhere other than Massachusetts,
override the location without editing the file:

```bash
export CODECARBON_COUNTRY_ISO_CODE=USA    # 3-letter ISO code, e.g. GBR, FRA, CAN
export CODECARBON_REGION=california       # US state / Canadian province, lowercase
```

We use offline mode on purpose: the default online mode looks up your location by IP
and writes latitude/longitude into the CSV, which we don't want in a shared repo.

## Accuracy notes

- NVIDIA GPUs are measured directly and accurately.
- Linux with Intel/AMD CPUs: CPU power is read from RAPL. If you see "Falling back on estimation"
  warnings, run `sudo chmod -R a+r /sys/class/powercap/intel-rapl` (resets on reboot).
- macOS and Windows: CPU power is estimated from the chip's rated power and load, so compare
  runs on the same machine rather than across machines.
- Very short runs (under a minute) give noisy numbers. Longer runs are more meaningful.

# PyTorch Profiler FLOP Count and CPU Time Tracking
We measure the FLOP counts and CPU time of runs on an ML model with [PyTorch](https://docs.pytorch.org/docs/stable/profiler.html).

## Setup
Install PyTorch if you haven't already:
```bash
pip install torch --break-system-packages
```

# Run the profiler
```bash
python pytorch/pytorch_profiler_demo.py
```

Currently, the profiler runs on a tiny MLP model. To change the model, optimizer, or loss function, edit the `build_model` function. To change the training data images or labels, edit the `build_data` function.

# Compliance Game

Students act as a data center compliance officer: for each signed job record they check the
evidence, then allow or block the job against the compute limits in `game_config.json`.

## Files

| File | Who edits it | What it is |
|---|---|---|
| `levels.json` | instructors | Hand-written records per level. Forged and replayed records are marked with `"attack"` |
| `game_config.json` | instructors | FLOP and energy limits, reference ranges per workload type |
| `answer_keys.json` | instructors | Correct verdict for every record |
| `game_data.json` | generated | Config + chip registry + signed records: **everything students load** |
| `play.py` | | Runs a level |
| `rot/` | | Simulated hardware root of trust (see `rot/README.md`) |

## Rebuild game_data.json

After any change to `levels.json` or `game_config.json`, from the repo root:

```bash
python -m rot.sign_levels
```

It signs every record with its lab's chip, builds the registry, checks that honest records pass and
attack records fail, and warns about any record missing from `answer_keys.json`.

## Play

```bash
python play.py 1        # level 1 to 4
```
