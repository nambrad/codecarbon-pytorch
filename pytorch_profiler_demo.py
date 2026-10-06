"""
This trains a tiny MLP of random data shaped like MNIST (28x28 images, 10 classes)
and uses the PyTorch profiler to record cumulative FLOPs at checkpoints
"""

import torch
import torch.nn as nn
from torch.profiler import profile, ProfilerActivity, schedule

# MLP model definition
class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28 * 28, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        return self.net(x)

def build_model():
    """
    Returns (model, optimizer, loss_fn)
    Edit this function to change the model architecture or training setup
    """
    model = MLP()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss()
    return model, optimizer, loss_fn

def build_data(batch_size=32):
    """
    Returns (images, labels)
    Edit this function to change the input data
    """
    images = torch.randn(batch_size, 1, 28, 28)
    labels = torch.randint(0, 10, (batch_size,))
    return images, labels

# Training setup
model, optimizer, loss_fn = build_model()
fake_images, fake_labels = build_data()

def train_step():
    optimizer.zero_grad()
    output = model(fake_images)
    loss = loss_fn(output, fake_labels)
    loss.backward()
    optimizer.step()

# Profile some steps, read out cumulative FLOPs
num_steps = 20
total_flops = 0

def on_ready(p):
    global total_flops
    cycle_flops = sum(e.flops for e in p.key_averages())
    total_flops += cycle_flops
    print(f"This cycle: {cycle_flops:,} FLOPs | Cumulative: {total_flops:,} FLOPs")

with profile(activities=[ProfilerActivity.CPU],
             record_shapes = True,
             with_flops = True,
             schedule = schedule(wait=0, warmup=0, active=5, repeat=4),
             on_trace_ready=on_ready) as prof:
    for step in range(1, num_steps + 1):
        train_step()
        prof.step()

print("\nTop operators by CPU time:")
print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=8))
