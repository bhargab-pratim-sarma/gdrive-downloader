#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM Preparation Script
Consolidates and cleans course materials, extracting subtitles into a single markdown file per course.
"""

import os
import re
import shutil
from pathlib import Path
from tqdm import tqdm
import textwrap

# --- Configuration ────────────────────────────────────────────────────────────
BASE_DIR = Path("/home/bhargavxharma/DATABASE/Atmanova/EBOOK")
SOURCE_DIR = BASE_DIR / "COLLECTION"
OUTPUT_DIR = BASE_DIR / "notebook-lm-ready"

# Supported extensions by NotebookLM
SUPPORTED_DOCS = {".pdf", ".txt", ".md", ".docx", ".csv", ".pptx", ".epub"}
SUPPORTED_IMAGES = {
    ".avif", ".bmp", ".gif", ".ico", ".jp2", ".png", ".webp", 
    ".tif", ".tiff", ".heic", ".heif", ".jpeg", ".jpg", ".jpe"
}
# Note: Media is supported but typically excluded to save space since we extract transcripts
SUPPORTED_MEDIA = {
    ".3g2", ".3gp", ".aac", ".aif", ".aifc", ".aiff", ".amr", ".au", ".avi", 
    ".cda", ".m4a", ".mid", ".mp3", ".mp4", ".mpeg", ".ogg", ".opus", ".ra", 
    ".ram", ".snd", ".wav", ".wma"
}

# Toggles for what to copy into the ready folder
COPY_DOCS = True
COPY_IMAGES = False
COPY_MEDIA = False  # Keep false to rely purely on the text transcripts

# Irrelevant files to ignore
IGNORE_FILENAMES = {
    "bonus resources.txt",
    "get bonus downloads here.url",
    "join for free ebooks [freepaidbooks.online].txt",
    "[tgx]downloaded from torrentgalaxy.to .txt",
    "1337x status.url",
    "note.txt",
    "_ uploads will cease (your support needed - urgent - goal).txt",
    "1. downloaded from 1337x.txt",
    "2. downloaded from torrentgalaxy.txt",
    "3. downloaded from the pirate bay.txt",
    "4. downloaded from demonoid.txt",
    "get latest books & magazines.html",
    "get more books & magazines.....txt"
}

IGNORE_PREFIXES = ("get bonus", "bonus resources", "downloaded from")
IGNORE_EXTENSIONS = {".url", ".part"}

# Colors for terminal output
class C:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    DIM = '\033[2m'
    RESET = '\033[0m'

def clr(text, color):
    return f"{color}{text}{C.RESET}"

def is_ignored(filename):
    lower_name = filename.lower()
    if lower_name in IGNORE_FILENAMES:
        return True
    if any(lower_name.startswith(p) for p in IGNORE_PREFIXES):
        return True
    if Path(filename).suffix.lower() in IGNORE_EXTENSIONS:
        return True
    return False

def clean_subtitle_text(filepath):
    """
    Parses .srt or .vtt file, removes timestamps, line numbers, and HTML tags.
    Consolidates text into readable paragraphs.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()

    lines = content.split('\n')
    cleaned_lines = []
    
    # Matches SRT (00:00:00,000 -->) and VTT (00:00.000 -->)
    timestamp_pattern = re.compile(r'\d{2}:\d{2}.*-->.*\d{2}:\d{2}')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.upper() == "WEBVTT":
            continue
        if line.isdigit():
            continue
        if timestamp_pattern.search(line):
            continue
            
        # Strip HTML-like tags (e.g., <font color="...">, <i>)
        line = re.sub(r'<[^>]+>', '', line)
        cleaned_lines.append(line)
        
    text = " ".join(cleaned_lines)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Organize into paragraphs for better readability in NotebookLM
    # Split by sentence endings (.!?)
    sentences = re.split(r'(?<=[.!?]) +', text)
    
    paragraphs = []
    current_para = []
    
    for s in sentences:
        current_para.append(s)
        # Create a paragraph every ~6 sentences
        if len(current_para) >= 6:
            paragraphs.append(" ".join(current_para))
            current_para = []
            
    if current_para:
        paragraphs.append(" ".join(current_para))
        
    return "\n\n".join(paragraphs)

