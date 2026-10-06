# PyTorch Emissions Tracking with CodeCarbon

We measure the energy use and CO2 emissions of our PyTorch training runs with
[CodeCarbon](https://github.com/mlco2/codecarbon) and keep the results here.

## Setup (once)

```bash
git clone <this-repo-url>
cd <repo-folder>
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

For an NVIDIA GPU, install the CUDA build of PyTorch from https://pytorch.org/get-started/locally/
before running `pip install -r requirements.txt`. CodeCarbon picks up the GPU automatically.

Check what hardware CodeCarbon can see:

```bash
codecarbon detect
```

## Run an experiment

```bash
python train.py --epochs 3 --tag baseline --who yourname
```

- `--tag` names the experiment (e.g. `baseline`, `mixed-precision`, `batch-256`) so runs can be compared.
- `--who` picks your results file, `results/emissions_<who>.csv`. Each person has their own file,
  so pushing results never causes merge conflicts.

To plug in a real model, edit `build_model()` and `get_data()` in `train.py`.

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

Open `results/SUMMARY.md` on GitHub to see a table of all runs.

## Settings

Shared settings live in `.codecarbon.config`. If you're somewhere other than Massachusetts,
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
python pytorch_profiler_demo.py
```

Currently, the profiler runs on a tiny MLP model. To change the model, optimizer, or loss function, edit the `build_model` function. To change the training data images or labels, edit the `build_data` function.
