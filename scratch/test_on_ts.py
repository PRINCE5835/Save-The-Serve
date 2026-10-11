import os
import sys

sys.path.append(r"C:\Users\princ\.gemini\antigravity-ide\brain\ab097620-1bf2-48b8-939b-9829fcb88188\scratch")
from refactor_comments import clean_js_ts

path = r"c:\Users\princ\OneDrive\Documents\Desktop\Save The Serve\frontend\src\context\AuthContext.tsx"
with open(path, "r", encoding="utf-8") as f:
    orig = f.read()

res = clean_js_ts(orig, path)
print("Original length:", len(orig))
print("Cleaned length:", len(res))
print("Contains '// default to Donor demo':", "// default to Donor demo" in res)
print("Contains Unsplash URL:", "https://images.unsplash.com" in res)
print("\nFirst 40 lines of cleaned:")
print("\n".join(res.splitlines()[:40]))
