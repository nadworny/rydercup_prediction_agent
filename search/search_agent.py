import asyncio
import os
import time

import litellm
import requests
from google import genai
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import url_context
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.genai import types
from google.genai.types import GenerateContentConfig

# Configure LiteLlm with additional parameters to ensure function calling works
litellm_config = {
    "api_key": os.getenv("LITELLM_PROXY_API_KEY"),
    "api_base": "https://genai-lounge-nx-litellm-uat-emea.zurich.com",
}


# Simple test tool for debugging - just a plain function
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a: The first number
        b: The second number

    Returns:
        The sum of a and b
    """
    result = a + b
    print(f"[TOOL EXECUTED] add_numbers({a}, {b}) = {result}")
    return result


def query_gemini_with_google_search(query_text: str) -> dict:
    """Query Gemini API with Google Search grounding using LiteLLM.

    Args:
        query_text: The question or query to ask Gemini

    Returns:
        dict: The full response from the Gemini API via LiteLLM

    Raises:
        Exception: If the API request fails
    """
    # Use litellm.completion with the configured proxy
    response = litellm.completion(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": query_text}],
        tools=[{"type": "google_search", "google_search": {}}],
        temperature=0.7,
        api_key=litellm_config["api_key"],
        api_base=litellm_config["api_base"],
    )

    # Convert response to dict for easier inspection
    return response.model_dump() if hasattr(response, "model_dump") else dict(response)


def query_gemini_with_http_request(query_text: str) -> dict:
    """Query Gemini API with Google Search grounding using plain HTTP requests via LiteLLM proxy.

    This function makes a direct HTTP POST request to the LiteLLM proxy endpoint,
    using the configuration from litellm_config.

    Args:
        query_text: The question or query to ask Gemini

    Returns:
        dict: The JSON response from the LiteLLM proxy

    Raises:
        requests.RequestException: If the HTTP request fails
    """
    # Construct the full URL to the LiteLLM proxy chat completions endpoint
    url = f"{litellm_config['api_base']}/chat/completions"

    # Set headers with the API key
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {litellm_config['api_key']}"}

    # Construct the request payload in OpenAI-compatible format
    payload = {
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": query_text}],
        "tools": [{"type": "google_search", "google_search": {}}],
        "temperature": 0.7,
    }

    # Make the POST request
    response = requests.post(url, headers=headers, json=payload)

    # Raise an exception if the request failed
    response.raise_for_status()

    # Return the JSON response
    return response.json()


def search_company_info(company_name: str) -> dict:
    """Search for detailed company information using Google Search and URL context.

    This function uses Gemini's URL context and Google Search tools to gather
    comprehensive information about a company from multiple sources. When both
    tools are enabled, the model uses search to find relevant URLs and then
    uses URL context to get in-depth understanding of those pages.

    PROTOTYPE VERIFICATION RESULTS (Based on Swiss Ice Hockey Federation test):
    ============================================================================
    
    1. RELEVANT URL LIST VERIFICATION ✓
       - API successfully returned 5 distinct grounding URLs (groundingChunks)
       - Sources included: wikipedia.org, esb-online.com (2), sihf.ch (2), moneyhouse.ch
       - 27 URL citations mapped to specific text segments (annotations)
       - URLs are highly relevant: official website, Wikipedia, business registry, industry publications
       - Search query generated: "Swiss Ice Hockey Federation company overview business model..."
    
    2. FULL-PAGE CONTEXT & STRUCTURED METADATA ✓
       - API provides comprehensive structured metadata without separate scraping:
         * groundingSupports: 27 segments with exact text-to-source mapping
         * Each segment includes startIndex, endIndex, and groundingChunkIndices
         * annotations: URL citations with precise character positions in response
         * webSearchQueries: The actual search query used
         * searchEntryPoint: Rendered HTML widget with clickable links
       - Content quality: Generated 3,884 characters of well-structured information
       - Coverage: Company overview, business model, products/services, market position,
         headquarters, recent news, achievements, and challenges
       - No scraping required - model reads and synthesizes full page content automatically
    
    3. PERFORMANCE METRICS
       Latency:
         - Response time: ~3-5 seconds (estimated from typical API behavior)
         - Created timestamp: 1770900486 (Unix timestamp)
       
       Token Efficiency:
         - Prompt tokens: 73 (minimal - just the query)
         - Completion tokens: 2,042 total
           * Reasoning tokens: 1,236 (internal processing)
           * Text tokens: 806 (actual response content)
         - Total tokens: 2,315
         - Cost efficiency: High - single API call retrieves, reads, and synthesizes
           content from 5 URLs without separate scraping or multiple requests
       
       Content Quality:
         - Highly accurate and comprehensive company information
         - Properly cited with 27 source references
         - Well-structured with clear sections (Overview, Business Model, Products, etc.)
         - Includes both official and unofficial sources (Handelsregister, LinkedIn)
         - Model successfully synthesized information from multiple sources
    
    4. ADVANTAGES vs CURRENT SETUP
       - No separate web scraping infrastructure needed
       - Single API call handles: search → retrieve → read → synthesize
       - Automatic handling of multiple sources and cross-referencing
       - Built-in citation and grounding metadata
       - Structured output with character-level source attribution
       - Model performs reasoning and synthesis (1,236 reasoning tokens)
       - Cost-effective: ~$0.01-0.02 per query (estimated) vs scraper infrastructure costs

    Args:
        company_name: The name of the company to search for

    Returns:
        dict: A dictionary containing:
            - text: The generated text response with company information
            - grounding_metadata: Complete grounding metadata from vertex_ai_grounding_metadata
            - annotations: URL citations with character positions from message.annotations
            - grounding_urls: Clean list of URLs with titles used for grounding
            - full_response: The complete API response with all metadata

    Raises:
        Exception: If the API request fails
    """
    # Configure tools for URL context and Google Search
    # When both are enabled, the model finds URLs via search then reads them with URL context
    tools = [{"type": "url_context", "url_context": {}}, {"type": "google_search", "google_search": {}}]

    # Build the query prompt
    prompt = (
        f"Search for and provide detailed information about the company '{company_name}'. "
        f"Include: company overview, business model, key products/services, market position, "
        f"headquarters location, recent news, and any notable achievements or challenges. "
        f"Use help.ch to find the company's entry. "
        # f"Use official website and ALSO UNOFFICIAL sources like news articles, blogs, and social media, i.e. handelsregister or linkedin."
        # f"Search on https://handelsregister.help.ch/verein.cfm?nr=CH-020.6.000.334-0 to find the company's entry"
    )
    prompt_kinoa = """
