# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import openai
# import os
# from dotenv import load_dotenv
# app = Flask(__name__)

# CORS(app)

# # CORS(app, resources={r"/suggest-business": {"origins": ""}})


# load_dotenv()

# openai.api_key = os.getenv('OPENAI_API_KEY')

# def get_suggestions(query):
#     response = openai.ChatCompletion.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": "You are an expert business consultant to provide business ideas with detailed analysis."},
#             {"role": "user", "content": f"""
#             Provide AI-driven business ideas for: {query}. For each idea, provide:

#             1. 1. **Business Idea & Concept**  
#                - A brief overview of the business opportunity.
#                - The market demand and scalability.
#             2.**AI Integration & Technology Recommendations**  
#                - AI solutions that can be implemented  
#                - Real-world examples of successful AI applications in this industry.
#             3. **Expected ROI & Profitability**:
#                 - Short-term vs long-term ROI analysis.  
#                 - Estimated revenue growth and cost-saving potential.  
#             4. **Key Business Elements**: 
#                 - Core components required for effective implementation.  
#                 - Operational efficiency improvements using AI.  
#             5. **Growth Strategy**:
#                 - How to expand and increase revenue using AI.  
#                 - Steps to ensure sustainability in a competitive market.  
#             6. **Risk Analysis & Mitigation**  
#                - Common risks involved in this business model.  
#                - AI-based risk mitigation strategies.  
#             7. **Industry Trends & Competitive Insights**: 
#                 - How has the industry evolved in the past 5 years?  
#                 - What are the latest innovations in 2024?  
#             8. **Innovative AI Solutions**: 
#                 **Innovative AI Solutions**  
#                - **Unique AI solutions** based on the latest technologies.  
#                - **Real-world, effective solution ideas** that have been successfully implemented in similar industries.  
#                - AI advancements that can provide a competitive advantage.
#             9. **Additional Recommendations**  
#                - Unique strategies to optimize efficiency and customer experience.  
#                - AI-powered marketing and automation tools.  
#                - Future-proofing the business with emerging AI trends.
#             Provide your response in a structured, easy-to-read format.
#             """}
#         ]
#     )
#     return response.choices[0].message.content

# @app.route('/suggest-business', methods=['POST'])
# def suggest_business():
#     data = request.get_json()
#     query = data.get("query")

#     if not query:
#         return jsonify({"error": "Query is required"}), 400

#     suggestions = get_suggestions(query)
#     return jsonify({"suggestions": suggestions})

# if __name__ == '__main__':
#     app.run(debug=True)

import json
import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv


app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/suggest-business": {"origins": ""}})
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

# client = openai
search_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_website",
            "description": "Fetch and extract content from a specified website URL.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to retrieve data from.",
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
]

# Define the prompt for generating business ideas
def generate_prompt(extracted_text):
    return f"""
    Based on the following website content, provide AI-driven business ideas with detailed analysis:

    website_content: {extracted_text}

    For each idea, include:

    1. **Business Idea & Concept**
       - A brief overview of the business opportunity.
       - The market demand and scalability.
    2. **AI Integration & Technology Recommendations**
       - AI solutions that can be implemented.
       - Real-world examples of successful AI applications in this industry.
    3. **Expected ROI & Profitability**
       - Short-term vs long-term ROI analysis.
       - Estimated revenue growth and cost-saving potential.
    4. **Key Business Elements**
       - Core components required for effective implementation.
       - Operational efficiency improvements using AI.
    5. **Growth Strategy**
       - How to expand and increase revenue using AI.
       - Steps to ensure sustainability in a competitive market.
    6. **Risk Analysis & Mitigation**
       - Common risks involved in this business model.
       - AI-based risk mitigation strategies.
    7. **Industry Trends & Competitive Insights**
       - How has the industry evolved in the past 5 years?
       - What are the latest innovations in 2024?
    8. **Innovative AI Solutions**
       - Unique AI solutions based on the latest technologies.
       - Real-world, effective solution ideas that have been successfully implemented in similar industries.
       - AI advancements that can provide a competitive advantage.
    9. **Additional Recommendations**
       - Unique strategies to optimize efficiency and customer experience.
       - AI-powered marketing and automation tools.
       - Future-proofing the business with emerging AI trends.

    Provide your response in a structured, easy-to-read format.
    """

