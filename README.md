AI Simulator Suite
Two Streamlit apps built on the OpenAI API — a job interview simulator and a debate simulator.

Job Interview Simulator (app.py)
You fill in your name, experience, and skills, then pick a seniority level, position, and company. The app spins up an AI interviewer and runs you through five questions. After each answer (starting from the second), a separate AI gives you quick feedback on how well you actually answered — not just whether it sounded good. At the end you get an overall score out of 10 and a written summary of your performance.
Debate Simulator (debate.py)
You pick a topic, set your position and the bot's position, and choose a difficulty level — Bad, Okay, or Good. The AI debater sticks to that level no matter how well or poorly you argue. After 10 rounds, a separate AI judge scores both sides from 1 to 100, quotes specific things each side said, and declares a winner.

Setup
You'll need Python 3.8+, an OpenAI API key, and the following packages:
pip install streamlit openai streamlit-js-eval
Add your key to .streamlit/secrets.toml:
OPENAI_API_KEY = "sk-..."
Then run whichever app you want:
streamlit run app.py
streamlit run debate.py
