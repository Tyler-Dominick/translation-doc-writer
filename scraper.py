"""Web scraping and URL fetching functionality"""

import requests
from bs4 import BeautifulSoup


def get_all_urls(base_url, blogs):
    """Fetch all URLs from website sitemap"""
    resp = requests.get(base_url + 'sitemap.xml')
    soup = BeautifulSoup(resp.content, 'xml')
    site_maps = soup.findAll('sitemap')
    
    out = set()
    print(f'{blogs}')
    for site_map in site_maps:
        map = site_map.find('loc').string
        if map == (base_url + "post-sitemap.xml") and (blogs=='no'):
            continue
        else:
            response = requests.get(map)
            sitemap_soup = BeautifulSoup(response.content, 'xml')
            urls = sitemap_soup.findAll('url')
            for u in urls:
                loc = u.find('loc').string
                out.add(loc)
    return out


def fetch_and_parse(url):
    """Fetch and parse HTML content from a URL"""
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'lxml')
    return soup

