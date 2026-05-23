# Batch Generation From File

## Batch Generation from File

```yaml
# .github/workflows/batch-generate.yml
name: Batch Video Generation

on:
  workflow_dispatch:
    inputs:
      prompts_file:
        description: 'Path to prompts JSON file'
        required: true
        default: 'prompts/weekly-content.json'

jobs:
  generate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include: ${{ fromJson(needs.load-prompts.outputs.prompts) }}
      max-parallel: 5

    steps:
      - uses: actions/checkout@v4

      - name: Generate video
        env:
          KLINGAI_API_KEY: ${{ secrets.KLINGAI_API_KEY }}
        run: |
          python scripts/generate_video.py \
            --prompt "${{ matrix.prompt }}" \
            --duration ${{ matrix.duration }} \
            --model "${{ matrix.model }}" \
            --output-json "results/${{ matrix.id }}.json"

      - uses: actions/upload-artifact@v4
        with:
          name: video-${{ matrix.id }}
          path: results/${{ matrix.id }}.json

  load-prompts:
    runs-on: ubuntu-latest
    outputs:
      prompts: ${{ steps.load.outputs.prompts }}
    steps:
      - uses: actions/checkout@v4
      - id: load
        run: |
          echo "prompts=$(cat ${{ inputs.prompts_file }})" >> $GITHUB_OUTPUT
```
