[phases.setup]
nixPkgs = ["python39", "pip", "gunicorn"]

[phases.build]
cmds = ["pip install -r requirements.txt"]

[phases.start]
cmds = ["gunicorn app:app --bind 0.0.0.0:$PORT"]
