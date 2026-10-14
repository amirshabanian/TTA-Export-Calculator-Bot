# GitHub Upload Guide (Persian)

1. Download and extract this ZIP on your computer.
2. Open your repository `amirshabanian/TTA-Export-Calculator-Bot`.
3. Before uploading, check the existing repository and back up anything important.
4. Upload the extracted **contents** to the repository root, not the enclosing folder.
5. If GitHub asks to replace `bot.py`, replace it only if you intend to publish this packaged 6.2.0-ORACLE code.
6. Never upload `.env`, `tta_bot.db`, logs, real customer PDFs, tokens, or private keys. `.gitignore` helps for Git users but does not prevent manual web uploads.
7. Commit message suggestion: `docs: publish v6.2.0 deployment guide and multilingual README`.
8. Open the Actions tab and confirm the Python tests workflow passes.
9. Railway and VPS do not update merely because GitHub files changed unless they are connected to auto-deploy. Follow `DEPLOYMENT.md` for each host.

Language switcher note: each language link opens a separate README file. GitHub does not automatically translate Markdown based on a visitor's GitHub UI language.

