#!/bin/bash

# Clean up empty agent directories
# This is a STRUCTURAL ENHANCEMENT, not a compliance fix

echo "============================================"
echo "CLEANING UP EMPTY DIRECTORIES"
echo "============================================"
echo ""
echo "Note: Empty directories are compliant - this improves clarity"
echo ""

# Track changes
removed=0
kept=0

# Find all agents directories
for agents_dir in $(find ./plugins -type d -name "agents" 2>/dev/null); do
    plugin_name=$(echo "$agents_dir" | cut -d'/' -f3-4)

    # Check if directory is empty or only has non-.md files
    md_count=$(find "$agents_dir" -name "*.md" 2>/dev/null | wc -l)

    if [[ $md_count -eq 0 ]]; then
        # Check if directory is completely empty
        if [ -z "$(ls -A "$agents_dir" 2>/dev/null)" ]; then
            echo "Found empty directory: $agents_dir"
            echo -n "  Remove? (y/n): "
            read -r response

            if [[ "$response" == "y" ]]; then
                rmdir "$agents_dir"
                echo "  ✓ Removed"
                ((removed++))
            else
                echo "  ⊗ Kept"
                ((kept++))
            fi
        else
            echo "Found agents/ with no .md files: $agents_dir"
            echo "  Contains: $(ls "$agents_dir" | tr '\n' ' ')"
            echo "  ⊗ Keeping (has other files)"
            ((kept++))
        fi
    fi
done

# Also check for other empty component directories
echo ""
echo "Checking for other empty directories..."

for dir_type in hooks scripts mcp; do
    for empty_dir in $(find ./plugins -type d -name "$dir_type" -empty 2>/dev/null); do
        echo "Found empty $dir_type directory: $empty_dir"
        echo -n "  Remove? (y/n): "
        read -r response

        if [[ "$response" == "y" ]]; then
            rmdir "$empty_dir"
            echo "  ✓ Removed"
            ((removed++))
        else
            echo "  ⊗ Kept"
            ((kept++))
        fi
    done
done

echo ""
echo "Summary:"
echo "  Directories removed: $removed"
echo "  Directories kept: $kept"
echo ""
echo "Note: Removed directories can be restored with git checkout if needed"