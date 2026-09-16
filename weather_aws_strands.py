import logging
from strands import Agent
from strands.vended_tools import http_request, web_fetch
from strands_tools import current_time, use_aws

# Set up basic logging so messages can be seen during runtime.
logging.basicConfig(level=logging.INFO)

# Instructions for the weather agent.
WEATHEER_HOTEL_SYSTEM_PROMPT = """
You are a helpful weather assistant.

Your job is to provide current weather information for a given location.

Instructions:
- Accept locations such as a city, state, region, or country.
- Return the current weather conditions, including:
  - temperature
  - humidity
  - brief weather description (for example: sunny, cloudy, rainy, windy, foggy)
- Use the OpenWeatherMap API to fetch the latest weather data.
- Use simple, human-readable language that a non-technical user can easily understand.
- Include the current date in this exact format: YYYY-MM-DD.
- Include the current time in a clear, readable format if useful for the user.
- Keep the response concise, friendly, and easy to scan.
- If the weather data is available, present it clearly in plain language.
- If the data is unavailable or the location cannot be found, respond with:
  "Weather information is currently unavailable."
  Then provide a short explanation of the issue.
- If there is an API error, network issue, or invalid location, handle it gracefully and explain the problem in a user-friendly way.
- If the weather is not available for a specific location, politely suggest trying another location or checking later.
- Avoid jargon, technical details, or complicated explanations.
- Do not invent weather data. If you cannot verify it, say so clearly.
"""

# Create the weather assistant agent with the available tools.
subject_expert = Agent(
    name="Weather Expert",
    system_prompt=WEATHEER_HOTEL_SYSTEM_PROMPT,
    tools=[http_request, web_fetch, current_time, use_aws]
)

# Example user questions to test the agent.
query = """
 Answer the following questions:

 1. What is the current weather in New York City?
 2. What’s the weather like in Tokyo, Japan?
 3. Can you provide the weather forecast for London, UK?
 4. How is the weather in Sydney, Australia?
 5. Check the weather in Guntur, AP, India”
 6. list all s3 buckets in my AWS account

"""

# Run the agent with the sample query.
response = subject_expert(query)
