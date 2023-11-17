import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

async def get_webpage_content(url: str, max_retries=2, timeout=7) -> str:
    async with httpx.AsyncClient() as client:
        await asyncio.sleep(6)
        for attempt in range(max_retries):
            response = await client.get(url, timeout=timeout, follow_redirects=True)
            response.raise_for_status()
            
            if response.is_redirect:
                url = response.headers['location']
                print(f"Redirecting to: {url}")
                continue
            
            return response.text

async def scrape_href_links(content: str, target_class: str) -> list:
    soup = BeautifulSoup(content, 'html.parser')
    base_url = "https://www.amazon.in"
    href_links = [urljoin(base_url, a['href']) for a in soup.find_all('a', {'class': target_class}, href=True)]
    return href_links

async def scrape_span_text(content: str, target_id: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    span_element = soup.find('span', {'id': target_id})
    return span_element.text.strip() if span_element else "No matching span element found"

async def price(content: str, target_class: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    price = soup.find('span', {'class': target_class})
    return price.text.strip() if price else "No matching span element found"

async def tech_details(content: str) -> dict:
    soup = BeautifulSoup(content, 'html.parser')
    tech_spec_table = soup.find('table', {'id': 'productDetails_techSpec_section_1'})

    tech_spec_data = {}
    if tech_spec_table:
        rows = tech_spec_table.find_all('tr')
        for row in rows:
            key = row.find('th', {'class': 'a-color-secondary a-size-base prodDetSectionEntry'})
            value = row.find('td', {'class': 'a-size-base prodDetAttrValue'})
            if key and value:
                new_value = value.text.strip()
                tech_spec_data[key.text.strip()] = new_value.replace('\u200e','')

    return tech_spec_data

async def product_details(content: str) -> dict:
    soup = BeautifulSoup(content, 'html.parser')
    tech_spec_table = soup.find('table', {'id': 'productDetails_detailBullets_sections1'})

    tech_sum_data = {}
    if tech_spec_table:
        rows = tech_spec_table.find_all('tr')
        for row in rows:
            key = row.find('th', {'class': 'a-color-secondary a-size-base prodDetSectionEntry'})
            value = row.find('td', {'class': 'a-size-base prodDetAttrValue'})
            if key and value:
                tech_sum_data[key.text.strip()] = value.text.strip()

    return tech_sum_data

async def scrape_star_rating(content: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    star_rating_class = "a-icon a-icon-star a-star-3-5 cm-cr-review-stars-spacing-big"
    star_rating_span = soup.find('i', {'class': star_rating_class})
    star_rating_text_class = "a-icon-alt"
    star_rating_text_span = soup.find('span', {'class': star_rating_text_class})
    return star_rating_text_span.text.strip() if star_rating_text_span else None

async def scrape_amazon_product(product_url: str) -> dict:
    content = await get_webpage_content(product_url)
    target_id = "productTitle"
    title_text = await scrape_span_text(content, target_id)
    price_class = "a-price-whole"
    prices = await price(content, price_class)
    tech_spec = await tech_details(content)
    tech_sum = await product_details(content)
    review = await scrape_star_rating(content)
    product = {
        'Title': title_text,
        'Price': prices,
        'Reviews': review
    }
    tech_sum.update(tech_spec)
    product.update(tech_sum)

    print("\nScraped Product:")
    print(product)
    return product

async def scrape_amazon():
    scraped_data = []
    for i in range(1, 4):
        # https://www.amazon.in/s?k=smartphone&page={i}&crid=2PR9G4NVATT3&qid=1699686221&sprefix=smartphone%2Caps%2C272"
        amazon_url = f"https://www.amazon.in/s?k=laptop&page={i}&crid=2PR9G4NVATT3&qid=1699686221&sprefix=laptop%2Caps%2C272"
        content = await get_webpage_content(amazon_url)
        target_class = "a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"
        href_links = await scrape_href_links(content, target_class)
        
        for product_url in href_links:
            await asyncio.sleep(10)
            scraped_data.append(await scrape_amazon_product(product_url))

    return scraped_data

# Example usage:
if __name__ == "__main__":
    asyncio.run(scrape_amazon())
