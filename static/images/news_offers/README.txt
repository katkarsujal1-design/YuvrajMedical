Store homepage Health News & Offers carousel images in this folder.

The homepage carousel checks this folder first. If a listed image is missing,
the page falls back to an existing Yuvraj Medical image so the carousel does
not show a broken image.

Recommended size:
- 1600 x 520 px for wide homepage banners, or 1200 x 700 px if you prefer a taller image
- JPG, JPEG, PNG, or WEBP
- Premium healthcare/product/logistics photos or realistic renders
- The carousel uses object-fit: contain, so the full image is visible without cropping

Example template path:
{{ url_for('static', filename='images/news_offers/upload-prescription.webp') }}

Suggested filenames:
- upload-prescription.webp
- same-day-delivery.webp
- health-essentials-offer.webp
- diabetes-care.webp
- cough-cold-care.webp
- vitamins-supplements.webp

After adding or replacing images, refresh the browser. Static images are served
from the project folder, so you do not need to edit HTML when the filenames
stay the same.
