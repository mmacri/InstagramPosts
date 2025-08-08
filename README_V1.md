# Instagram Affiliate Post Generator (V1)

This repository contains a simple script and template for generating Instagram‑ready assets from a spreadsheet of products with affiliate links.

## Contents

- **instagramposts_v1.xlsx** – example Excel template with transformed product data. Use this as a starting point and add your own rows.
- **generate_instagram_posts.py** – Python script that reads the Excel file and produces assets for each product.
- **requirements.txt** – list of Python dependencies.

## How to use

1. **Install dependencies** (recommended in a virtual environment):
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

2. **Prepare your Excel** based on `instagramposts_v1.xlsx`:
   - Each row represents one product.
   - Columns:
     - `product_id`: unique identifier (used for folder names).
     - `title`: product title.
     - `short_desc`: short description (first sentence used for alt text if no override).
     - `benefits_pipe`: pipe‐separated list of benefits (e.g., `Easy to use|Compact size|Long battery life`).
     - `affiliate_url`: full affiliate link (including your tag).
     - `image_urls_comma`: comma‐separated list of image URLs (max 10).
     - `post_type`: `single` or `carousel` (other values ignored).
     - `post_group`: optional grouping ID (not used in this version).
     - `price`, `rating`, `review_count`, `category`: optional fields used in the caption.
     - `seo_keywords_comma`, `hashtags_comma`: optional keywords and hashtags.
     - `cta_override`: optional call‐to‐action override.
     - `disclosure_override`: optional FTC disclosure override.
     - `alt_text_override`: optional alt text override.

3. **Run the generator**:
   ```bash
   python generate_instagram_posts.py --excel your_products.xlsx --out output_directory
   ```
   - A folder is created for each product in `output_directory`.
   - Inside each folder:
     - `images/` – 1080×1080 JPG images downloaded and prepared.
     - `caption.txt` – caption for Instagram.
     - `alt_text.txt` – accessibility description.
     - `meta.json` – metadata summarizing the assets.

4. **Post manually**:
   - Copy the images to your phone or computer.
   - Paste the caption from `caption.txt` when creating an Instagram post.
   - Use `alt_text.txt` as the alt text.

## Notes

- This script is a minimal MVP for individual and carousel posts. Multi‑product comparison posts (`best_of` and `comparison`) are not yet implemented.
- The script will skip images that fail to download or process.
- If no hashtags are provided, none will be added.
