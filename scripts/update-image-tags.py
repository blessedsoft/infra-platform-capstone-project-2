"""Update the immutable image tag in the staging overlay during CI."""
from pathlib import Path
import os
import re

tag = os.environ.get("IMAGE_TAG")
if not tag:
    raise SystemExit("IMAGE_TAG is required")
path = Path("gitops/overlays/staging/kustomization.yaml")
text = path.read_text()
updated = re.sub(r"(\bnewTag:\s*)\S+", rf"\g<1>{tag}", text)
path.write_text(updated)
