"""
Run this if embeddings fail with a 404 "model not found" error or a
dimension mismatch. It lists which embedding models your Gemini API key
actually has access to.

Usage:
    export GOOGLE_API_KEY=your_real_key
    python3 list_models.py
"""
import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))

print("Models supporting embedContent for your Gemini API key:\n")
for m in genai.list_models():
    if "embedContent" in m.supported_generation_methods:
        print(f"  {m.name}")

print("\nSet EMBEDDING_MODEL in your .env to whichever name is listed above.")
print("Note: this doesn't show the output dimension directly - if you change")
print("EMBEDDING_MODEL, you may need to try a value for EMBEDDING_DIM and")
print("adjust based on the dimension-mismatch error message (it states")
print("both the expected and actual dimension).")
