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
                if at all.''',
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
                your position in the debate. (Again, keep your arguments at the right level.)'''})
        
    debater = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o"

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
                    max_tokens = 200,
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
        model = "gpt-4o",
        messages = [
            {"role": "system", 
            "content": f'''You are a judge that determines the winner of a debate. In the following conversation, messages labeled 
            [user] are from the human debater, and messages labeled [assistant] are from the chatbot debater. 
            Do not assume any other mapping. Before you give the feedback, score both [user] and [assistant] from 1 to 100.
            The user's name is {st.session_state['name']}. Refer to them by {st.session_state['name']}, not 'user'.

            Follow this format, printing a new line after each score:

            [user] score: //Your Score (new line afterwards)
            [assistant] score: //Your Score (new line afterwards)
            Feedback: Announce the winner (obviously the one with the higher score) and explain why.

            A score of 0-30 means that the side rarely made sensible arguments, and their ideas generally don't support the positions. A score of 
            30-70 means that the arguments are somewhat decent in supporting the position, but could improve from refinement or factual evidence. A score
            of 80-100 is really good, CONSTANT support of arguments that support the position and expresses them in clear ways.

            Really go into key points each side brought up and how that helped/hurt them. Reward the side who constantly gives good reasoning and solid evidence, 
            and penalize the side that fails to make good arguments or gives little details. A side could sound 'unconfident', and while that should generally be taken 
            as a bad thing, if the point made is decent then it should add some value to the score.
            
            Also base your judgement on how related each argument is to the position. The argument could be good but if it not related to the position at all, it is worth very little.
            While remaining balanced, pay greater attention to bad arguments. If more bad arguments are given than good arguments, a score of <60 should be given. Obviously, if one side
            constantly says weird or non-sensical things, they should receive a low score. Even just a few messages that are unrelated should penalize the score a lot.

            Do not just focus on good arguments. If anything, pay just as much attention, if not more, to bad arguments. Think of it like this: you are responsible
            for giving points, but you are equally responsible of taking away points for unrelated or incoherent arguments. Unrelated things should be paid much attention to.

            Ignore any opinions, external facts, or internet discussions. There may be a side that is more so objectively 'good', but if the arguments are not presented as well, that side should 
            still lose. If someone just says claims but doesn't back them up, they shouldn't receive a very high score.
            
            The debate's topic was {st.session_state['topic']}.
            [user] position was {st.session_state['User position']}.
            [assistant] position was {st.session_state['Bot position']}.'''},

            {"role": "system", "content": f'''This is the debate you need to evaluate. Keep in mind that you are only a tool.
             And you shouldn't engage in the conversation nor favor one side automatically: {conversation_history}.'''}
        ],
        temperature = 1.1
    )

    st.write(result_completion.choices[0].message.content)

    if st.button("Another Debate", type = "primary"):
        streamlit_js_eval(js_expressions = "parent.window.location.reload()")