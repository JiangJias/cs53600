docker run --rm \
  -v "$(pwd)":/app \
  -v "$(pwd)/gurobi.lic":/opt/gurobi/gurobi.lic:ro \
  -e GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic \
  -w /app \
  gurobi/python:latest \
  python main.py