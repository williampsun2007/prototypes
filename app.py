from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title = "Job Interview Simulator", page_icon = "💬")
st.title("Interview Simulator")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
      st.session_state.messages = []
if "question_response" not in st.session_state:
    st.session_state.question_response = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    if ("name" in st.session_state and st.session_state["name"] != "") and ("experience" in st.session_state and st.session_state["experience"] != "") and ("skills" in st.session_state and st.session_state["skills"] != ""):
        st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:
    st.subheader('Personal information', divider = 'rainbow')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(label = "Name", max_chars = 40, placeholder = "Enter your name")

    st.session_state["experience"] = st.text_area(label = "Experience", value = "", height = None, 
                          max_chars = 200, placeholder = "Describe your experience")

    st.session_state["skills"] = st.text_area(label = "Skills", value = "", height = None, max_chars = 200, placeholder = "List your skills")

    st.subheader("Company and Position", divider = "rainbow")

    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
           "Choose level",
           key = "visibility",
          options = ["Junior", "Mid-level", "Senior"],
      )

    with col2:
        st.session_state["position"] = st.selectbox(
           "Choose a position",
          ("Data Scientist", "Data engineer", "ML Engineer", "BI Analyst", "Financial Analyst"))
    
    st.session_state["company"] = st.selectbox(
      "Choose a Company",
     ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify")
    )

    if st.button("Start Interview", on_click = complete_setup):
        if st.session_state.setup_complete:
            st.write("Setup complete. Starting interview...")
        else:
            st.write("You have not filled out all your personal information.")

if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        '''
        Start by introducing yourself.
        ''',
        icon = "👋"
    )

    if not st.session_state.messages:
        st.session_state.messages.append({"role": "system",
                                          "content": f'''
                                           You are a HR executive that interviews an interviewee called {st.session_state['name']} with
                                           experience {st.session_state['experience']} and skills {st.session_state['skills']}. You should
                                           interview him for the position {st.session_state['level']} {st.session_state['position']} at the company
                                           {st.session_state['company']}.
                                           '''})
        
    if not st.session_state.question_response:
        st.session_state.question_response = [{"role": "system",
                                               "content": f'''You are a feedback giver for an interviewee called {st.session_state['name']}.
                                               Provided will be questions given from another AI bot, and the response given by the user. You are
                                               not directly interviewing the user. Instead, you are giving them short, 1-2 sentence feedback
                                               on their response to the bot's question. Judge things based on how related their response is to
                                               the question, how cohesive it is, and whether or not it makes them look good. Also give it a rating
                                               out of 10. Really base your feedback on how well it answers the question, even if it sounds good.
                                               
                                               The bot asking the question has the role 'assistant'.'''}]

    client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])
    feedbacker = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
       st.session_state.openai_model = "gpt-4o"

    for message in st.session_state.messages:
       if message["role"] != "system":
          with st.chat_message(message["role"]):
             st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer.", max_chars = 1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                st.session_state.question_response.append({"role": "user", "content": prompt})

            if st.session_state.user_message_count > 0:
                with st.chat_message("assistant", avatar = "👩‍🏫"):
                    feedback = feedbacker.chat.completions.create(
                        model = st.session_state.openai_model,
                        messages = [
                            {"role": m['role'], "content": m['content']}
                            for m in st.session_state.question_response
                        ],
                        stream = True,
                        temperature = 1.1
                    )
                    st.write_stream(feedback)

            with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model = st.session_state.openai_model,
                        messages = [
                            {"role": m['role'], "content": m['content']}
                            for m in st.session_state.messages
                        ],
                        stream = True,
                        temperature = 1.1
                    )
                    response = st.write_stream(stream)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.question_response = st.session_state.question_response[0 : 1]
            st.session_state.question_response.append({"role": "assistant", "content": response})
            st.session_state.user_message_count += 1
            
            if st.session_state.user_message_count >= 5:
                st.session_state.chat_complete = True
        
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click = show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model = "gpt-4o",
        messages = [
            {"role": "system", "content": f'''You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format: 
             Overall Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questions.

             Try not to give generic feedback. Really go into the user's responses, pick out what you like or don't like, and use that to support
             your response. A score 1-3 means that the user really doesn't know what they are doing. A score 4-7 means that they show some skill
             and maybe offer a little, but you are really not sure about them. A score of 8-10 means they are almost the perfect fit. Make sure that
             the user is ultimately talking about why you should hire them at {st.session_state['company']} with position {st.session_state['position']}.
             If they don't talk about this specifically (such as talking about another position or company), give them a lower score.
             '''},
            {"role": "user", "content": f'''This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't
             engage in the conversation: {conversation_history}'''}
        ],
        temperature = 1.1
    )

    st.write(feedback_completion.choices[0].message.content)    

    if st.button("Restart Interview", type = "primary"):
        streamlit_js_eval(js_expressions = "parent.window.location.reload()")