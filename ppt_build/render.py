# -*- coding: utf-8 -*-
"""Render deck slides to PNG via PowerPoint COM for visual QA."""
import os, sys
try:
    import win32com.client
except ImportError:
    os.system("pip install pywin32 --quiet")
    import win32com.client

DECK = r"C:\Users\USER\Downloads\FarmShield_AAA09_Hackwell2_0_v3.pptx"
OUTDIR = os.path.abspath("render")
os.makedirs(OUTDIR, exist_ok=True)

app = win32com.client.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(DECK, ReadOnly=True, WithWindow=False)
pres.SaveAs(OUTDIR, 18)  # ppSaveAsPNG
pres.Close()
app.Quit()
print("rendered to", OUTDIR)
for f in sorted(os.listdir(OUTDIR)):
    print(" ", f)
