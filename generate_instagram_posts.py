#!/usr/bin/env python3
"""
generate_instagram_posts.py
=================================

This script reads an Excel spreadsheet containing product details and
affiliate information and generates Instagram‑ready assets for each
product or grouped post. It can create single‑image or carousel posts
depending on the number of images provided. The script downloads
product images, crops or pads them to a square 1080×1080 format,
Generates a caption using a simple template, writes alt text for
accessibility, and outputs a meta JSON file for traceability.

Usage:
    python generate_instagram_posts.py --excel path/to/products.xlsx --out output_dir

Requirements:
    See requirements.txt for dependencies. Install with:
        pip install -r requirements.txt

Excel columns expected:
    product_id            Unique identifier for the product.
    title                 Product title.
    short_desc            Short description (used for alt text fallback).
    benefits_pipe         Pipe‑separated list of key benefits (e.g. "Long battery life|Water resistant").
    affiliate_url         Affiliate link for the product.
    image_urls_comma      Comma‑separated list of image URLs (max 10).
    post_type             "single", "carousel", "best_of", or "comparison" (only "single" and "carousel" are used here).
    post_group            Optional ID for grouped/comparison posts (not used in this version).
    price                 Optional price string to include in caption.
    rating                Optional rating (e.g. 4.5).
    review_count          Optional number of reviews.
    category              Optional product category.
    seo_keywords_comma    Optional comma‑separated keywords (not used in this version).
    hashtags_comma        Comma‑separated hashtags to append to caption.
    cta_override          Optional call‑to‑action override to replace default CTA.
    disclosure_override   Optional FTC disclosure override.
    alt_text_override     Optional alt text override for images.

Output:
    For each product row, the script creates a directory under
    --out with the product_id as the folder name. Inside each
    product directory:

    images/         Contains 1080×1080 JPG images downloaded and processed.
    caption.txt     Plain text caption ready to paste into Instagram.
    alt_text.txt    Alt text for images (first image only).
    meta.json       JSON metadata summarizing the generated assets.

This script is intended as a reference implementation for the
Instagram affiliate posts MVP. Customize the caption template or
extend grouping logic as needed.
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests
from PIL import Image, ImageOps


def slugify(value: str) -> str:
    """Simple slugify function: lowercases and replaces non‑alphanumeric chars with hyphens."""
    import re
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = value.strip('-')
    return value or 'post'


def square_image(image: Image.Image, size: int = 1080) -> Image.Image:
    """Resize and pad/crop an image to a square of the given size."""
    return ImageOps.fit(image, (size, size), Image.LANCZOS)


def generate_caption(row: pd.Series) -> str:
    """Generate a caption string from a product row."""
    lines: List[str] = []
    title = row.get('title', '')
    if title:
        lines.append(f"Check out {title}!")
    benefits = row.get('benefits_pipe', '')
    if isinstance(benefits, str) and benefits:
        for benefit in benefits.split('|'):
            benefit = benefit.strip()
            if benefit:
                lines.append(f"• {benefit}")
    price = row.get('price')
    rating = row.get('rating')
    review_count = row.get('review_count')
    if price and not pd.isna(price):
        lines.append(f"Price: {price}")
    if rating and not pd.isna(rating):
        rc_str = f" ({int(review_count)} reviews)" if review_count and not pd.isna(review_count) else ''
        lines.append(f"Rating: {rating}/5{rc_str}")
    cta_override = row.get('cta_override', '')
    if isinstance(cta_override, str) and cta_override:
        cta = cta_override
    else:
        affiliate_url = row.get('affiliate_url', '')
        cta = f"Learn more and buy here: {affiliate_url}" if affiliate_url else ''
    if cta:
        lines.append(cta)
    hashtags = row.get('hashtags_comma', '')
    if isinstance(hashtags, str) and hashtags:
        parts = [tag.strip() for tag in hashtags.split(',') if tag.strip()]
        if parts:
            lines.append(' '.join(part if part.startswith('#') else f"#{part}" for part in parts))
    disclosure = row.get('disclosure_override', '')
    if not (isinstance(disclosure, str) and disclosure):
        disclosure = "As an Amazon Associate I earn from qualifying purchases."
    lines.append(disclosure)
    return '\n'.join(lines)


def generate_alt_text(row: pd.Series) -> str:
    alt_override = row.get('alt_text_override', '')
    if isinstance(alt_override, str) and alt_override:
        return alt_override
    title = row.get('title', '') or 'product'
    desc = row.get('short_desc', '')
    if isinstance(desc, str) and desc:
        desc = desc.strip().split('.')[0]
    else:
        desc = ''
    return f"Image of {title}. {desc}".strip()


def process_product(row: pd.Series, out_dir: Path) -> None:
    product_id = str(row.get('product_id') or slugify(row.get('title', 'post')))
    product_slug = slugify(product_id)
    prod_path = out_dir / product_slug
    images_path = prod_path / 'images'
    images_path.mkdir(parents=True, exist_ok=True)
    # Download images
    image_urls = []
    imgs_field = row.get('image_urls_comma', '')
    if isinstance(imgs_field, str) and imgs_field:
        image_urls = [u.strip() for u in imgs_field.split(',') if u.strip()]
    downloaded_files = []
    for i, url in enumerate(image_urls):
        if i >= 10:
            break
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            img_sq = square_image(img)
            fname = f"image_{i+1}.jpg"
            fpath = images_path / fname
            img_sq.save(fpath, format='JPEG', quality=90)
            downloaded_files.append(str(fpath.name))
        except Exception:
            continue
    # Write caption
    caption = generate_caption(row)
    with open(prod_path / 'caption.txt', 'w', encoding='utf-8') as f:
        f.write(caption)
    # Write alt text
    alt_text = generate_alt_text(row)
    with open(prod_path / 'alt_text.txt', 'w', encoding='utf-8') as f:
        f.write(alt_text)
    # Write meta.json
    meta = {
        'product_id': product_id,
        'title': row.get('title'),
        'post_type': row.get('post_type'),
        'images': downloaded_files,
        'caption_file': 'caption.txt',
        'alt_text_file': 'alt_text.txt',
        'affiliate_url': row.get('affiliate_url'),
    }
    with open(prod_path / 'meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Generate Instagram posts from product Excel file.')
    parser.add_argument('--excel', required=True, help='Path to the Excel file with product data')
    parser.add_argument('--out', required=True, help='Output directory for generated posts')
    args = parser.parse_args()
    excel_path = Path(args.excel)
    out_path = Path(args.out)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file {excel_path} does not exist")
    out_path.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(excel_path)
    for _, row in df.iterrows():
        process_product(row, out_path)


if __name__ == '__main__':
    from io import BytesIO
    import pandas
    main()
