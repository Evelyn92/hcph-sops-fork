# HCPh Project: Standard Operation Procedures (SOPs)

Generated from https://github.com/nipreps/SOPs-Cookiecutter

How to *see* these documents:

```
git clone https://github.com/TheAxonLab/hcph-sops.git
cd hcph-protocol
python -m pip install -r requirements.txt
mkdocs serve
```

If everything's fine, you should see the documentation rendered at https://localhost:8000.

If you want not to have *secrets* redacted, you will need to add the secrets repository (private) as a git submodule under the folder `secrets/`.

To export to PDF, execute:

```
mkdocs build
```
