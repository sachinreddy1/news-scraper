import gradio as gr
import os

import asyncio
import agentql
from playwright.async_api import BrowserContext, async_playwright

import logging
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from constants import SYSTEM_ALIGNMENT_PROMPT, HUMAN_ALIGNMENT_PROMPT, SYSTEM_SUMMARY_PROMPT, HUMAN_SUMMARY_PROMPT

from gtts import gTTS
from io import BytesIO

from transformers import pipeline

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv()

PLACEHOLDER = """I am a software engineer interested in technology and science. I like to read about the latest advancements in AI, machine learning, and space exploration. 

I prefer articles that are well-researched, informative, and easy to understand. 

I enjoy reading about new technologies, scientific discoveries, and innovative ideas. I am open to exploring new topics and learning about different fields."""

ARTICLE_LINK_QUERY = """
{
    article_links(should be a link to an article like "https://thezvi.substack.com/p/ais-will-increasingly-fake-alignment")[]
}
"""

ARTICLE_QUERY = """
{
    article_title,
    published_date,
    text
}
"""

chat = ChatAnthropic(temperature=0, model_name="claude-3-5-haiku-20241022")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

async def scrape_article(link): 
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await agentql.wrap_async(context.new_page())

        page.enable_stealth_mode()

        try:
            log.info("Scraping article... %s", link)

            await page.goto(link)
            await page.wait_for_page_ready_state()
            article = await page.query_data(
                ARTICLE_QUERY,
                mode="fast"
            )

            return article['article_title'], article['text']
        except Exception as e:
            log.info("Error scraping article... %s", e)
            gr.Info("Error scraping article... " + link, duration=5)

        await browser.close()

async def fetch_article_links(website):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await agentql.wrap_async(context.new_page())

        page.enable_stealth_mode()

        try:
            log.info("Navigating to the page... %s", website)

            await page.goto(website)
            await page.wait_for_page_ready_state()
            article_links = await page.query_data(ARTICLE_LINK_QUERY)
            
            return article_links['article_links']
        except Exception as e:
            log.info("Error fetching article links... %s", e)
            gr.Info("Error fetching article links... " + website, duration=5)

        await browser.close()

async def process_article(article, preferences, wordsPerArticle=250):
    if article is None:
        return None

    title, text = article

    if title is None or text is None:
        return None

    try:
        log.info("Summarizing article... %s", title)

        relevance_prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_ALIGNMENT_PROMPT), ("human", HUMAN_ALIGNMENT_PROMPT)])
        chain = relevance_prompt | chat
        response = await chain.ainvoke(
            {
                "preferences": preferences,
                "article_text": text
            }
        )

        relevance = int(response.content)
    except Exception as e:
        log.info("Error aligning article... %s", e)
        gr.Info("Error aligning article... " + title, duration=5)
        return None

    if relevance >= 70:
        try:
            response = summarizer(text, max_length=wordsPerArticle, min_length=50, do_sample=False)
            return title + "\n\n" + response[0]['summary_text']
        except Exception as e:
            log.info("Error summarizing article... %s", e)
            gr.Info("Error summarizing article... " + title, duration=5)
            return None

    return None

async def summarizeNews(preferences, websites, wordsPerArticle):
    if len(websites) == 0:
        gr.Info("Websites are empty.", duration=5)
        return None

    article_link_tasks = [fetch_article_links(site) for site in websites.split("\n")]
    article_link_groups = await asyncio.gather(*article_link_tasks)
    article_links = [link for group in article_link_groups for link in group]

    article_tasks = [scrape_article(link) for link in article_links]
    articles = await asyncio.gather(*article_tasks)

    summaries = await asyncio.gather(*[process_article(article, preferences, wordsPerArticle) for article in articles])
    summaries = [summary for summary in summaries if summary is not None]
    summary_text = "\n\n".join(summaries)

    try:
        mp3_fp = BytesIO()
        tts = gTTS(summary_text, lang='en')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_bytes = mp3_fp.read()
    except Exception as e:
        log.info("Error generating audio... %s", e)
        raise gr.Error("Error generating audio...", duration=5)

    log.info("Done generating audio...")

    return audio_bytes, summary_text

demo = gr.Interface(
    fn=summarizeNews,
    title="News Summarizer",
    inputs=[
        gr.Textbox(
            label="Profile: Enter your new's preferences here.", 
            lines=10,
            placeholder=PLACEHOLDER
        ),
        gr.Textbox(
            label="Websites to scrape:",
            lines=5,
            placeholder="https://hackernews.com\nhttps://techcrunch.com",
        ),
        gr.Slider(100, 500, value=250, label="Number of words per article", info="Choose between 100 and 500"),
    ],
    outputs=[
        gr.Audio(label="Generated audio summary"),
        gr.Textbox(
            label="Generated text summary",
            lines=5,
            placeholder="...",
        )
    ],
)

if __name__ == "__main__":
    demo.launch(share=True)