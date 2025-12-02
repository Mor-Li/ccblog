#!/usr/bin/env python3
"""Convert SVG files to PNG for WeChat compatibility."""

import os
import subprocess
from pathlib import Path

def convert_svg_to_png_cairosvg(svg_path: Path, png_path: Path, width: int = 1200):
    """Convert SVG to PNG using cairosvg."""
    try:
        import cairosvg
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=width
        )
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"Error converting {svg_path}: {e}")
        return False

def convert_svg_to_png_pillow(svg_path: Path, png_path: Path, width: int = 1200):
    """Convert SVG to PNG using Pillow with svg2rlg."""
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM

        drawing = svg2rlg(str(svg_path))
        if drawing:
            # Scale to desired width while maintaining aspect ratio
            scale = width / drawing.width
            drawing.width = width
            drawing.height = drawing.height * scale
            drawing.scale(scale, scale)

            renderPM.drawToFile(drawing, str(png_path), fmt='PNG')
            return True
    except ImportError:
        return False
    except Exception as e:
        print(f"Error converting {svg_path}: {e}")
        return False

def main():
    blog_dir = Path("/home/limo/ccblog/blog/llm-nondeterminism")

    # Find all SVG files
    svg_files = list(blog_dir.glob("*.svg"))

    if not svg_files:
        print("No SVG files found")
        return

    print(f"Found {len(svg_files)} SVG files to convert")

    # Try different conversion methods
    success_count = 0

    for svg_file in svg_files:
        png_file = svg_file.with_suffix('.png')

        # Try cairosvg first (better quality)
        if convert_svg_to_png_cairosvg(svg_file, png_file):
            print(f"✓ Converted (cairosvg): {svg_file.name}")
            success_count += 1
        elif convert_svg_to_png_pillow(svg_file, png_file):
            print(f"✓ Converted (pillow): {svg_file.name}")
            success_count += 1
        else:
            print(f"✗ Failed: {svg_file.name}")

    print(f"\nConverted {success_count}/{len(svg_files)} files")

    # Update the markdown file to use .png instead of .svg
    md_file = blog_dir / "defeating-nondeterminism-in-llm-inference.md"
    if md_file.exists():
        content = md_file.read_text()
        updated_content = content.replace('.svg)', '.png)')
        md_file.write_text(updated_content)
        print(f"\n✓ Updated markdown file to reference .png files")

if __name__ == "__main__":
    main()
