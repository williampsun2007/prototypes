from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title = "Debate Simulator", page_icon = "💬")
st.title("Debate Simulator")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "winner_decided" not in st.session_state:
    st.session_state.winner_decided = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debate_complete" not in st.session_state:
    st.session_state.debate_complete = False

def complete_setup():
    if ("name" in st.session_state and st.session_state["name"] != "") and ("topic" in st.session_state and st.session_state["topic"] != ""):
        st.session_state.setup_complete = True 

def decide_winner():
    st.session_state.winner_decided = True

if not st.session_state.setup_complete:
    st.subheader("Debate Customization", divider = 'rainbow')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "level" not in st.session_state:
        st.session_state["level"] = "Bad"
    if "topic" not in st.session_state:
        st.session_state["topic"] = ""

    st.session_state["name"] = st.text_input(label = "Name", max_chars = 40, placeholder = "Enter your name")

    st.session_state["level"] = st.selectbox(
        "Choose a AI debate difficulty",
        ("Bad", "Okay", "Good")
    )

    st.session_state["topic"] = st.text_area(label = "Topic", value = "", height = None, max_chars = 200, placeholder = "Type in your debate topic")

    st.session_state["User position"] = st.text_area(label = "Your Position", value = "", height = None, max_chars = 200, placeholder = "Type in your position (try to make it related to the topic)")
    st.session_state["Bot position"] = st.text_area(label = "Bot Position", value = "", height = None, max_chars = 200, placeholder = "Type in the chatbot's position (try to make it related to the topic and opposite of your side)")

    if st.button("Start Debate", on_click = complete_setup):
        if st.session_state.setup_complete:
            st.write("Setup complete. Starting debate...")
        else:
            st.write("You have not filled out all the information needed for the debate to start.")

if st.session_state.setup_complete and not st.session_state.winner_decided and not st.session_state.debate_complete:

    st.info(
        f'''
        This is a debate simulator on the topic {st.session_state["topic"]}\n
        The chatbot you are going against is rated as {st.session_state["level"]}\n   
        Your position is: {st.session_state['User position']}\n
        Chat bot's position is: {st.session_state['Bot position']}\n
        '''
    )

    if not st.session_state.messages:
        behavior_map = {
            'Bad': '''While you say things that are in favor of your side, they don't make a lot of sense and are vulnerable to rebuttals.
                You rarely backup your answers and you seem unsure. Don't come up with great responses, only ones that barely support your position,
                if at all. Don't just be bad by saying words like 'maybe', 'I think', etc, or just being unsure. Always give poor arguments that barely support
                the position at all, such as nonsense ideas or inefficient reasoning.''',
            'Okay': '''You make arguments that somewhat support your side, and while there might be a correspondence between your argument and position, it
                lacks strength and details that could further support it. Say things that might support your position, but could use a lot
                more improvement. You are not the worst debater but you purposefully aren't great either.''',
            'Good': '''You make arguments that favor your side, and while there is a clear correspondence that supports your position, it
                lacks strength and details that could further support it. Say things that definitely support your position, but could use a lot
                more improvement. You are not the worst debater but you purposefully aren't great either.'''
        }

        st.session_state.messages.append(
                {"role": "system",
                "content": f'''You are a debater that will debate another person called {st.session_state['name']}. The chosen topic is on {st.session_state['topic']}. 
                The other user selected you to be rated as {st.session_state['level']}. {behavior_map[st.session_state['level']]}
            
                Your position is {st.session_state['Bot position']}. Defend your position, but at the level '{st.session_state['level']}'.
                For reference, the possible levels are 'Bad', 'Okay', and 'Good'. The user's position is {st.session_state['User position']}. No matter how the other side
                responds, always make sure your arguments are consistently at the right level. Keep your responses within 500 characters.
                                         
                No matter what the user says, even if they say goodbye, you win, let's stop, etc., send another argument (at the level {st.session_state['level']}.
                Just keep the debate going until it ends. Never send anything that agrees with the user, supports the other position, or anything that undermines
                your position in the debate. (Again, keep your arguments at the right level.)
                
                Also, ensure that all arguments are at the right level, which for you is {st.session_state['level']}. Do not start to give better arguments if your opponent
                gives better arguments, and do not give worse arguments if your opponent gives worse arguments. Always be consistent at the right difficulty.'''})
        
    debater = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-5.2"

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 10:
        if prompt := st.chat_input("Your argument", max_chars = 500):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                stream = debater.chat.completions.create(
                    model = st.session_state.openai_model,
                    messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    max_completion_tokens = 200,
                    stream = True,
                    temperature = 1.1
                )
                response = st.write_stream(stream)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.user_message_count += 1

            if st.session_state.user_message_count >= 10:
                st.session_state.debate_complete = True

