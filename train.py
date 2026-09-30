"""
Train a PyTorch model while CodeCarbon measures energy use and CO2 emissions.

Usage:
    python train.py                       # quick demo run
    python train.py --epochs 5 --tag baseline

Each person's results go to results/emissions_<name>.csv so you never get git merge conflicts.
Replace build_model() and get_data() with your real model and dataset.
"""
import argparse
import getpass

import torch
import torch.nn as nn
from codecarbon import OfflineEmissionsTracker


def build_model():
    # TODO: swap in your real model
    return nn.Sequential(
        nn.Linear(784, 256), nn.ReLU(),
        nn.Linear(256, 128), nn.ReLU(),
        nn.Linear(128, 10),
    )


def get_data(n=20_000, batch_size=128):
    # TODO: swap in your real DataLoader. Synthetic data keeps the demo download-free.
    x = torch.randn(n, 784)
    y = torch.randint(0, 10, (n,))
    ds = torch.utils.data.TensorDataset(x, y)
    return torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=True)


def train(epochs, device):
    model = build_model().to(device)
    loader = get_data()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        total = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"epoch {epoch + 1}/{epochs}  loss={total / len(loader):.4f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--tag", default="demo", help="label for this experiment, e.g. baseline, bigger-batch")
    p.add_argument("--who", default=getpass.getuser(), help="your name; picks your results file")
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Running on {device} as '{args.who}', tag '{args.tag}'")

    # Other settings (output folder, country/region, etc.) come from .codecarbon.config.
    # The tag is stored in the CSV's project_name column so you can compare experiments.
    tracker = OfflineEmissionsTracker(
        project_name=args.tag,
        output_file=f"emissions_{args.who}.csv",
    )
    tracker.start()
    try:
        train(args.epochs, device)
    finally:
        kg = tracker.stop()

    data = tracker.final_emissions_data
    print(f"\nEnergy used: {data.energy_consumed * 1000:.3f} Wh")
    print(f"Emissions:   {kg * 1000:.4f} g CO2eq")
    print(f"Saved to results/emissions_{args.who}.csv")


if __name__ == "__main__":
    main()
