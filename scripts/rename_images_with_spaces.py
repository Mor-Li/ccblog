#!/usr/bin/env python3
"""
Rename image files with spaces in their names and update Markdown references.
"""
import os
import re
from pathlib import Path

def rename_files_with_spaces(directory):
    """Rename all files with spaces in the directory."""
    directory = Path(directory)
    renamed_files = {}

    for file in directory.glob("*"):
        if file.is_file() and " " in file.name:
            new_name = file.name.replace(" ", "_")
            new_path = file.parent / new_name

            print(f"Renaming: {file.name}")
            print(f"      to: {new_name}")

            file.rename(new_path)
            renamed_files[file.name] = new_name

    return renamed_files

def update_markdown_references(md_file, renamed_files):
    """Update image references in Markdown file."""
    md_path = Path(md_file)

    if not md_path.exists():
        print(f"Markdown file not found: {md_file}")
        return

    content = md_path.read_text(encoding='utf-8')
    original_content = content

    # Update references for each renamed file
    for old_name, new_name in renamed_files.items():
        # Handle both ./ prefix and without
        content = content.replace(f"./{old_name}", f"./{new_name}")
        content = content.replace(old_name, new_name)

    if content != original_content:
        md_path.write_text(content, encoding='utf-8')
        print(f"\nUpdated Markdown file: {md_file}")
        print(f"Replaced {len(renamed_files)} image references")
    else:
        print(f"\nNo changes needed in Markdown file")

if __name__ == "__main__":
    blog_dir = "/home/limo/ccblog/blog/streamingllm"
    md_file = f"{blog_dir}/streamingllm_wechat.md"

    print("=== Renaming files with spaces ===")
    renamed = rename_files_with_spaces(blog_dir)

    if renamed:
        print(f"\n=== Updating Markdown references ===")
        update_markdown_references(md_file, renamed)
        print(f"\n✓ Done! Renamed {len(renamed)} files")
    else:
        print("\n✓ No files with spaces found")