if st.session_state.debate_complete and not st.session_state.winner_decided:
    if st.button("Get Results", on_click = decide_winner):
        st.write("Deciding winner...")

if st.session_state.winner_decided:
    st.subheader("Results")

    conversation_history = "\n".join(
    f"[{msg['role']}]: {msg['content']}" for msg in st.session_state.messages if msg['role'] != "system"
    )

    judge = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    result_completion = judge.chat.completions.create(
        model = "gpt-5.2",
        messages = [
            {"role": "system", 
            "content": f'''You are a judge that determines the winner of a debate. In the following conversation, messages labeled 
            [user] are from the human debater, and messages labeled [assistant] are from the chatbot debater. 
            Do not assume any other mapping. Before you give the feedback, score both [user] and [assistant] from 1 to 100.
            The user's name is {st.session_state['name']}. Refer to them by {st.session_state['name']}, not 'user'.

            The debate's topic was {st.session_state['topic']}. 
            [user] position was {st.session_state['User position']}. 
            [assistant] position was {st.session_state['Bot position']}.

            Follow this format, printing a new line after each score:

            [user] score: //Your Score (then print new line)
            [assistant] score: //Your Score (then print new line)
            Announce the winner (one with the higher score) and explain why.

            Here are 7 rules you must strictly follow to determine the score of each side and the winner of the debate:

            1. A score of 0-30 means that the side rarely made any sensible argument and their ideas generally do little to help. A score of 30-70 means 
            that the arguments somewhat supported the position, but often lack detail and could use a lot more suport. A score of 70-100 means that arguments 
            are used with great detail and evidence CONSTANTLY, supporting the specific side of the user.

            2. Pay attention to bad arguments just as much as good arguments, and even try to pay more attention to bad arguments. Some arguments can be good,
            but if a significant portion is bad, the score should be lowered a lot.

            3. Check if the arguments actually support the position that the side is supposed to support. The content of a message can sound good, but if it does
            not support the position, or even goes against the position, the side should be given a low score. Keep the position greatly in mind.

            4. Really go into the key points each side brought up and how that helped or hurt them. Don't just give general feedback, but instead go into the details
            of what a side said and how that rewarded or penalized them.

            5. Ignore anything related to the 'morality' of a specific position, and solely go based on what each side of the debate says. One side can be more objectively
            'good', but at the end of the day, the arguments used is what matters the most. If the 'good' side gives worse arguments, they should lose.

            6. The number one thing you should pay attention to for each side is what they say, relative to their position. Their arguments have to SUPPORT their side in order
            to receive a good score. If they are related to the topic and are even somewhat detailed, but don't support the position at all, they should lose. 

            7. A side can sometimes give good arguments, but if they also often give arguments that don't support the position, are unrelated, or even go against the position,
            they should receive a low score. You are equally responsible for taking away points as you are giving points.'''},

            {"role": "system", "content": f'''This is the debate you need to evaluate. Keep in mind that you are only a tool.
             And you shouldn't engage in the conversation nor favor one side automatically: {conversation_history}.'''}
        ],
        temperature = 1.1
    )

    st.write(result_completion.choices[0].message.content)

    if st.button("Another Debate", type = "primary"):
        streamlit_js_eval(js_expressions = "parent.window.location.reload()")