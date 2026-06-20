"""Write minimal CI/CD workflow to .github/workflows/"""
content = """name: Deploy a QAS
on:
  push:
    tags:
      - 'v*-qas'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "CI/CD works for tag ${{ github.ref_name }}"
      - run: echo "Trigger: ${{ github.event_name }}"
"""
import pathlib
pathlib.Path(".github/workflows/deploy-qas.yml").write_text(content)
print("Written OK")
