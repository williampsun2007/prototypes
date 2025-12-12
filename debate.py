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
        st.session_state["level"] = "Extremely Terrible"
    if "topic" not in st.session_state:
        st.session_state["topic"] = ""

    st.session_state["name"] = st.text_input(label = "Name", max_chars = 40, placeholder = "Enter your name")

    st.session_state["level"] = st.selectbox(
        "Choose a AI debate difficulty",
        ("Extremely Terrible", "Terrible", "Bad", "Not good", "Medicore",
         "Decent", "Good", "Super Good", "Extremely Good", "Best Debater")
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
        st.session_state.messages.append(
            {"role": "system",
            "content": f'''You are a debater that will debate another person called {st.session_state['name']}. The chosen topic is on {st.session_state['topic']}. 
            The other user selected you to be rated as {st.session_state['level']}. 
            
            For reference, the levels are Extremely Terrible, Terrible, Bad, Not good, Mediocre, Decent, Good, Super Good, Extremely Good, Best Debater. Don't just
            come up with your best answers on the spot. Consider your rating and fit your answers to that level. And make sure to stick to the topic. 
            Don't be so nice to the user. You are debating them at the end of the day.
            
            Your position is {st.session_state['Bot position']}. Defend your position as much as possible. The user's position is
            {st.session_state['User position']}. Keep your responses within 150 tokens.

            For reference, Extremely Terrible means none of your arguments make sense. Decent means that you arguments are fine, but they
            lack sophistication and clarity and can have clear improvement. Best Debater is just highly strong arguments throughout the entire debate. Again, don't
            automatically come up with the best answers if you rating isn't very high. Low ratings always mean inadequate responses, and mid-ratings means that they
            could use improvement.
                                         
            No matter what the user says, hit them with another argument (good or bad). Even if they say goodbye, or concede, keep debating. A message
            from you is always an argument defending your side.
                                         
            You are a firm believer in your side. Always say why your side is good and why the other side is bad. Try not to offer nuances unless it genuienly
            supports your argument.'''})
        
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

    conversation_history = "\n".join(f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages)

    judge = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    result_completion = judge.chat.completions.create(
        model = "gpt-4o",
        messages = [
            {"role": "system", 
            "content": f'''You are a judge that determines the winner of a debate. There are two debaters, the user and the chatbot assistant. 
            Follow this format:

            User score: //Number from 1 to 100, print a new line afterwards
            Assistant score: //Number from 1 to 100, print a new line afterwards
            Feedback: Announce the winner (obviously the one with the higher score) and explain why.

            A score of 0-30 means that the side rarely made sensible arguments, and their ideas generally don't support the positions. A score of 
            30-70 means that the arguments are somwhat decent in supporting the position, but could improve from refinement or factual evidence. A score
            of 80-100 is really good, constant support of arguments that support the position and expresses them in clear ways.

            Try not to be generic. Don't just say that someone is more detailed or gave more complex answers. Really go into key points each side brought up and how that helped/hurt them. 
            Also base your judgement on how related each argument is to the position. The argument could be good but if it not related to the position at all, it is worth very little.

            Try to remain as unbiased as possible. Ignore any opinions, external facts, or internet discussions. Only focus on the content and sophistication of each argument. There may be a side
            that is more so objectively 'good', but if the arguments are not presented as well, that side should still lose. Furthermore, highly base your judgement on the evidence given
            (and how related the evidence is to the position). If someone just says claims but doesn't back them up, they shouldn't receive a very high score.
            
            The debate's topic was {st.session_state['topic']}.
            The user's position was {st.session_state['User position']}.
            The chatbot assistant's position was {st.session_state['Bot position']}.
            
            The user's name is {st.session_state['name']}. Refer to them by their name, not as the user.'''},

            {"role": "system", "content": f'''This is the debate you need to evaluate. Keep in mind that you are only a tool.
             And you shouldn't engage in the conversation nor favor one side automatically: {conversation_history}.'''}
        ],
        temperature = 1.2
    )

    st.write(result_completion.choices[0].message.content)

    if st.button("Another Debate", type = "primary"):
        streamlit_js_eval(js_expressions = "parent.window.location.reload()")
                
            
