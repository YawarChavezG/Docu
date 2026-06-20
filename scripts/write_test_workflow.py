"""Write minimal test workflow - trigger on push to main"""
content = """name: Test Basic
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Workflow triggered by ${{ github.event_name }} on ${{ github.ref_name }}"
      - run: uname -a
"""
import pathlib
pathlib.Path(".github/workflows/test_basic.yml").write_text(content)
print("Written: test_basic.yml")
