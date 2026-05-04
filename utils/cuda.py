import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Using device: {device}")


print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())