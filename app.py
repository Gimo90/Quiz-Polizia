import pandas as pd
import random
import streamlit as st
import os
import hashlib
from datetime import datetime

st.set_page_config(page_title="Quiz Polizia di Stato", layout="wide")

st.markdown("""
    <style>
    body {
        font-weight: bold;
        font-family: 'Helvetica', sans-serif;
        background-color: #f4f4f5;
    }
    .block-container {
        padding: 2rem 2rem 2rem 2rem;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        font-family: 'Helvetica', sans-serif;
    }
    .stSelectbox label, .stRadio label {
        font-size: 16px;
        color: #f4f4f5; /* White text for better contrast on dark background */
        font-family: 'Helvetica', sans-serif;
        font-weight: bold;
    }
    .stMarkdown, .stDataFrame, .stSubheader {
        background-color: #f4f4f5;
        padding: 1.5em;
        border-radius: 10px;
        margin-bottom: 1em;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
        font-family: 'Helvetica', sans-serif;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------- USER MANAGEMENT ----------
USERS_FILE = "users.csv"
STATS_FILE = "performance.csv"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> pd.DataFrame:
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password_hash"])


def save_user(username: str, password: str) -> bool:
    users = load_users()
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password)]], columns=["username", "password_hash"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USERS_FILE, index=False)
    return True


def authenticate(username: str, password: str) -> bool:
    users = load_users()
    hashed = hash_password(password)
    if username in users["username"].values:
        return users.loc[users["username"] == username, "password_hash"].iloc[0] == hashed
    return False


def save_performance(username: str, score: int, total: int) -> None:
    percentage = (score / total) * 100
    record = pd.DataFrame(
        [[username, datetime.now(), score, total, percentage]],
        columns=["username", "timestamp", "score", "total", "percentage"],
    )
    if os.path.exists(STATS_FILE):
        existing = pd.read_csv(STATS_FILE)
        combined = pd.concat([existing, record], ignore_index=True)
    else:
        combined = record
    combined.to_csv(STATS_FILE, index=False)


def load_performance(username: str) -> pd.DataFrame:
    if os.path.exists(STATS_FILE):
        df = pd.read_csv(STATS_FILE)
        if "percentage" not in df.columns:
            df["percentage"] = (df["score"] / df["total"]) * 100
        return df[df["username"] == username]
    return pd.DataFrame(columns=["username", "timestamp", "score", "total", "percentage"])


# ---------- SESSION STATE SETUP ----------
for key in [
    "quiz_questions",
    "user_answers",
    "quiz_started",
    "intro_shown",
    "logged_in_user",
    "n_questions",
    "selected_package",
]:
    if key not in st.session_state:
        if key in ["logged_in_user", "selected_package"]:
            st.session_state[key] = None
        elif key in ["quiz_started", "intro_shown"]:
            st.session_state[key] = False
        else:
            st.session_state[key] = {}

# ---------- AUTHENTICATION UI ----------
if not st.session_state.logged_in_user:
    st.title("🔐 Accesso Utente - Quiz Polizia di Stato")
    tab1, tab2 = st.tabs(["Accedi", "Registrati"])

    with tab1:
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Accedi"):
            if authenticate(login_user, login_pass):
                st.session_state.logged_in_user = login_user
                st.session_state.intro_shown = False
                st.rerun()
            else:
                st.warning("Credenziali errate.")

    with tab2:
        new_user = st.text_input("Nuovo Username", key="register_user")
        new_pass = st.text_input("Nuova Password", type="password", key="register_pass")
        if st.button("Registrati"):
            if save_user(new_user, new_pass):
                st.success("Registrazione completata! Ora puoi accedere.")
            else:
                st.warning("Username già esistente.")

    st.stop()

# ---------- LOAD DATA ----------
df = pd.read_excel("questions_extracted.xlsx")
df.columns = df.columns.str.strip()
df = df.rename(
    columns={
        "Question": "question",
        "Correct Answer": "correct",
        "Option A": "A",
        "Option B": "B",
        "Option C": "C",
        "Option D": "D",
        "Option E": "E",
    }
)

# ---------- INTRO PAGE ----------
if not st.session_state.intro_shown:
    st.title("🚔 Quiz Polizia di Stato")
    st.markdown(
        f"""
        <div style='font-size:17px; line-height:1.7; color:#222; background-color:#f0f8ff; padding:20px; border-radius:10px; border-left: 6px solid #1f77b4;'>
        👋 Benvenuto, <b>{st.session_state.logged_in_user}</b>!<br><br>

        Questo simulatore ti aiuterà a prepararti per il concorso di <b>Agente della Polizia di Stato</b>.<br>

        <ul style='color:#444;'>
        <li style='margin-bottom: 10px;'><b style='color:#1f77b4;'>📌</b> Ogni test propone un pacchetto di domande a scelta (25, 50, 75 o 100), selezionate <b>casualmente</b> ogni volta.</li>
        <li style='margin-bottom: 10px;'><b style='color:#2ca02c;'>✅</b> Le risposte vengono corrette subito con spiegazioni sulle scelte corrette e sbagliate.</li>
        <li style='margin-bottom: 10px;'><b style='color:#ff7f0e;'>📈</b> Dopo ogni test, visualizzi un grafico con l'<b>andamento delle tue performance</b> nel tempo.</li>
        <li style='margin-bottom: 10px;'><b style='color:#9467bd;'>🏆</b> Una <b>classifica</b> mostra la media dei punteggi e i grafici per ciascun utente.</li>
        <li style='margin-bottom: 10px;'><b style='color:#e377c2;'>🎮</b> L’esperienza è gamificata: più provi, più migliori, più sali!</li>
        </ul>

        Seleziona il numero di domande e clicca per iniziare ⬇️
        </div>
        """,
        unsafe_allow_html=True
    )
    st.session_state.selected_package = st.selectbox(
        "Scegli il pacchetto di domande:", [25, 50, 75, 100], index=0
    )
    if st.button("👉 Inizia la simulazione"):
        st.session_state.n_questions = st.session_state.selected_package
        st.session_state.intro_shown = True
        st.session_state.quiz_started = False
        st.rerun()
    st.stop()

# ---------- QUIZ LOGIC ----------
# Ensure a fresh random seed each time we rebuild the quiz so that
# every iteration uses a newly‑shuffled set of questions/answers.
random.seed()
if not st.session_state.quiz_started:
    required_columns = ["question", "correct", "A", "B", "C", "D", "E"]
    for col in required_columns:
        if col not in df.columns:
            st.error(f"⚠️ Colonna mancante: {col}")
            st.stop()

    quiz_df = df[required_columns].dropna()
    sample_size = min(st.session_state.n_questions or 25, len(quiz_df))
    sampled = quiz_df.sample(n=sample_size).reset_index(drop=True)

    randomized_questions = []
    for _, row in sampled.iterrows():
        options = [
            (label, row[label])
            for label in ["A", "B", "C", "D", "E"]
            if pd.notna(row[label])
        ]
        random.shuffle(options)
        correct_letter = row["correct"]
        correct_text = row[correct_letter]
        option_texts = [opt[1] for opt in options]
        randomized_questions.append(
            {
                "question": row["question"],
                "answer_choices": option_texts,
                "correct": correct_text,
            }
        )

    st.session_state.quiz_questions = randomized_questions
    st.session_state.quiz_started = True

st.title("📝 Quiz in corso")

for i, question in enumerate(st.session_state.quiz_questions):
    st.subheader(f"Domanda {i + 1}:")
    st.markdown(
        f"""
        <p style='font-size:17px; font-family:Helvetica, sans-serif; font-weight:bold; color:#f4f4f5;'>
    {question["question"]}
</p>
        """,
        unsafe_allow_html=True
    )

    options = question["answer_choices"]
    if options:
        selected = st.radio("", options, key=f"q{i}", format_func=lambda x: f"**{x}**")
        st.session_state.user_answers[i] = selected
    else:
        st.warning("⚠️ Nessuna opzione trovata per questa domanda.")

if st.button("📊 Invia e visualizza i risultati"):
    correct = 0
    st.subheader("📈 Risultati")
    for i, question in enumerate(st.session_state.quiz_questions):
        user_ans = st.session_state.user_answers.get(i)
        correct_ans = question["correct"]
        if user_ans == correct_ans:
            correct += 1
            st.success(f"Domanda {i + 1}: Corretta ✅")
        else:
            st.error(
                f"Domanda {i + 1}: Sbagliata ❌ (Risposta corretta: {correct_ans})"
            )

    score = correct
    total = len(st.session_state.quiz_questions)
    percentage = (score / total) * 100
    st.info(f"✔️ Punteggio totale: {score} su {total} ({percentage:.1f}%)")

    save_performance(st.session_state.logged_in_user, score, total)

    history = load_performance(st.session_state.logged_in_user)
    if not history.empty:
        history["percentage"] = (
            history["percentage"] if "percentage" in history.columns else (history["score"] / history["total"] * 100)
        )
        st.line_chart(history[["timestamp", "percentage"]].set_index("timestamp"))
        avg_score = history["percentage"].mean()
        st.success(f"📊 Media dei punteggi: {avg_score:.2f}%")
        st.info(f"🌟 Totale tentativi: {len(history)}")

        # ---------- LEADERBOARD ----------
        st.markdown("---")
        st.subheader("🏆 Classifica - Andamento e Media per Utente")
        full_data = pd.read_csv(STATS_FILE)
        if "percentage" not in full_data.columns:
            full_data["percentage"] = (full_data["score"] / full_data["total"]) * 100

        avg_by_user = full_data.groupby("username")["percentage"].mean().sort_values(ascending=False)
        st.write("**Media percentuale per utente:**")
        st.dataframe(avg_by_user.round(2).reset_index().rename(columns={"percentage": "% medio"}))

        st.write("**Andamento delle prestazioni nel tempo:**")
        chart_data = full_data.copy()
        chart_data["timestamp"] = pd.to_datetime(chart_data["timestamp"])
        chart_data = chart_data.sort_values("timestamp")
        import altair as alt
        chart = alt.Chart(chart_data).mark_line(point=True).encode(
            x="timestamp:T",
            y="percentage:Q",
            color="username:N",
            tooltip=["username", "percentage", "timestamp"]
        ).properties(
            width=700,
            height=400
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("---")
st.subheader("🔁 Vuoi riprovare con un nuovo numero di domande?")

retry_n = st.selectbox(
    "Seleziona il nuovo pacchetto:", [25, 50, 75, 100], index=0, key="retry_package"
)

if st.button("🔄 Rifai il quiz"):
    st.session_state.n_questions = retry_n
    st.session_state.quiz_started = False
    st.session_state.quiz_questions = []
    st.session_state.user_answers = {}
    st.rerun()
