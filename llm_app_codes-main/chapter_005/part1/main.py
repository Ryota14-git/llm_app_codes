# Github: https://github.com/naotaka1128/llm_app_codes/chapter05/part1/main.py

import traceback
import streamlit as st

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# models
from langchain_openai import ChatOpenAI


import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

###### dotenv を利用しない場合は消してください ######
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    import warnings
    warnings.warn("dotenv not found. Please make sure to set your environment variables manually.", ImportWarning)
################################################


SUMMARIZE_PROMPT = """以下のコンテンツについて、内容を300文字程度でわかりやすく要約してください。

========

{content}

========

日本語で書いてね！
"""


def init_page():
    st.set_page_config(
        page_title="Website Summarizer",
        page_icon="🤗"
    )
    st.header("Website Summarizer 🤗")
    st.sidebar.title("Options")


def select_model(temperature=0):
    models = ("GPT-3.5", "GPT-4", "Claude 3.5 Sonnet", "Gemini 1.5 Pro")
    model = st.sidebar.radio("Choose a model:", models)
    if model == "GPT-3.5":
        return ChatOpenAI(
            temperature=temperature,
            model_name="gpt-3.5-turbo"
        )
    elif model == "GPT-4":
        return ChatOpenAI(
            temperature=temperature,
            model_name="gpt-4o"
        )
   


def init_chain():
    llm = select_model()
    prompt = ChatPromptTemplate.from_messages([
        ("user", SUMMARIZE_PROMPT),
    ])
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    return chain


def validate_url(url):
    """ URLが有効かどうかを判定する関数 """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_content(url):
    try:
        with st.spinner("Fetching Website ..."):
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            # なるべく本文の可能性が高い要素を取得する
            if soup.main:
                return soup.main.get_text()
            elif soup.article:
                return soup.article.get_text()
            else:
                return soup.body.get_text()
    except:
        st.write(traceback.format_exc())  # エラーが発生した場合はエラー内容を表示
        return None


MODEL_PRICES = {
    "input": {
        "gpt-3.5-turbo": 0.5 / 1_000_000,
        "gpt-4o": 5 / 1_000_000
    },
    "output": {
        "gpt-3.5-turbo": 1.5 / 1_000_000,
        "gpt-4o": 15 / 1_000_000,
    }
}

def get_message_counts(text):
    if "gemini" in st.session_state.model_name:
        return st.session_state.llm.get_num_tokens(text)
    else:
        # Claude 3 はトークナイザーを公開していないので、tiktoken を使ってトークン数をカウント
        # これは正確なトークン数ではないが、大体のトークン数をカウントすることができる
        if "gpt" in st.session_state.model_name:
            encoding = tiktoken.encoding_for_model(st.session_state.model_name)
        else:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")  # 仮のものを利用
        return len(encoding.encode(text))

def calc_and_display_costs():
    output_count = 0
    input_count = 0
    for role, message in st.session_state.message_history:
        # tiktoken でトークン数をカウント
        token_count = get_message_counts(message)
        if role == "ai":
            output_count += token_count
        else:
            input_count += token_count

    # 初期状態で System Message のみが履歴に入っている場合はまだAPIコールが行われていない
    if len(st.session_state.message_history) == 1:
        return

    input_cost = MODEL_PRICES['input'][st.session_state.model_name] * input_count
    output_cost = MODEL_PRICES['output'][st.session_state.model_name] * output_count
    if "gemini" in st.session_state.model_name and (input_count + output_count) > 128000:
        input_cost *= 2
        output_cost *= 2

    cost = output_cost + input_cost

    st.sidebar.markdown("## Costs")
    st.sidebar.markdown(f"**Total cost: ${cost:.5f}**")
    st.sidebar.markdown(f"- Input cost: ${input_cost:.5f}")
    st.sidebar.markdown(f"- Output cost: ${output_cost:.5f}")


def main():
    init_page()
    chain = init_chain()

    # ユーザーの入力を監視
    if url := st.text_input("URL: ", key="input"):
        is_valid_url = validate_url(url)
        if not is_valid_url:
            st.write('Please input valid url')
        else:
            if content := get_content(url):
                st.markdown("## Summary")
                st.write_stream(chain.stream({"content": content}))
                st.markdown("---")
                st.markdown("## Original Text")
                st.write(content)

    # コストを表示する場合は第3章と同じ実装を追加してください
    calc_and_display_costs()


if __name__ == '__main__':
    main()
