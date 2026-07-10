# Browser Collection Contract

Use the browser because Meditherapy and marketplace reviews may render inside JavaScript widgets or iframes.

## Collection procedure

1. Navigate directly to the user-provided product URL.
2. Confirm the product name and current URL.
3. Inspect the rendered DOM, including expanded iframe content.
4. Locate the review count and visible review containers.
5. Collect a bounded set of visible reviews. Prefer at least 10 when the page exposes them.
6. Preserve exact visible wording when short. For long reviews, save a faithful excerpt and do not add facts.
7. Record explicit skin type, usage period, rating, routine context and repurchase intent only when visible.
8. Capture a page screenshot and a product image. Use VLM to transcribe visible marketing text from those images into `visual_claims`.

## Input schema

```json
{
  "project": "Public customer voice run",
  "product_name": "Product name",
  "product_image_url": "https://public-image-url",
  "channels": [
    {"name": "meditherapy", "type": "product_page", "url": "https://product-url"}
  ],
  "visual_claims": [
    {
      "phrase": "Visible text transcribed from image",
      "source": "product_image",
      "provenance": "browser_vlm_visible_text",
      "url": "https://source-url"
    }
  ],
  "reviews": [
    {
      "channel": "meditherapy_official",
      "url": "https://source-product-url",
      "captured_at": "2026-01-01T00:00:00+09:00",
      "provenance": "browser_visible_review",
      "rating": 5,
      "skin_type": "민감성",
      "usage_period": "2주",
      "text": "Visible review or faithful excerpt"
    }
  ]
}
```

Do not use `manual_reviews`, `_sample` channel names, fabricated ratings, or inferred demographics in a real run.

## Visual production contract

- Generate three text-free 2x2 webtoon sheets from `instagram/imagegen_prompts.json` with Codex built-in image generation.
- Keep each panel's lower area quiet so the deterministic renderer can add Korean dialogue.
- Generate a clean product hero from the captured product reference only after inspecting it; remove promotional headline text and keep no unsupported claims.
- Store generated assets inside the run output. Never leave final project assets only in the global Codex generated-images directory.
- Re-run generation with `comic_background_paths` and `product_hero_path`; Korean text must come from the Law-MCP-reviewed storyboard, not from image generation.
