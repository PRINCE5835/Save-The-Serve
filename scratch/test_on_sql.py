import os
import sys

sys.path.append(r"C:\Users\princ\.gemini\antigravity-ide\brain\ab097620-1bf2-48b8-939b-9829fcb88188\scratch")
from refactor_comments import clean_sql

path = r"c:\Users\princ\OneDrive\Documents\Desktop\Save The Serve\supabase\seed.sql"
with open(path, "r", encoding="utf-8") as f:
    orig = f.read()

res = clean_sql(orig)
print("Original length:", len(orig))
print("Cleaned length:", len(res))
print("Contains '-- 1. Create Mock':", "-- 1. Create Mock" in res)
print("\nCleaned content:")
print(res)
