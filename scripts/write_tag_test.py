"""Write test workflow to verify tag trigger"""
content = """name: Test Tag
on:
  push:
    tags:
      - 'v*'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Tag workflow triggered by ${{ github.event_name }}"
      - run: echo "Ref: ${{ github.ref_name }}"
"""
import pathlib
pathlib.Path(".github/workflows/test_tag.yml").write_text(content)
print("Written test_tag.yml")
