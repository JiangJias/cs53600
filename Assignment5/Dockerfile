# Use the official PyTorch image as the base.
# This provides native support for torch.distributed and the gloo backend.
FROM pytorch/pytorch:latest

# Set the working directory inside the container
WORKDIR /app

# Install matplotlib, which is required for plotting the assignment benchmark graphs
RUN pip install --no-cache-dir matplotlib

# Default command to execute when the container starts
# (This can be overridden when running 'docker run')
CMD ["python", "benchmark.py"]