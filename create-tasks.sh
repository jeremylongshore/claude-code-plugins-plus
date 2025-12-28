#!/bin/bash
# Create all beads tasks for interactive lab

EPIC="claude-code-plugins-pvx"

# Phase 1: Colab Notebooks (9 tasks)
bd create "Phase 1.1: Environment setup for Jupyter notebooks" -p 1 --parent "$EPIC" --description "Install jupytext, nbformat, ipykernel. Create notebooks/ directory. Set up conversion workflow. Estimated: 30min"

bd create "Phase 1.2: Convert GUIDE-00 to interactive notebook" -p 1 --parent "$EPIC" --description "Convert Mental Model guide to .ipynb. Add interactive code cells, Try it yourself prompts. Test in Colab. Estimated: 1hr"

bd create "Phase 1.3: Convert ORCHESTRATION-PATTERN to notebook" -p 1 --parent "$EPIC" --description "Convert main reference guide to .ipynb (915 lines). Add executable examples for each section. Interactive phase contract builder. Verification script demo. Estimated: 2hrs"

bd create "Phase 1.4: Convert GUIDE-01 to interactive notebook" -p 1 --parent "$EPIC" --description "Convert Architecture guide to .ipynb. Add context budget calculator (interactive). Visualize phase flow with diagrams. Estimated: 1hr"

bd create "Phase 1.5: Convert GUIDE-02 to interactive notebook" -p 1 --parent "$EPIC" --description "Convert Build Your Own guide to .ipynb. Add workflow template generator. Interactive decision tree. Estimated: 1hr"

bd create "Phase 1.6: Convert GUIDE-03 to interactive notebook" -p 1 --parent "$EPIC" --description "Convert Debugging guide to .ipynb. Add runnable debugging examples. Interactive troubleshooting wizard. Estimated: 1hr"

bd create "Phase 1.7: Update README with Colab badges" -p 1 --parent "$EPIC" --description "Add Open in Colab badges for all 5 notebooks. Update Learning Lab section. Add Interactive Version callout. Estimated: 30min"

bd create "Phase 1.8: Test and validate all notebooks" -p 1 --parent "$EPIC" --description "Open each notebook in Colab. Run all cells end-to-end. Verify no errors. Test on fresh Google account. Estimated: 1hr"

bd create "Phase 1.9: Create v4.1.0 release (Colab notebooks)" -p 1 --parent "$EPIC" --description "Merge feature/interactive-colab to main. Update 000-docs/247-OD-CHNG-changelog.md (v4.1.0). Tag and release. Estimated: 30min"

# Phase 2: GitHub Codespaces (6 tasks)
bd create "Phase 2.1: Create devcontainer configuration" -p 2 --parent "$EPIC" --description "Create .devcontainer/devcontainer.json. Configure Ubuntu base image. Install bash, jq, git. Estimated: 30min"

bd create "Phase 2.2: Add workspace configuration" -p 2 --parent "$EPIC" --description "Configure VS Code extensions. Set up integrated terminal. Add welcome message with instructions. Estimated: 30min"

bd create "Phase 2.3: Create Codespaces getting started guide" -p 2 --parent "$EPIC" --description "Add CODESPACES.md with instructions. Quick start commands. How to run 5-phase workflow. Estimated: 30min"

bd create "Phase 2.4: Add Codespaces badge to README" -p 2 --parent "$EPIC" --description "Add Open in GitHub Codespaces badge. Update docs to mention both options (Colab + Codespaces). Estimated: 15min"

bd create "Phase 2.5: Test Codespaces environment" -p 2 --parent "$EPIC" --description "Launch fresh Codespace. Run through entire workflow. Verify all scripts executable. Estimated: 30min"

bd create "Phase 2.6: Create v4.2.0 release (Codespaces)" -p 2 --parent "$EPIC" --description "Merge feature/codespaces-env to main. Update 000-docs/247-OD-CHNG-changelog.md (v4.2.0). Tag and release. Estimated: 30min"

# Phase 3: Advanced Features (6 tasks)
bd create "Phase 3.1: Create Streamlit demo app" -p 3 --parent "$EPIC" --description "Build interactive workflow visualizer. Show phase execution in real-time. Live report generation. Estimated: 4hrs"

bd create "Phase 3.2: Add video walkthroughs" -p 3 --parent "$EPIC" --description "Record 5-min intro video. Embed in notebooks. Add to README. Estimated: 3hrs"

bd create "Phase 3.3: Claude API integration examples" -p 3 --parent "$EPIC" --description "Add live API call examples in notebooks. Show actual agent spawning. Demonstrate verification pattern. Estimated: 2hrs"

bd create "Phase 3.4: Create interactive decision tree" -p 3 --parent "$EPIC" --description "Build Which workflow pattern fits my use case? questionnaire. Web-based. Generates starter template. Estimated: 3hrs"

bd create "Phase 3.5: Build Observable notebooks" -p 3 --parent "$EPIC" --description "Create visual architecture explorer. Interactive diagrams. Publish to Observable. Estimated: 4hrs"

bd create "Phase 3.6: Create v4.3.0 release (Advanced features)" -p 3 --parent "$EPIC" --description "Merge feature/advanced-interactive to main. Update 000-docs/247-OD-CHNG-changelog.md (v4.3.0). Tag and release. Estimated: 30min"

echo "✅ All tasks created!"
