# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, List
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.article_fetcher import fetch_recent_articles_for_role
from app.firestore_sources import get_sources_for_role

MODEL = "gemini-3.6-flash"


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to extract and persist cross-session memories after each turn."""
    try:
        await callback_context.add_session_to_memory()
    except (ValueError, Exception):
        pass
    return None


def fetch_sources(role: str) -> List[Dict[str, Any]]:
    """Retrieves news sources stored in Firestore relevant to a specific role or role description.

    Args:
        role: The role (e.g. 'Product Designer', 'Design Engineer', 'PM', 'Frontend', 'Backend', 'FDE')
              or custom job description.

    Returns:
        A list of dictionaries with source details: name, url, type (hackernews or rss), category (news or reads), and relevant roles.
    """
    return get_sources_for_role(role)


def fetch_recent_articles(role: str) -> List[Dict[str, Any]]:
    """Fetches real recent tech articles from the last 30 days for a given role or work description.

    Queries Firestore for the sources associated with the role, then retrieves real articles
    from Hacker News (Algolia API, >=100 points) and RSS feeds.

    Args:
        role: The user's role or description of what they do.

    Returns:
        A list of article dictionaries, each containing:
        - title (str): Headline of the article
        - source (str): Name of the publication
        - category (str): 'news' (breaking/launches/releases/tools) or 'reads' (in-depth essays/analysis)
        - published_date (str): Published date formatted as YYYY-MM-DD
        - link (str): Direct URL to the real article
    """
    return fetch_recent_articles_for_role(role)


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Loopy, a personalized tech news briefing agent for tech professionals.\n"
        "Guidelines:\n"
        "1. Memory & Role Recall:\n"
        "   - You have long-term cross-session memory enabled via PreloadMemoryTool.\n"
        "   - When a user states their role or describes what they do (e.g. 'I am a Product Designer', "
        "'I build backend microservices and databases'), remember this role or description across sessions.\n"
        "   - If the user returns in a new session without stating their role (e.g. 'Give me my briefing', "
        "'What is the news today?'), check your preloaded memories for their stored role or work description, "
        "and immediately use that to fetch and personalize their briefing.\n"
        "2. When the user specifies their role or describes what they do, or when you recall it from memory, "
        "immediately call the `fetch_recent_articles` tool for that role.\n"
        "3. Selection & Mix Rules:\n"
        "   - Select up to 5 items total.\n"
        "   - LEAD WITH NEWS: Prioritize actual industry news, product launches, releases, and new tools "
        "(from 'news' sources like Hacker News, TechCrunch, The Verge, Figma Releases, GitHub Blog, Product Hunt).\n"
        "   - AI RELEASES ARE UNIVERSAL: Major AI model and AI tool releases (e.g. Gemini, OpenAI, Claude, AI developer/design tools) "
        "count as highly relevant news for EVERY role, including designers (Product Designer, Design Engineer) and PMs.\n"
        "   - Include AT MOST 2 'reads' (longform essays/opinion pieces from 'reads' sources like UX Collective, A List Apart, Smashing Magazine, Lenny's, The Pragmatic Engineer).\n"
        "   - Rank by relevance to the user's role and recency.\n"
        "4. STRICT GROUNDING: Only include articles returned by `fetch_recent_articles`. "
        "Never invent, synthesize, or hallucinate articles or URLs. If fewer than 5 real items are returned, "
        "only present the items found without filling the gap.\n"
        "5. If the user provided a custom description, tailor the concrete action in 'Why it matters' "
        "directly to what they described doing."
    ),
    workflow_description=(
        "Call fetch_recent_articles for the user's role, select up to 5 items (leading with news, max 2 reads), "
        "and return a structured A2UI surface with the articles grouped into News and Reads."
    ),
    ui_description=(
        "Render the briefing as a clean, structured A2UI surface.\n"
        "Structure rules:\n"
        "- Root element should be a Column containing section headings (using Text with usageHint='h2') "
        "and article cards.\n"
        "- Group articles under two sections: 'News' (for news items) and 'Reads' (for longform reads).\n"
        "- Show each article in the brief as its own Card.\n"
        "- Inside each article Card, include a Column containing:\n"
        "  1. Headline: Text with usageHint 'h3' displaying the article title.\n"
        "  2. Metadata Row: A Row with two Text components: source name and published date.\n"
        "  3. Why it matters: Text explaining why this matters specifically to the user's role, "
        "naming concrete tools/workflows they can try. For designers on AI releases, explain what the release means for design work.\n"
        "  4. Link: Text component with the label 'Read article' or markdown link pointing to the article's real link URL, "
        "or Text with usageHint 'body' displaying [Read article](URL).\n"
        "- Keep cards simple, built from rows and columns, no buttons or forms (they do nothing in adk web).\n"
        "- Output ONLY the raw A2UI JSON array — no prose, and never wrap it in <a2a_datapart_json> tags."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[PreloadMemoryTool(), fetch_recent_articles, fetch_sources],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