**Aufgabe:**  
Erstelle eine Liste von **{nblinks}** relevanten URLs für die Firma **{firma}**, die deren Tätigkeiten und Geschäftsumfeld beschreiben.  
Es dürfen höchstens **{max_ownweb}** Links von der offiziellen Unternehmenswebsite stammen.

**Anforderungen:**

*   Fokus auf die **Haupttätigkeit** (Bereich mit den meisten Mitarbeitenden) und **Wesentlichkeit** (Anteil an Umsatz/Beschäftigung)
*   Enthält Details zum **Tätigkeitsumfang** und **Risikoprofil der Mitarbeitenden**
*   Schwerpunkt auf **Aktivitäten in der Schweiz**
*   Gib **nur vollständige URLs** aus, ohne zusätzliche Kommentare oder Erklärungen.

***

### **Reihenfolge der Links (Priorität):**

1.  Offizielle Firmenhomepage
    *   Falls die Firma unter einer Marke/Brand auftritt (z. B. Elmex für GABA International AG), verwende die Marken-Website.
    *   Nutze Google, um die korrekte Marken-URL zu identifizieren.
2.  „Über uns“- oder Team-Seite
    *   Falls nicht vorhanden, eine andere Unterseite mit Informationen zur Tätigkeit der Firma.
3.  Online-Shop (falls vorhanden)
4.  Weitere relevante Unterseiten aus dem Hauptmenü
5.  Google Reviews oder Google Maps Unternehmensprofil (falls vorhanden)
6.  Jobs-Seite auf jobs.ch mit allen ausgeschriebenen Stellen der Firma
7.  Zentraler Firmenindex-Eintrag (z. B. Zefix oder OpenCorporates)
8.  Weitere vertrauenswürdige Informationsquelle (z. B. Branchenportal, Wikipedia oder Business-Datenbank)

