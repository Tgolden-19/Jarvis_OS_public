import os
import asyncio
from commands.validators import NoteModel
import aiofiles
from pathlib import Path

NOTES_DIR = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTENSIONS = {".txt", ".rtf"}

DEBUG = True


async def list_notes():
    files = [f.name for f in NOTES_DIR.iterdir() if f.suffix in SUPPORTED_EXTENSIONS]
    if DEBUG:
        print("Available Notes:")
        for f in files:
            print(f"- {f}")
    return files


async def create_note(note:NoteModel):
    if not name.endswith(ext):
        name += ext
    filepath = NOTES_DIR / name
    async with aiofiles.open(filepath, mode="w", encoding="utf-8") as f:
        await f.write(content)
    if DEBUG:
        print(f"Note '{name}' created.")


async def read_note(note:NoteModel):
    filepath = NOTES_DIR / note.title
    if not filepath.exists():
        print("Note does not exist.")
        return
    async with aiofiles.open(filepath, mode="r", encoding="utf-8") as f:
        content = await f.read()
    if DEBUG:
        print(f"Contents of {note.title}:\n{content}")
    return content


async def update_note(note:NoteModel):
    filepath = NOTES_DIR / note.title
    if not filepath.exists():
        print("Note does not exist.")
        return
    async with aiofiles.open(filepath, mode="w", encoding="utf-8") as f:
        await f.write(note.content)
    if DEBUG:    
        print(f"Note '{note.title}' updated.")


async def delete_note(note:NoteModel):
    filepath = NOTES_DIR / note.title
    if filepath.exists():
        filepath.unlink()
        print(f"Note '{note.title}' deleted.")
    else:
        print("Note does not exist.")



