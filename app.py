import numpy as np
import random
import tensorflow as tf
import logging
import json
from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
dataset_path = "game_data.json"
choices = ["batu", "gunting", "kertas"]

logging.basicConfig(
    filename="game_results.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

encoder = tf.keras.preprocessing.text.Tokenizer()
encoder.fit_on_texts(choices)


def ensure_dataset_exists():
    try:
        with open(dataset_path, "r") as f:
            data = json.load(f)
            if not data:
                create_new_dataset()
    except FileNotFoundError:
        logging.info("Dataset not found, creating a new one.")
        create_new_dataset()


def create_new_dataset():
    data = {"player_choice": [], "computer_choice": [], "result": []}
    with open(dataset_path, "w") as f:
        json.dump(data, f)


def load_data():
    with open(dataset_path, "r") as f:
        data = json.load(f)
        player_choices = data["player_choice"]
        computer_choices = data["computer_choice"]

        X = np.array(encoder.texts_to_sequences(player_choices)).reshape(-1, 1)
        y = np.array(encoder.texts_to_sequences(computer_choices)) - 1
        y = np.clip(y, 0, len(choices) - 1)

        return X, y


def build_model():
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Embedding(
                input_dim=len(encoder.word_index) + 1, output_dim=32
            ),
            tf.keras.layers.GlobalAveragePooling1D(),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dense(3, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
    )
    return model


def start_game_with_machine_learning(player_choice):
    ensure_dataset_exists()
    X, y = load_data()
    if len(X) == 0:
        logging.info("No data available for training.")
        return random.choice(choices)
    model = build_model()
    model.fit(X, y, epochs=50, batch_size=32, verbose=0)
    player_choice_encoded = np.array(
        encoder.texts_to_sequences([player_choice])
    ).reshape(-1, 1)
    computer_choice_encoded = np.argmax(model.predict(player_choice_encoded))
    computer_choice = list(encoder.word_index.keys())[computer_choice_encoded]
    return computer_choice


def determine_winner(player, computer):
    if player == computer:
        return "Seri!"
    elif (
        (player == "batu" and computer == "gunting")
        or (player == "gunting" and computer == "kertas")
        or (player == "kertas" and computer == "batu")
    ):
        return "Pemain menang!"
    elif (
        (computer == "batu" and player == "gunting")
        or (computer == "gunting" and player == "kertas")
        or (computer == "kertas" and player == "batu")
    ):
        return "Komputer menang!"


@app.get("/")
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/start_game/")
async def start_game(player_choice: str = Form(...)):
    computer_choice = start_game_with_machine_learning(player_choice)
    result = determine_winner(player_choice, computer_choice)
    save_to_json(player_choice, computer_choice, result)
    logging.info(f"Player: {player_choice}, Computer: {computer_choice}")
    return JSONResponse(
        content={
            "result": f"Pemain memilih {player_choice}, Komputer memilih {computer_choice}. Hasilnya: {result}"
        }
    )


def save_to_json(player_choice, computer_choice, result):
    data = {"player_choice": [], "computer_choice": [], "result": []}
    with open(dataset_path, "r") as f:
        data = json.load(f)

    data["player_choice"].append(player_choice)
    data["computer_choice"].append(computer_choice)
    data["result"].append(result)

    with open(dataset_path, "w") as f:
        json.dump(data, f)