def format_course_name(name):
    # Strip common bracket prefixes like "[ CourseMega.com ]" to make names cleaner
    return re.sub(r'^\[.*?\]\s*', '', name).strip()

def process_course(course_dir):
    clean_name = format_course_name(course_dir.name)
    output_course_dir = OUTPUT_DIR / clean_name
    output_course_dir.mkdir(parents=True, exist_ok=True)
    
    merged_md_path = output_course_dir / f"{clean_name}.md"
    
    subtitles = []
    other_files = []
    
    # Traverse and categorize files
    for root, _, files in os.walk(course_dir):
        for file in files:
            if is_ignored(file):
                continue
                
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            if ext in {".srt", ".vtt"}:
                subtitles.append(file_path)
            elif ext in SUPPORTED_DOCS and COPY_DOCS:
                other_files.append(file_path)
            elif ext in SUPPORTED_IMAGES and COPY_IMAGES:
                other_files.append(file_path)
            elif ext in SUPPORTED_MEDIA and COPY_MEDIA:
                other_files.append(file_path)
                
    # Sort subtitles by path to maintain logical episodic flow
    subtitles.sort()
    
    # Write the consolidated markdown file
    with open(merged_md_path, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# {clean_name}\n\n")
        
        if subtitles:
            md_file.write("## Video Transcripts\n\n")
            for sub_file in subtitles:
                # Use the relative path to create a meaningful section heading
                rel_path = sub_file.relative_to(course_dir)
                heading = str(rel_path.with_suffix('')).replace('/', ' - ')
                
                md_file.write(f"### {heading}\n\n")
                cleaned_text = clean_subtitle_text(sub_file)
                if cleaned_text:
                    md_file.write(f"{cleaned_text}\n\n")
                else:
                    md_file.write("_Transcript is empty._\n\n")
        else:
            md_file.write("_No subtitle transcripts available for this directory._\n\n")
            
    # Copy other supported files (Hardlink to save space, fallback to copy)
    for src_file in other_files:
        dest_file = output_course_dir / src_file.name
        
        # Handle filename collisions by prepending parent folder name
        if dest_file.exists():
            dest_file = output_course_dir / f"{src_file.parent.name} - {src_file.name}"
            
        try:
            # Try hardlink first (fast, uses 0 extra disk space)
            os.link(src_file, dest_file)
        except FileExistsError:
            pass  # Already linked
        except OSError:
            # Fallback to standard copy if on different drives/filesystems
            shutil.copy2(src_file, dest_file)

def main():
    print(clr("\n  NotebookLM Dataset Preparer", C.CYAN))
    print(clr("  ───────────────────────────\n", C.DIM))
    
    if not SOURCE_DIR.exists():
        print(clr(f"❌ Source directory not found: {SOURCE_DIR}", C.RED))
        return
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all top-level directories in COLLECTION (these are our "parents")
    courses = [d for d in SOURCE_DIR.iterdir() if d.is_dir()]
    
    if not courses:
        print(clr("⚠️  No course directories found.", C.YELLOW))
        return
        
    print(clr(f"ℹ️  Found {len(courses)} courses to process.", C.CYAN))
    print(clr(f"ℹ️  Output directory: {OUTPUT_DIR}\n", C.CYAN))
    
    for course in tqdm(courses, desc="Processing Courses", bar_format="{l_bar}%s{bar}%s{r_bar}" % (C.GREEN, C.RESET)):
        process_course(course)
        
    print(clr("\n✅  All datasets prepared successfully!", C.GREEN))
    print(clr(f"📂  Ready for ingestion at: {OUTPUT_DIR}\n", C.GREEN))

if __name__ == "__main__":
    main()
