SYSTEM_ALIGNMENT_PROMPT="""

Given the user's news preferences and an article, generate a number to signify the article's
alignment with the user's preferences. The number should be between 0 and 100, where 100 is
the highest possible alignment and 0 is the lowest possible alignment.

Only reply with a number between 0 and 100. If the user's preferences are empty, return 0.
Do not include any other information in your response. Do not provide any explanation or reasoning.

Example Input:
User's news preferences: 
I like articles about technology and science.

Article:
New study shows that AI can predict the future.

Example Output:
75

"""

HUMAN_ALIGNMENT_PROMPT="""
User's news preferences: 
{preferences}

Article:
{article_text}
"""

SYSTEM_SUMMARY_PROMPT="""

Given the user's news preferences and an article, provide a summary of the article in 1 paragraphs.
The summary should be concise and informative, covering the main points of the article.
Align the article as much as possible with the user's preferences and what they would find interesting.

Make sure to include the most important information and leave out any unnecessary details.
Add a title to the summary and make sure it is well-structured and easy to read.

Example Input:
User's news preferences: 
I like articles about technology and science.

Article Title:
New study shows that AI can predict the future

Article:
Researchers have developed a new AI system that can predict future events with high accuracy. The system uses advanced machine learning algorithms to analyze large datasets and identify patterns that can help predict future outcomes. The study, published in the journal Science, demonstrates the potential of AI to revolutionize forecasting and decision-making in various fields. The researchers hope that their work will lead to new applications of AI in areas such as finance, healthcare, and climate science.

Example Output:
New study shows that AI can predict the future

Researchers have created an AI system capable of accurately predicting future events by analyzing large datasets with advanced machine learning algorithms. Published in Science, the study highlights AI's potential to transform forecasting and decision-making in fields like finance, healthcare, and climate science.

"""

HUMAN_SUMMARY_PROMPT="""
User's news preferences: 
{preferences}

Article Title:
{article_title}

Article:
{article_text}
"""