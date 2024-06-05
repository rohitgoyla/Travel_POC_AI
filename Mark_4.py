import streamlit as st
from datetime import datetime
import openai
import requests
import os


# Set up API keys
openai.api_key = os.environ['api_key']
weather_api_key = '6d71539c0a4b340713b2a341cf10f5e0'


class DestinationDataNotFoundError(Exception):
    pass


def create_prompt(destination, travel_days):
    prompt = f"""
    I am planning a trip to {destination}. Here are the details:
    - Days to visit: {', '.join(travel_days)}
    - Consider the weather for each day.

    Please create a detailed itinerary for my trip.
    """
    return prompt


def get_weather(destination, date):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={destination}&appid={weather_api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise DestinationDataNotFoundError(f"Destination data for {destination} is not available.")


def fetch_weather_for_days(destination, days):
    weather_info = {}
    for day in days:
        date = datetime.strptime(day, "%Y-%m-%d").strftime("%Y-%m-%d")
        weather_data = get_weather(destination, date)
        weather_info[date] = weather_data
    return weather_info


def generate_itinerary(destination, travel_days):
    weather_info = fetch_weather_for_days(destination, travel_days)
    prompt = create_prompt(destination, travel_days)

    # Add weather information to the prompt
    for day, weather in weather_info.items():
        weather_details = f"Weather on {day}: {weather['weather'][0]['description']}, Temp: {weather['main']['temp']}K"
        prompt += f"\n{weather_details}"

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response


def calculate_cost(response):
    tokens_used = response.usage.total_tokens
    cost_per_token = 0.00006  # Sample cost
    total_cost = tokens_used * cost_per_token
    return tokens_used, total_cost


# Streamlit Interface
st.title("Travel Itinerary Planner")

# Input fields
destination = st.text_input("Enter your destination:")

# Single calendar date picker and multiselect for selected dates
selected_date = st.date_input("Select a travel date:", datetime.today())
if "travel_dates" not in st.session_state:
    st.session_state.travel_dates = []

if st.button("Add Date"):
    st.session_state.travel_dates.append(selected_date)
    st.session_state.travel_dates = list(set(st.session_state.travel_dates))  # Remove duplicates

# Display selected dates
st.write("Selected Travel Dates:")
st.session_state.travel_dates.sort()
for date in st.session_state.travel_dates:
    st.write(date.strftime("%Y-%m-%d"))

travel_days_str = [date.strftime("%Y-%m-%d") for date in st.session_state.travel_dates]

if st.button("Submit"):
    if destination and travel_days_str:
        try:
            itinerary_response = generate_itinerary(destination, travel_days_str)
            st.write(f"\nGenerated Itinerary:\n{itinerary_response.choices[0].message.content}")
            tokens_used, total_cost = calculate_cost(itinerary_response)
            st.write(f"\nTokens Used: {tokens_used}")
            st.write(f"Total Cost: ${total_cost:.4f}")
        except DestinationDataNotFoundError as e:
            st.error(e)
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please enter a destination and select at least one travel date.")