system_prompt = {
    "role": "system",
    "content": (
        "You are an expert business consultant providing detailed, AI-driven business ideas with comprehensive analysis. "
        "When responding, include the following details for each idea:\n\n"
        
        "1. **Business Idea & Concept**:\
            Provide a brief overview of the business opportunity and analyze its market demand and scalability.\n\n"
        "2. **AI Integration & Technology Recommendations**: \
            Outline AI solutions that can be implemented, including real-world examples of successful AI applications in the industry.\n\n"
        "3. **Expected ROI & Profitability**: \
            Analyze short-term versus long-term ROI, and estimate revenue growth along with potential cost-saving benefits.\n\n"
        "4. **Key Business Elements**:\
            Identify the core components required for effective implementation and describe how operational efficiency can be improved using AI.\n\n"
        "5. **Growth Strategy**: \
            Explain strategies to expand revenue using AI, including actionable steps to ensure sustainability in a competitive market.\n\n"
        "6. **Risk Analysis & Mitigation**:\
            Discuss common risks associated with the business model and propose AI-based strategies for mitigating these risks.\n\n"
        "7. **Industry Trends & Competitive Insights**:\
            Analyze how the industry has evolved over the past five years and highlight the latest innovations as of 2024.\n\n"
        "8. **Innovative AI Solutions**: \
            Recommend unique AI solutions based on the latest technologies, including effective implementations in similar industries, and discuss advancements that provide a competitive edge.\n\n"
        "9. **Additional Recommendations**: \
            Offer strategies to optimize efficiency and customer experience, suggest AI-powered marketing and automation tools, "
        "and discuss methods for future-proofing the business with emerging AI trends.\n\n"
        
        "Present your response in a structured, clear, and easy-to-read format."
    )
}


def search_website(url):
    """
    Fetches HTML content from a URL and extracts its text.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements to avoid non-relevant content
        for tag in soup(['script', 'style']):
            tag.decompose()
        text = soup.get_text(separator=' ')
        # Clean up whitespace
        text = ' '.join(text.split())
        return str(text)
    except Exception as e:
        print("Error fetching website:", e)
        return None


def generate_response(client, messages, tools=None, tool_choice="auto", model="gpt-4o-2024-11-20"):
    """
    This function makes calls to the Chat Completions API to generate the chat response.
    """
    try:
        # response = client.completions.create(
        #     model=model, messages=messages, tools=tools, tool_choice=tool_choice
        # )
        # return response
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice   
        )
        return response
        
    except Exception as e:
        print("Unable to generate Chat Completion response")
        print(f"Exception: {e}")
        return e


def call_function(name: str, args: dict):
    """
    Helper function to handle the function calling.
    """
    if name == "search_website":
        return search_website(**args)


def tool_calling(tool):
    tool_id = tool.id
    tool_name = tool.function.name
    tool_args = json.loads(tool.function.arguments)

    print(f"Running ({tool_name}) tool...")

    result = call_function(name=tool_name, args=tool_args)
    if result:
        result = generate_prompt(result)
        print("Tool Response", result)

    return {"role": "tool", "tool_call_id": tool_id, "content": str(result)}


def get_suggestions(query, system=system_prompt, client=None, model="gpt-4o-2024-11-20"):
    """
    This function will generate the final response.
    """
    # Initial Prompt
    # messages = [system, {"role": "user", "content": query}]
    messages = [system]
    messages.append(
        {
            "role": "user",
            "content": query,
        }
    )
    # print(f"Initial prompt:\n{json.dumps(messages, indent=2)}")

    try:
        # Invoke model first time
        response = generate_response(client=client,messages=messages, tools=search_tools, model=model)
        
        response_messages = response.choices[0].message
        # print(f"Initial output : {response_messages}")

        # Adding the intermediate messages into messages list
        messages.append(response_messages)

        tool_calls = getattr(response_messages, 'tool_calls', None)

        if tool_calls:
            for tool in tool_calls:
                tool_msg = tool_calling(tool=tool)
                messages.append(tool_msg)

            response = generate_response(client=client, messages=messages, tools=search_tools)

        # print(f"Final Response : {response}")
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error Occured During generate response {e}")
        # print(f"Exception: {e}")
        return f"Exception: {e}"

@app.route('/suggest-business', methods=['POST'])
def suggest_business():
    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "Query is required"}), 400

    suggestions = get_suggestions(query)
    return jsonify({"suggestions": suggestions})

if __name__ == '__main__':
    app.run(debug=True)
