# artsemfab Website

One-page site for Artsemfab: custom roll cages, scanned and designed for each car before they are built. Styled as a fabrication drawing: paper grid, dimension lines and title blocks.

## Edit your content

- All text is in `index.html`, in page order: hero, Process (scan, design, build), Work, About, Request a build, footer title block.
- **Instagram:** the block at the end of Work links to `https://www.instagram.com/artsemfab/` (the `.instagram` link); change the URL and the `See @artsemfab` button text if the handle differs.
- **Build requests** go to `artsemfab@gmail.com` through FormSubmit (the `action` on `#contact-form`). The first submission sends a confirmation email to that address, which has to be clicked once before requests arrive.
- **Colours and fonts** are the tokens at the top of `styles.css`.

## Images

The page only loads the web-sized copies in `assets/web/`. The originals in `assets/` stay as the full-resolution source.

To add a photo, make a web copy (about 1400–1800px on the long edge) and reference that:

```bash
sips -s format jpeg -s formatOptions 78 -Z 1600 "assets/New Build.jpg" --out assets/web/new-build.jpg
```

Give 3D renders on a white background `class="render"`: they are multiplied onto the paper, so the white disappears and the model sits on the sheet. Photos go without it.

A Work entry is one `<article class="sheet">` with the image and a `title-block` (Chassis, Scope); copy an existing one.

## Run locally

```bash
python3 -m http.server 8090
```

Then open http://localhost:8090.

## Deploy to Cloudflare Pages (free)

1. Create a GitHub repo and push these files.
2. In Cloudflare dashboard, go to **Workers & Pages** -> **Create application** -> **Pages**.
3. Connect your GitHub repo.
4. Build settings:
   - Framework preset: `None`
   - Build command: (leave empty)
   - Build output directory: `/`
5. Deploy.

Your site will get a free `*.pages.dev` URL, and you can connect a custom domain later.
