#!/bin/bash

source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate agents-mas
(sleep 3 && open http://localhost:8765) &
PYTHONWARNINGS="ignore::UserWarning" solara run viz_app.py
