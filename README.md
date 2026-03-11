# pa-newsroom-rss
Repo for creating, hosting, and updating an PA Newsroom RSS-feed. 

Mål: Denna sida publicerar RSS‑filen här:

[https://konto.github.io/repo/feed.xml] (exempel: https://alberthberg.github.io/pa-newsroom-rss/feed.xml)

Gör så här om allt måste återskapas:

Skapa nytt tomt GitHub-repo.

Ladda upp alla fyra filer/mappar:

1. generate_feed.py

2. feed.xml

3. README.md

4. hela mappen .github/workflows/ (med filen update.yml)


Gå till Settings → Pages

Build and deployment → Source: Deploy from a branch

Branch: main och Folder: / (root) → Save


Gå till Actions → öppna workflow “Update RSS feed” → Run workflow.

Vänta ~1–2 minuter och öppna länken med strukturen https://konto.github.io/repo/feed.xml. 
Din faktiska länk beror alltså på vad ditt kontonamn är och vad du döpt repot till.
