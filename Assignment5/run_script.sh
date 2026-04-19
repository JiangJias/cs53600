# docker build -t cs536-pytorch .

docker run --rm \
  -v "$(pwd)":/app \
  -w /app \
  --ipc=host \
  cs536-pytorch \
  python benchmark.py