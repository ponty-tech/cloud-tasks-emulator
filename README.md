# cloud-tasks-emulator

To configure poetry for GCP ```poetry config repositories.gcp https://europe-north1-python.pkg.dev/prs-next/ponty```

To build run ```poetry build```\
To deploy run ```poetry publish -r gcp```

# Release notes

## 1.0.7
Added support for more redis version and bumped ruff

## 1.0.8
Reverted to max 2.* for redis due to ZADD issue