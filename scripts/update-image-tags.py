"""Update the immutable image tag in the staging overlay during CI."""
from pathlib import Path
import os

tag = os.environ.get("IMAGE_TAG")
if not tag:
    raise SystemExit("IMAGE_TAG is required")
path = Path("gitops/overlays/staging/kustomization.yaml")
text = path.read_text()
path.write_text(text.replace("newTag: IMAGE_TAG", f"newTag: {tag}"))
