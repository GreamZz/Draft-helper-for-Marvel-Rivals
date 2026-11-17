import json
import pandas as pd

try:
    with open("match_history.json", "r", encoding="utf-8") as f:
        matches_data = json.load(f)
except FileNotFoundError:
    print("Файл не найден")
    matches_data = None

matches_list = [matches_data] if isinstance(matches_data, dict) else matches_data

if matches_list:
    dataset_rows = []

    for match in matches_list:
        game_mode = match.get("game_mode_id")

        players = match.get("match_players", [])

        camp_1_won = None
        for p in players:
            if p.get("camp") == 1:
                camp_1_won = p.get("is_win")
                break

        if camp_1_won is None:
            continue

        match_entry = {
            "Game_Mode": f"Mode_{game_mode}",
            "Camp_1_Won": int(camp_1_won)
        }

        for p in players:
            camp = p.get("camp")
            hero_id = p.get("cur_hero_id")
            if camp and hero_id:
                match_entry[f"Camp{camp}_Hero_{hero_id}"] = 1

        dataset_rows.append(match_entry)

    if dataset_rows:
        df = pd.DataFrame(dataset_rows).fillna(0)

        df = pd.get_dummies(df, columns=["Game_Mode"], dtype=int)

        hero_cols = [c for c in df.columns if "Hero_" in c]
        df[hero_cols] = df[hero_cols].astype(int)

        cols = [c for c in df.columns if c != "Camp_1_Won"] + ["Camp_1_Won"]
        df = df[cols]

        csv_filename = "matches_dataset.csv"
        df.to_csv(csv_filename, index=False, encoding="utf-8")

        print(f"Всего матчей: {len(df)}")
        print(f"Количество признаков: {len(df.columns)}")
        print(list(df.columns[:10]))