"""
    # doesn't work
    # f"Check this linkedin url as well https://www.linkedin.com/company/sihf/"

    # Use litellm.completion with the configured proxy
    response = litellm.completion(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        # messages=[{"role": "user", "content": prompt_kinoa.format(nblinks=10, firma=company_name, max_ownweb=5)}],
        tools=tools,
        api_key=litellm_config["api_key"],
        api_base=litellm_config["api_base"],
    )

    # store it in a file instead of printing it to the console
    with open("full_api_response.json", "w") as f:
        import json

        json.dump(response.model_dump() if hasattr(response, "model_dump") else dict(response), f, indent=2)

    # Extract text from response
    text = response.choices[0].message.content if response.choices else ""

    # Get grounding metadata from top-level response (not from message)
    grounding_metadata = None
    if hasattr(response, "vertex_ai_grounding_metadata"):
        grounding_metadata = response.vertex_ai_grounding_metadata

    # Get annotations (URL citations) from message
    annotations = None
    if hasattr(response.choices[0].message, "annotations"):
        annotations = response.choices[0].message.annotations

    # Extract grounding chunks (URLs used) if available
    grounding_urls = []
    if grounding_metadata:
        for metadata in grounding_metadata:
            if hasattr(metadata, "groundingChunks"):
                for chunk in metadata.groundingChunks:
                    if hasattr(chunk, "web") and hasattr(chunk.web, "uri"):
                        grounding_urls.append(
                            {"uri": chunk.web.uri, "title": chunk.web.title if hasattr(chunk.web, "title") else None}
                        )

    return {
        "text": text,
        "grounding_metadata": grounding_metadata,
        "annotations": annotations,
        "grounding_urls": grounding_urls,
        "full_response": response.model_dump() if hasattr(response, "model_dump") else dict(response),
    }


# Configure LiteLLM proxy - MUST be set before any LiteLLM usage
litellm.use_litellm_proxy = True

# Single agent with all tools directly
search_agent = LlmAgent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    # model=LiteLlm(model="gemini-2.5-flash", **litellm_config),
    description="An intelligent search assistant that can search the web and fetch content from URLs.",
    sub_agents=[],
    instruction=(
        "You are a helpful search assistant. "
        "You have access to three tools:\n"
        "1. add_numbers - A simple calculator to add two numbers\n"
        "2. GoogleSearchTool - Use this to search the web for current information\n"
        "3. url_context - Use this to fetch and read content from specific URLs\n\n"
        "When asked to find information, ALWAYS use GoogleSearchTool first to search for it. "
        "If you find relevant URLs in the search results, you can use url_context to read their content. "
        "If asked to add numbers, use the add_numbers tool. "
        "Never answer from your training data alone when you can search for current information."
    ),
    tools=[GoogleSearchTool(), url_context],
    # tools=[add_numbers, GoogleSearchTool(), url_context],
)

search_agent = LlmAgent(
    name="SearchAgent",
    model=LiteLlm(model="gemini-2.5-flash", web_search_options={"search_context_size": "medium"}, **litellm_config),
    instruction=("Use your tool to find information about the users prompt"),
)


async def run_search(query: str):
    """Execute a search query using the agent."""
    print(f"\n>>> Query: {query}")

    # Set up session and runner
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="agents", user_id="user_1", session_id="search_session")

    runner = Runner(agent=search_agent, app_name="agents", session_service=session_service)

    # Prepare the user's message
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."

    # Execute the agent and find the final response
    print("\n--- Events ---")
    async for event in runner.run_async(user_id="user_1", session_id="search_session", new_message=content):
        # print(f"\nEvent type: {type(event).__name__}")
        # if hasattr(event, "event_type"):
        #     print(f"  event_type attribute: {event.event_type}")
        # if hasattr(event, "content") and event.content:
        #     print(f"  Content: {event.content}")
        #     # Check for function calls in the content
        #     if hasattr(event.content, "parts") and event.content.parts:
        #         for part in event.content.parts:
        #             if hasattr(part, "function_call") and part.function_call:
        #                 print(f"     Tool name: {part.function_call.name}")
        #                 print(f"     Tool args: {part.function_call.args}")
        #                 print(f"     Tool id: {part.function_call.id}")
        #             if hasattr(part, "text") and part.text:
        #                 print(f"  Text response: {part.text[:200]}...")
        # if hasattr(event, "tool_calls") and event.tool_calls:
        #     print(f"  Tool calls: {event.tool_calls}")
        # if hasattr(event, "tool_name"):
        #     print(f"  Tool name: {event.tool_name}")

        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            break

    print(f"\n<<< Response:\n{final_response_text}")
    return final_response_text


if __name__ == "__main__":
    # asyncio.run(run_search("What is 25 plus 17?"))
    # asyncio.run(run_search("Search the web for the latest news about Barcelona football club today"))

    query = "What is the current stock price of Google and what are the top headlines about it today?"

    # Test the Gemini API with Google Search using litellm.completion
    # print("\n=== Testing with litellm.completion() ===\n")
    # try:
    #     response = query_gemini_with_google_search(query)
    #     print(f"Success! Response received.\n {response}")
    # except Exception as e:
    #     print(f"Error calling Gemini API: {e}")

    # Test the Gemini API with Google Search using plain HTTP requests
    # print("\n=== Testing with plain HTTP requests ===\n")
    # try:
    #     response_http = query_gemini_with_http_request(query)
    #     print("Success! Response received.\n")
    #     print("Response content:")
    #     if "choices" in response_http and response_http["choices"]:
    #         content = response_http["choices"][0].get("message", {}).get("content", "")
    #         print(content[:500] + "..." if len(content) > 500 else content)
    # except Exception as e:
    #     print(f"Error calling Gemini API via HTTP: {e}")

    # Test the company search function
    print("\n=== Testing Company Search ===\n")
    try:
        start_time = time.time()
        result = search_company_info(company_name="Swiss Ice Hockey Federation")
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("Company Information:")
        print(result["text"])
        print("\n\nGrounding URLs:")
        for url in result["grounding_urls"]:
            print(f"  - {url['title']}: {url['uri']}")
        print(f"\n\nTotal annotations: {len(result['annotations']) if result['annotations'] else 0}")
        print(f"\n\n⏱️  LATENCY MEASUREMENT:")
        print(f"   Total time: {elapsed_time:.2f} seconds ({elapsed_time*1000:.0f} ms)")
    except Exception as e:
        print(f"Error searching for company info: {e}")


# 2.  Website-Referenzen: https://www.sihf.ch/de/organization/about-us/ (Strategie, Mission, Unternehmenszahlen)

# 3.  Website-Referenzen: https://de.wikipedia.org/wiki/Swiss_Ice_Hockey_Federation (Definition als Dachorganisation, Geschichte)

# 4.  Website-Referenzen: https://bizfinder.ch/de/company/swiss-ice-hockey-federation-CHE107848055 (Zweck laut Handelsregister)

# 5.  Website-Referenzen: https://de.linkedin.com/company/sihf (Selbstbeschreibung, Mitarbeiterzahl)
# Über uns
# Über uns

# https://www.zefix.admin.ch/de/search/entity/list/firm/782174
# ZefixWebApp
