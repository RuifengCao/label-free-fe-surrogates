"""Exit code 0 if torch sees a CUDA GPU, 2 otherwise; prints what it found."""
import sys

import torch

print("torch", torch.__version__, "| cuda build", torch.version.cuda, "| gpu seen", torch.cuda.is_available(),
      "|", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no device")
sys.exit(0 if torch.cuda.is_available() else 2)
