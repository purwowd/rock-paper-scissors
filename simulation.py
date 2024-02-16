import requests
import random


num_simulation = 10
player_choices = []

game_history = {
    "batu": {"batu": 0, "gunting": 0, "kertas": 0},
    "gunting": {"batu": 0, "gunting": 0, "kertas": 0},
    "kertas": {"batu": 0, "gunting": 0, "kertas": 0},
}


def start_simulation():
    base_url = "http://localhost:8000"
    computer_wins = 0
    player_wins = 0
    draws = 0

    global player_choices
    global game_history

    for i in range(num_simulation):
        if len(player_choices) > 0:
            player_choice = predict_player_choice(player_choices)
        else:
            player_choice = random.choice(["batu", "kertas", "gunting"])

        try:
            response = requests.post(
                f"{base_url}/start_game/", data={"player_choice": player_choice}
            )
            if response.status_code == 200:
                result = response.json().get("result", "")
                print(f"Game {i+1}: {result}")

                player_choices.append(player_choice)

                computer_choice = result.split()[-1].strip()

                if player_choice in [
                    "batu",
                    "gunting",
                    "kertas",
                ] and computer_choice in ["batu", "gunting", "kertas"]:
                    game_history[player_choice][computer_choice] += 1

                if "Komputer menang" in result:
                    computer_wins += 1
                elif "Pemain menang" in result:
                    player_wins += 1
                else:
                    draws += 1
            else:
                print(f"Game {i+1} gagal dengan status kode: {response.status_code}")
        except requests.RequestException as e:
            print(f"Permintaan gagal: {e}")

    total_games = num_simulation
    computer_win_percentage = (computer_wins / total_games) * 100
    player_win_percentage = (player_wins / total_games) * 100
    draw_percentage = (draws / total_games) * 100

    print("=" * 50)

    print(
        f"Kemungkinan komputer menang dalam {total_games} permainan: {computer_win_percentage:.1f}%"
    )
    print(
        f"Kemungkinan pemain menang dalam {total_games} permainan: {player_win_percentage:.1f}%"
    )
    print(f"Kemungkinan seri dalam {total_games} permainan: {draw_percentage:.1f}%")


def predict_player_choice(player_choices):
    if len(player_choices) >= 3:
        last_three_choices = player_choices[-3:]
        most_frequent_choice = max(
            set(last_three_choices), key=last_three_choices.count
        )
        counter_choice = {"batu": "gunting", "gunting": "kertas", "kertas": "batu"}

        if len(set(last_three_choices)) == 1:
            return counter_choice[most_frequent_choice]

        else:
            player_freq = sum(
                game_history[choice][most_frequent_choice]
                for choice in last_three_choices
            )
            computer_freq = sum(game_history[most_frequent_choice].values())
            threshold = 0.6
            if computer_freq != 0 and player_freq / computer_freq > threshold:
                return counter_choice[most_frequent_choice]
            else:
                return random.choice(["batu", "kertas", "gunting"])

    else:
        return random.choice(["batu", "kertas", "gunting"])


if __name__ == "__main__":
    start_simulation()
