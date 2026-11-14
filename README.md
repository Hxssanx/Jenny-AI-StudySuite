# Jenny-AI-StudySuite

uhh so i made this ai study app cause of a hackathon that ended up ghosting me. anyway here it is i guess. 

## what it does
- searches the web when it doesn't know stuff (powered by duckduckgo)
- makes quizzes for when u actually wanna study
- flashcards cuz why not
- reads your notes or yt links and summarizes them so u dont have to watch a 20 min video

## tech stack
- streamlit (frontend)
- groq api (qwen model)
- python stuff

## how to run it cuz idk why you'd want to
1. clone this repo
2. install the stuff:
   ```bash
   pip install -r requirements.txt
   ```
3. make a `.env` file and put your key in there (obviously don't leak your key on github):
   ```env
   GROQ_API_KEY="your_key_here"
   ```
4. run it:
   ```bash
   streamlit run app.py
   ```
