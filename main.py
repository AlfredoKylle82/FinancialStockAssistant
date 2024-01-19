import json
import openai
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf

openai.api_key = open('API_KEY', 'r').read()

def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].close)

def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1').Close
    return str(data.rolling(ndow=window).mean().iloc[-1])

def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14-1, adjust=False).mean()
    ema_down = down.ewm(com=14-1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100- (100 / (1*rs)).iloc[-1])

def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()

    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust=False)

    MACD_histogram = MACD - signal

    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'

def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data.Close)
    plt.title('{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.savefig('stock.png')
    plt.close()

functions = [
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (for example AAPL for Apple).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'calculate_SMA',
        'description': 'Calculates the Simple Moving Average (SMA) of a stock price over a specified window of time.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol.'
                },
                'window': {
                    'type': 'integer',
                    'description': 'The window size in days for the SMA calculation.'
                }
            },
            'required': ['ticker', 'window']
        }
    },
    {
        'name': 'calculate_EMA',
        'description': 'Calculates the Exponential Moving Average (EMA) of a stock price over a specified window of time.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol.'
                },
                'window': {
                    'type': 'integer',
                    'description': 'The window size in days for the EMA calculation.'
                }
            },
            'required': ['ticker', 'window']
        }
    },
    {
        'name': 'calculate_RSI',
        'description': 'Calculates the Relative Strength Index (RSI) of a stock.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol.'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'calculate_MACD',
        'description': 'Calculates the Moving Average Convergence Divergence (MACD) of a stock.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol.'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'plot_stock_price',
        'description': 'Plots the stock price of a company over the last year.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol.'
                }
            },
            'required': ['ticker']
        }
    }
]

available_functions = {
    'get_stock_price': get_stock_price,
    'calculate_SMA': calculate_SMA,
    'calculate_EMA': calculate_EMA,
    'calculate_RSI': calculate_RSI,
    'calculate_MACD': calculate_MACD,
    'plot_stock_prize': plot_stock_price
}

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.title('Stock Analysis Chatbot Assistant')
user_input = st.text_input('your input:')

if user_input:
    try:
        st.session_state['messages'].append({'role': 'user', 'content': f'{user_input}'})

        response = openai.chat.completions.create(
            model='gpt-3.5=turbo-0613',
            messages=[
                {
                  "role": "user",
                  "content": "Refactor the following Python code:\n\n'''\nwhile True:\n  mass = int(input(\"Enter the mass value: \"))\n  if mass > 0:\n    break\nwhile True:\n  acceleration = int(input(\"Enter the acceleration: \"))\n  if acceleration > 0:\n    break\nprint(\"The Force is\", mass * acceleration)\n'''"
                }
              ],
            temperature=0,
            max_tokens=4000,
            top_p=1,
            frequency_penalty=0.5,
            presence_penalty=0,
            functions=functions,
            function_call='auto'
        )

        response_message = response['choices'][0]['message']
        if response_message.get('funciton_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            if function_name in['get_stock_price', 'calculate_RSI', 'calculate_MACD', 'plot_stock_price']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_SMA', 'calculate_EMA']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}

            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            if function_name =='plot_stock_price':
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name': function_name,
                        'content': function_response
                    }
                )
                second_response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo-0613',
                    messages=st.session_state['messages']
                )
                st.text(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response['choices'][0]['message']['content']})
        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role': 'assistant', 'content': response_message['content']})
    except Exception as e:
        raise e




