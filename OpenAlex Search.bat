@echo off
title OpenAlex Search
cd /d D:\Apps\openalex-search

echo Starting OpenAlex Search...
uv run streamlit run app.py

pause
