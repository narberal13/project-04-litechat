"""Website crawler using Playwright — fetches HTML, metadata, and screenshots."""

import asyncio
from dataclasses import dataclass, field
from playwright.async_api import async_playwright


@dataclass
class CrawlResult:
    url: str
    final_url: str = ""
    html: str = ""
    title: str = ""
    meta_description: str = ""
    meta_keywords: str = ""
    h1_tags: list[str] = field(default_factory=list)
    h2_tags: list[str] = field(default_factory=list)
    images_without_alt: int = 0
    images_total: int = 0
    internal_links: int = 0
    external_links: int = 0
    has_viewport_meta: bool = False
    has_canonical: bool = False
    has_favicon: bool = False
    has_structured_data: bool = False
    page_size_bytes: int = 0
    load_time_ms: int = 0
    status_code: int = 0
    error: str | None = None


async def crawl_url(url: str, timeout_ms: int = 30000) -> CrawlResult:
    result = CrawlResult(url=url)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=(
                        "Mozilla/5.0 (compatible; SiteScanBot/1.0; "
                        "+https://sitescan.example.com)"
                    ),
                )
                page = await context.new_page()

                start_time = asyncio.get_event_loop().time()
                response = await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                end_time = asyncio.get_event_loop().time()

                result.load_time_ms = int((end_time - start_time) * 1000)
                result.status_code = response.status if response else 0
                result.final_url = page.url

                result.html = await page.content()
                result.page_size_bytes = len(result.html.encode("utf-8"))

                # Extract metadata via JS evaluation
                metadata = await page.evaluate("""() => {
                    const getMeta = (name) => {
                        const el = document.querySelector(
                            `meta[name="${name}"], meta[property="${name}"]`
                        );
                        return el ? el.getAttribute('content') || '' : '';
                    };

                    const images = document.querySelectorAll('img');
                    const links = document.querySelectorAll('a[href]');
                    const currentHost = window.location.hostname;

                    let imagesWithoutAlt = 0;
                    images.forEach(img => {
                        if (!img.getAttribute('alt') || img.getAttribute('alt').trim() === '') {
                            imagesWithoutAlt++;
                        }
                    });

                    let internalLinks = 0;
                    let externalLinks = 0;
                    links.forEach(link => {
                        try {
                            const href = new URL(link.href);
                            if (href.hostname === currentHost) {
                                internalLinks++;
                            } else {
                                externalLinks++;
                            }
                        } catch {}
                    });

                    return {
                        title: document.title || '',
                        metaDescription: getMeta('description'),
                        metaKeywords: getMeta('keywords'),
                        h1Tags: [...document.querySelectorAll('h1')].map(h => h.textContent.trim()),
                        h2Tags: [...document.querySelectorAll('h2')].map(h => h.textContent.trim()),
                        imagesTotal: images.length,
                        imagesWithoutAlt: imagesWithoutAlt,
                        internalLinks: internalLinks,
                        externalLinks: externalLinks,
                        hasViewportMeta: !!document.querySelector('meta[name="viewport"]'),
                        hasCanonical: !!document.querySelector('link[rel="canonical"]'),
                        hasFavicon: !!(
                            document.querySelector('link[rel="icon"]') ||
                            document.querySelector('link[rel="shortcut icon"]')
                        ),
                        hasStructuredData: !!(
                            document.querySelector('script[type="application/ld+json"]')
                        ),
                    };
                }""")

                result.title = metadata["title"]
                result.meta_description = metadata["metaDescription"]
                result.meta_keywords = metadata["metaKeywords"]
                result.h1_tags = metadata["h1Tags"]
                result.h2_tags = metadata["h2Tags"]
                result.images_total = metadata["imagesTotal"]
                result.images_without_alt = metadata["imagesWithoutAlt"]
                result.internal_links = metadata["internalLinks"]
                result.external_links = metadata["externalLinks"]
                result.has_viewport_meta = metadata["hasViewportMeta"]
                result.has_canonical = metadata["hasCanonical"]
                result.has_favicon = metadata["hasFavicon"]
                result.has_structured_data = metadata["hasStructuredData"]

                await context.close()
            finally:
                await browser.close()

    except Exception as e:
        result.error = str(e)

    return result
