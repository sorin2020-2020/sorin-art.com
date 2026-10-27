# Sorin Angeleanu — portfolio

A plain static website: HTML, one CSS file, one small JavaScript file. No build step, no frameworks, nothing to install.

## View it offline

Open `index.html` in any browser (double-click it). Everything works offline except the YouTube videos and the video thumbnails, which need an internet connection.

## Publish on GitHub Pages (free)

1. Create a new **public** repository on GitHub, for example `portfolio`.
2. Upload everything in this folder to the repository root (drag the files into "Add file → Upload files", or use GitHub Desktop). Keep the `.nojekyll` file.
3. In the repository go to **Settings → Pages**. Under "Build and deployment" choose **Deploy from a branch**, branch **main**, folder **/ (root)**, then **Save**.
4. After a minute GitHub starts building the site. Because of the `CNAME` file it will be served at https://sorin-art.com once the DNS records below are in place.

## Your domain: sorin-art.com

The `CNAME` file in this folder already tells GitHub Pages to serve the site on `sorin-art.com`.

1. After uploading, open **Settings → Pages** and check that **Custom domain** shows `sorin-art.com` (type it in and save if it is empty).
2. At the company where you rent the domain, open the DNS settings and add:
   - four **A** records for `@` (the bare domain): `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - one **CNAME** record for `www` pointing to `<your-github-username>.github.io`
   - remove any old A or CNAME records that point to Cargo.
3. DNS can take from a few minutes to a day. When GitHub shows the DNS check as successful, tick **Enforce HTTPS**.

## Editing

- Text and projects live in `_build/content.py`; run `python3 _build/build.py` to regenerate the pages. See `_build/UPDATING.md`.
- Images are in `assets/img/`. Each image has a large version (`-l.jpg`, max 1800 px) and a medium one (`-m.jpg`, max 900 px).
- Colours and type are set at the top of `assets/css/style.css`.

Font: Archivo by Omnibus-Type, SIL Open Font License (see `assets/fonts/OFL.txt`).
