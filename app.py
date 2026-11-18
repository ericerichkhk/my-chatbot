import os
import streamlit as st
from openai import OpenAI

st.title("ABC Bank Customer Service")

# 1. Connect to OpenRouter safely via Streamlit Secrets
api_key = st.secrets.get("OPENROUTER_API_KEY", os.environ.get("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY_HERE"))
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai")

# 2. Define Main Menu and Sub-Menu Categories
SUB_MENUS = {
    "1. Deposit / Withdrawal": [
        "ATM Withdrawal Limit",
        "Counter Deposit Rules",
        "⬅ Back to Main Menu",
    ],
    "2. Interest Rates": [
        "HKD Savings Rate",
        "USD Savings Rate",
        "⬅ Back to Main Menu",
    ],
    "3. Fixed Deposit": [
        "3-Month HKD Fixed Deposit Rate",
        "Minimum Deposit Amount",
        "Early Withdrawal Rules",
        "⬅ Back to Main Menu",
    ],
    "4. Credit Card Application": [
        "Income & Age Requirements",
        "How to Apply",
        "⬅ Back to Main Menu",
    ],
    "5. Branch Addresses": [
        "Hong Kong Island Branch",
        "Kowloon Branch",
        "Opening Hours",
        "⬅ Back to Main Menu",
    ],
}

MAIN_MENU_OPTIONS = list(SUB_MENUS.keys()) + ["6. Transfer to Human Agent"]

# 3. Define your company knowledge base and strict AI rules
SYSTEM_PROMPT = """
You are a customer service chatbot for ABC Bank.
Your job is to filter the user's question and answer ONLY using the approved knowledge base below.

APPROVED KNOWLEDGE BASE:
- ATM Withdrawal Limit: Daily ATM withdrawal limit is HK$20,000 per card.
- Counter Deposit Rules: Cash and cheque deposits at branch counters are free during business hours.
- HKD Savings Rate: Standard HKD savings account interest rate is 0.875% p.a.
- USD Savings Rate: Standard USD savings account interest rate is 1.25% p.a.
- 3-Month HKD Fixed Deposit Rate: Currently 3.5% p.a. for new funds.
- Minimum Deposit Amount: Minimum fixed deposit amount is HK$10,000 (or US$1,500).
- Early Withdrawal Rules: Early uplift of a fixed deposit before maturity forfeits accrued interest and incurs a HK$200 handling fee.
- Income & Age Requirements: Credit card applicants must be 18 or older with a minimum annual income of HK$150,000.
- How to Apply: Apply online via the ABC Bank mobile app with your HKID and latest 3 months' bank statements.
- Hong Kong Island Branch: Main Branch is located at 1 Queen's Road Central.
- Kowloon Branch: Kowloon Branch is located at 680 Nathan Road, Mong Kok.
- Opening Hours: All branches are open Monday to Friday, 9:00 AM - 5:00 PM (closed on Saturdays, Sundays, and public holidays).

STRICT RULES:
1. Match the user's keywords or selected menu option to the approved facts above.
2. Reply in the same language the customer uses (English, Traditional Chinese, or Cantonese).
3. Keep answers polite, clear, and concise.
4. After answering, ask if they need help with anything else.
5. If the user asks about anything NOT covered in the knowledge base (such as lost cards, account balances, mortgages, or complaints), DO NOT guess or make up an answer. Instead, reply ONLY with the exact tag: [TRANSFER_TO_AGENT]
"""

# 4. Initialize chat state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome to ABC Bank! What sector of banking service do you need help with today? Choose an option below or type your question:",
        }
    ]
    st.session_state.current_menu = "MAIN"
    st.session_state.escalated = False

# 5. Handle menu navigation or OpenRouter AI query
def handle_selection(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})

    if user_text == "6. Transfer to Human Agent":
        st.session_state.escalated = True
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Connecting you to a human customer service agent now. Please hold..."
        })
        return

    if user_text == "⬅ Back to Main Menu":
        st.session_state.current_menu = "MAIN"
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Sure! Please select a main banking service below or type your question:"
        })
        return

    if user_text in SUB_MENUS:
        st.session_state.current_menu = user_text
        clean_name = user_text.split(". ", 1)[-1]
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"What specific information do you need about **{clean_name}**? Choose a topic below or type your question:"
        })
        return

    # Send question to OpenRouter (free model router)
    with st.spinner("Checking banking information..."):
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=api_messages,
            temperature=0.1
        )
        reply = response.choices[0].message.content.strip()

    if "[TRANSFER_TO_AGENT]" in reply:
        st.session_state.escalated = True
        handoff_msg = (
            "I don't have the information needed to answer that safely. "
            "I am transferring you to a human customer service agent now. Please hold..."
        )
        st.session_state.messages.append({"role": "assistant", "content": handoff_msg})
    else:
        st.session_state.messages.append({"role": "assistant", "content": reply})

# 6. Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Display active menu buttons
if not st.session_state.escalated:
    if st.session_state.current_menu == "MAIN":
        st.write("**Main Services:**")
        buttons_to_show = MAIN_MENU_OPTIONS
    else:
        st.write(f"**{st.session_state.current_menu} — Sub-Topics:**")
        buttons_to_show = SUB_MENUS[st.session_state.current_menu]

    cols = st.columns(2)
    for idx, option in enumerate(buttons_to_show):
        if cols[idx % 2].button(option, use_container_width=True):
            handle_selection(option)
            st.rerun()

# 8. Handle typed questions or human agent queue notice
if st.session_state.escalated:
    st.warning("Connected to Human Agent Queue — AI responses are paused.")
    if st.button("Start New AI Chat"):
        st.session_state.clear()
        st.rerun()
else:
    if prompt := st.chat_input("Or type your question here..."):
        handle_selection(prompt)
        st.rerun()
