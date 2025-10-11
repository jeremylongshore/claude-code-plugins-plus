#!/bin/bash

# Script to remove emojis from all markdown and other text files
# PROFESSIONAL CLAUDE CODE MARKETPLACE - NO EMOJIS

echo "=== EMOJI REMOVAL SCRIPT ==="
echo "Removing all emojis for professional presentation"
echo ""

# Counter for tracking
TOTAL_FILES=0
MODIFIED_FILES=0

# Function to remove emojis from a file
remove_emojis() {
    local file="$1"

    # Create a backup
    cp "$file" "$file.bak"

    # Remove common emojis and emoji unicode ranges
    # This sed command removes most common emojis
    sed -i 's/[🌀-🏿]//g' "$file"
    sed -i 's/[😀-🙏]//g' "$file"
    sed -i 's/[🚀-🛿]//g' "$file"
    sed -i 's/[🌍-🌿]//g' "$file"
    sed -i 's/[🍀-🍿]//g' "$file"
    sed -i 's/[🎀-🏿]//g' "$file"
    sed -i 's/[🐀-🐿]//g' "$file"
    sed -i 's/[👀-👿]//g' "$file"
    sed -i 's/[💀-💿]//g' "$file"
    sed -i 's/[🔀-🔿]//g' "$file"
    sed -i 's/[🕀-🕿]//g' "$file"
    sed -i 's/[🖀-🖿]//g' "$file"
    sed -i 's/[🗀-🗿]//g' "$file"
    sed -i 's/[🤀-🤿]//g' "$file"
    sed -i 's/[🥀-🥿]//g' "$file"
    sed -i 's/[🦀-🦿]//g' "$file"
    sed -i 's/[🧀-🧿]//g' "$file"
    sed -i 's/[🨀-🩿]//g' "$file"
    sed -i 's/[🪀-🪿]//g' "$file"
    sed -i 's/[🫀-🫿]//g' "$file"
    sed -i 's/[☀-⛿]//g' "$file"
    sed -i 's/[✀-➿]//g' "$file"
    sed -i 's/[⬀-⬿]//g' "$file"
    sed -i 's/[⭐-⭿]//g' "$file"

    # Check if file was modified
    if ! cmp -s "$file" "$file.bak"; then
        MODIFIED_FILES=$((MODIFIED_FILES + 1))
        echo "  [CLEANED] $file"
        rm "$file.bak"
    else
        rm "$file.bak"
    fi

    TOTAL_FILES=$((TOTAL_FILES + 1))
}

# Process all markdown files
echo "Processing markdown files..."
while IFS= read -r file; do
    remove_emojis "$file"
done < <(find /home/jeremy/projects/claude-code-plugins -name "*.md" -type f)

# Process all Astro files
echo ""
echo "Processing Astro files..."
while IFS= read -r file; do
    remove_emojis "$file"
done < <(find /home/jeremy/projects/claude-code-plugins/marketplace -name "*.astro" -type f)

# Process all TypeScript/JavaScript files
echo ""
echo "Processing TypeScript/JavaScript files..."
while IFS= read -r file; do
    remove_emojis "$file"
done < <(find /home/jeremy/projects/claude-code-plugins -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -type f)

echo ""
echo "=== EMOJI REMOVAL COMPLETE ==="
echo "Total files processed: $TOTAL_FILES"
echo "Files modified: $MODIFIED_FILES"
echo ""
echo "Repository is now emoji-free and professional."