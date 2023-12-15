import scrapy
import re
# from urllib import urlencode
from urllib.parse import urljoin, urlencode
import json

# queries = ['Mens Tshirt','Mens Shirt','Mens Jeans','Womens Jeans']

queries = [
    # Mens Clothing
    # "Men's T-Shirts",
    # "Men's Shirts",
    # "Men's Jeans",
    # "Men's Jackets",
    # "Men's Suits",
    # "Men's Sweaters",
    # "Men's Activewear",
    # "Men's Sleepwear",

    # Womens Clothing
    # "Women's Dresses",
    # "Women's Tops",
    # "Women's Jeans",
    # "Women's Jackets",
    # "Women's Sweaters",
    # "Women's Activewear",
    # "Women's Sleepwear",
    # "Women's Skirts",

    # Shoes
    # "Men's Shoes",
    # "Women's Shoes",
    # "Athletic Shoes",
    # "Boots",
    # "Sandals",
    # "Slippers",
    # "Sneakers",

    # Accessories
    # "Jewelry",
    # "Watches",
    # "Handbags",
    # "Backpacks",
    # "Wallets",
    # "Sunglasses",
    # "Hats",
    # "Belts",
    # "Scarves",
    # "Gloves",
    # "Ties",
    # "Umbrellas",

    # Specialized Clothing
    # "Workout Clothing",
    # "Maternity Clothing",
    # "Plus Size Clothing",
    # "Petite Clothing",

    # Outdoor Clothing
    # "Outdoor Jackets",
    # "Hiking Boots",
    "Rain Gear",
    "Winter Coats",

    # Formalwear
    "Suits",
    "Formal Dresses",
    "Tuxedos",

    # Vintage Clothing
    "Vintage Dresses",
    "Retro T-Shirts",
    "Vintage Accessories",

    # Swimwear
    "Men's Swimwear",
    "Women's Swimwear"
]


API = 'a8935fe32852c87c18aa39775d2f9255'
# '4e1fe28d930499c7900ec2aa11dcc184'
# 'de9c3de4c267432172db09464bb67e6b'
# 'b876a75ea4a1b1dfdf74171a46f6f993'
def get_url(url):
    payload = {'api_key': API, 'url': url, 'country_code': 'us'}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url

class AmazonSpider(scrapy.Spider):
    name = "amazon"
    
    def start_requests(self):
        for query in queries:
            url = 'https://www.amazon.com/s?' + urlencode({'k': query})
            yield scrapy.Request(url=url, callback=self.parse_keyword_response,
                                 headers={"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}, meta={'query': query})


    def parse_keyword_response(self, response):
        query = response.meta['query']
        products = response.xpath('//*[@data-asin]')
        for product in products:
            asin = product.xpath('@data-asin').extract_first()
            product_url = f"https://www.amazon.com/dp/{asin}"
            # print("product url", product_url)
            yield scrapy.Request(url=get_url(product_url), callback=self.parse_product_page, meta={'asin': asin, 'query': query})
        next_page = response.xpath('//li[@class="a-last"]/a/@href').extract_first()
        # print("next page", next_page)
        if next_page:
            url = urljoin("https://www.amazon.com",next_page)
            # print("next page url", url)
            yield scrapy.Request(url=get_url(url), callback=self.parse_keyword_response, meta={'query': query})


    def parse_product_page(self, response):
        asin = response.meta['asin']
        query = response.meta['query']
        title = response.xpath('//*[@id="productTitle"]/text()').extract_first()
        image = re.search('"large":"(.*?)"',response.text).groups()[0]
        rating = response.xpath('//*[@id="acrPopover"]/@title').extract_first()
        number_of_reviews = response.xpath('//*[@id="acrCustomerReviewText"]/text()').extract_first()
        price = response.xpath('//*[@id="priceblock_ourprice"]/text()').extract_first()

        if not price:
            price = response.xpath('//*[@data-asin-price]/@data-asin-price').extract_first() or \
                    response.xpath('//*[@id="price_inside_buybox"]/text()').extract_first()
        temp = response.xpath('//*[@id="twister"]')
        sizes = []
        colors = []
        if temp:
            s = re.search('"variationValues" : ({.*})', response.text).groups()[0]
            json_acceptable = s.replace("'", "\"")
            di = json.loads(json_acceptable)
            sizes = di.get('size_name', [])
            colors = di.get('color_name', [])
        bullet_points = response.xpath('//*[@id="feature-bullets"]//li/span/text()').extract()
        seller_rank = response.xpath('//*[text()="Amazon Best Sellers Rank:"]/parent::*//text()[not(parent::style)]').extract()

        yield {'asin': asin, 'Title': title, 'MainImage': image, 'Rating': rating, 'NumberOfReviews': number_of_reviews,
            'Price': price, 'AvailableSizes': sizes, 'AvailableColors': colors, 'BulletPoints': bullet_points,
            'SellerRank': seller_rank, 'ProductCat': query}
    
    

