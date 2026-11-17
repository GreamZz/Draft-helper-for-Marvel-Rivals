import sqlite3
from collections import Counter

DB_NAME = "characters.db"


class DraftRecommender:

    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self.heroes = {}
        self.counters = {}
        self._load_data()

    def _load_data(self): # загрузка необходимых данных из БД
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # загрузка героев
        cursor.execute("SELECT * FROM hero")
        for row in cursor.fetchall():
            self.heroes[row["id"]] = dict(row)

        # 2. загрузка матрицы контр-пиков
        cursor.execute("SELECT hero_id, target_hero_id, score FROM counters")
        for row in cursor.fetchall():
            self.counters[(row["hero_id"], row["target_hero_id"])] = row["score"]

        conn.close()

    def recommend( # расчет score
        self, my_team_ids: list[int], enemy_team_ids: list[int], top_n: int = 5
    ):
        my_team = [self.heroes[hid] for hid in my_team_ids if hid in self.heroes]
        enemy_team = [
            self.heroes[hid] for hid in enemy_team_ids if hid in self.heroes
        ]
        role_counts = Counter([h["role"] for h in my_team])

        scores = []

        for hero_id, hero in self.heroes.items():
            if hero_id in my_team_ids:
                continue  # пропуск уже выбранных героев

            # по таблице контр-пика персонажей
            s_counter = 0
            for enemy in enemy_team:
                direct_key = (hero_id, enemy["id"])
                reverse_key = (enemy["id"], hero_id)

                if direct_key in self.counters:
                    s_counter += self.counters[direct_key]

                elif reverse_key in self.counters:
                    s_counter += -self.counters[reverse_key]

            # очки по тегам
            s_rules = 0
            # если есть летающие то плюс к хитскану
            has_flying_enemies = any(e.get("is_flying") == 1 for e in enemy_team)
            if has_flying_enemies and hero.get("attack_type") == "HITSCAN":
                s_rules += 2.5

            my_dive_count = sum(1 for h in my_team if h.get("is_dive") == 1)
            if my_dive_count >= 1 and hero.get("is_dive") == 1:
                s_rules += 1.5

            # синергии с командой
            s_synergy = 0

            if hero["role"] == "Vanguard" and role_counts["Strategist"] >= 1:
                s_synergy += 1.0

            # штрафы за дисбаланс ролей
            penalty_role = 0
            current_role_count = role_counts[hero["role"]]

            # базовый выбор 2-2-2
            if current_role_count >= 2:
                penalty_role += 10.0  # штраф за выбор 3 героя той же роли
            elif current_role_count == 0 and len(my_team) >= 3:
                s_synergy += 2.0

            total_score = s_counter + s_rules + s_synergy - penalty_role

            scores.append(
                {
                    "hero": hero,
                    "total_score": round(total_score, 1),
                    "breakdown": f"Counters: {s_counter} | Rules: {s_rules} | Syn: {s_synergy} | Pen: -{penalty_role}",
                }
            )

        scores.sort(key=lambda x: x["total_score"], reverse=True)

        print(
            f"Рекомендации (Союзников: {len(my_team)}, Врагов: {len(enemy_team)}):\n"
        )
        for rank, item in enumerate(scores[:top_n], 1):
            h = item["hero"]
            print(
                f"{rank}. {h['name']:<15} [{h['role']:<10}] -> Очков: {item['total_score']:>5.1f}"
            )
            print(f"{item['breakdown']}")


if __name__ == "__main__":
    recommender = DraftRecommender()

    enemies = [13, 20, 22]
    my_team = []

    recommender.recommend(my_team_ids=my_team, enemy_team_ids=enemies, top_n=5)