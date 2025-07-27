import requests
from bs4 import BeautifulSoup
import feedparser
import logging
import json

logger = logging.getLogger(__name__)

def fetch_yahoo_news_articles():
    """
    Fetches news articles from a given Yahoo News RSS feed.
    For each article, it also scrapes the full content and publisher from its detail page.
    Prioritizes extracting publisher from JSON-LD data.
    """
    rss_url = "https://tw.news.yahoo.com/rss"
    news_articles = []
    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo:
            logger.warning(f"RSS feed parsing error (bozo bit set): {feed.bozo_exception}")

        for entry in feed.entries:
            article_url = entry.link
            full_content = None
            publisher = None

            if article_url:
                try:
                    response = requests.get(article_url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    json_ld_script = soup.find('script', {'type': 'application/ld+json'})
                    if json_ld_script:
                        try:
                            data = json.loads(json_ld_script.string)

                            if 'creator' in data and \
                               isinstance(data['creator'], dict) and \
                               data['creator'].get('@type') == 'Organization' and \
                               'name' in data['creator']:
                                publisher = data['creator']['name']
                                logger.info(f"Publisher found from JSON-LD (creator.name as Organization): {publisher} for {article_url}")
                            elif 'provider' in data and \
                                 isinstance(data['provider'], dict) and \
                                 data['provider'].get('@type') == 'Organization' and \
                                 'name' in data['provider']:
                                publisher = data['provider']['name']
                                logger.info(f"Publisher found from JSON-LD (provider.name as Organization): {publisher} for {article_url}")
                            else:
                                logger.debug(f"JSON-LD found for {article_url}, but no 'Organization' type found in 'creator.name' or 'provider.name'.")

                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Error parsing JSON-LD script for {article_url}: {e}")
                        except Exception as e:
                            logger.warning(f"An unexpected error occurred during JSON-LD parsing for {article_url}: {e}")
                    else:
                        logger.debug(f"JSON-LD script (type='application/ld+json') not found for {article_url}.")


                    article_container = soup.find("div", class_="atoms")
                    if article_container:
                        paragraphs = article_container.find_all("p")
                        full_content = "".join(p.text for p in paragraphs)
                        if full_content:
                            logger.info(f"Successfully extracted content from 'atoms' div for {article_url}.")
                        else:
                            logger.warning(f"Found 'atoms' div but no content extracted for {article_url}.")
                    else:
                        logger.warning(f"Could not find <div class='atoms'> for main content for {article_url}.")
                        description_meta = soup.find('meta', {'name': 'description'})
                        if description_meta and 'content' in description_meta.attrs:
                            full_content = description_meta['content']
                            logger.info(f"Fallback: Content set to meta description for {article_url}.")
                        else:
                            logger.warning(f"Could not find any content for {article_url}.")

                    if not publisher:
                        logger.warning(f"Could not determine publisher for {article_url} after all attempts.")

                except requests.exceptions.RequestException as req_e:
                    logger.error(f"Error fetching article page {article_url}: {req_e}")
                except Exception as e:
                    logger.error(f"Error parsing article page {article_url}: {e}")

            news_articles.append({
                'title': entry.title,
                'link': article_url,
                'published_at': entry.published,
                'summary': entry.summary,
                "publisher": publisher,
                "content": full_content,
            })

    except Exception as e:
        logger.error(f"Error fetching RSS feed {rss_url}: {e}")

    return news_articles