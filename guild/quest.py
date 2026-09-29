"""帮派日常与周常任务系统"""
import random
from dataclasses import dataclass, field

# 任务池：每日/每周从此随机抽取，保证类型保底
QUEST_POOL = [
    {"qid": "kill", "name": "kill10", "category": "combat", "target": 10, "difficulty": 1},
    {"qid": "boss", "name": "boss1", "category": "combat", "target": 1, "difficulty": 3},
    {"qid": "gather", "name": "gather20", "category": "collect", "target": 20, "difficulty": 1},
    {"qid": "escort", "name": "escort3", "category": "collect", "target": 3, "difficulty": 2},
    {"qid": "donate", "name": "donate5", "category": "social", "target": 5, "difficulty": 1},
    {"qid": "visit", "name": "visit3", "category": "social", "target": 3, "difficulty": 1},
]

BASE_REWARD = {"gold": 100, "exp": 50}
DAILY_COUNT = 3


@dataclass
class Quest:
    qid: str
    name: str
    type: str  # daily/weekly
    progress: int = 0
    target: int = 10
    completed: bool = False
    claimed: bool = False
    reward: dict = field(default_factory=dict)
    category: str = ""
    difficulty: int = 1
    abandoned: bool = False
    abandon_count: int = 0


class GuildQuest:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.quests: dict[str, Quest] = {}
        self.weekly_progress: int = 0
        self.contributions: dict[str, int] = {}  # 个人贡献独立记录
        self.mailbox: list = []  # 奖励自动发放到邮箱
        self._saved_progress: dict[str, int] = {}  # 模拟服务器端实时存档

    def refresh_quests(self):
        # 保留进行中任务的进度，只重置已完成和已放弃的
        for q in self.quests.values():
            if q.completed or q.abandoned:
                q.progress = 0
                q.completed = False
                q.claimed = False
                q.abandoned = False

    def get_daily_quests(self) -> list:
        # 从任务池随机抽取，且每个类别至少保底一个
        pool = [dict(p) for p in QUEST_POOL]
        picked = []
        categories = {p["category"] for p in pool}
        for cat in categories:
            candidates = [p for p in pool if p["category"] == cat and p not in picked]
            if candidates:
                picked.append(self.rng.choice(candidates))
        remaining = [p for p in pool if p not in picked]
        self.rng.shuffle(remaining)
        picked.extend(remaining[: max(0, DAILY_COUNT - len(picked))])
        return [
            Quest(p["qid"], p["name"], "daily", target=p["target"],
                  category=p["category"], difficulty=p["difficulty"],
                  reward=dict(BASE_REWARD))
            for p in picked
        ]

    def update_progress(self, qid: str, amount: int):
        # 进度实时保存，断线重连可恢复
        q = self.quests.get(qid)
        if q is None or q.completed:
            return
        q.progress = min(q.target, q.progress + amount)
        self._saved_progress[qid] = q.progress  # 实时存档到服务器
        if q.progress >= q.target:
            q.completed = True
            self.weekly_progress += 1
            self.auto_claim(qid)

    def restore_progress(self, qid: str) -> int:
        # 断线重连后从服务器存档恢复进度
        saved = self._saved_progress.get(qid, 0)
        if qid in self.quests:
            self.quests[qid].progress = saved
        return saved

    def get_reward(self, quest: Quest, guild_level: int) -> dict:
        # 奖励按帮派等级和任务难度分级
        multiplier = guild_level * quest.difficulty
        return {k: v * multiplier for k, v in quest.reward.items()}

    def get_weekly_bonus(self) -> dict:
        # 周常按完成日常数量累计，多劳多得
        if self.weekly_progress <= 0:
            return {}
        return {
            "gold": 50 * self.weekly_progress,
            "exp": 20 * self.weekly_progress,
        }

    def abandon_quest(self, qid: str) -> bool:
        # 放弃不删除，当天可重新接取；放弃次数影响评分
        q = self.quests.get(qid)
        if q is None:
            return False
        q.abandoned = True
        q.abandon_count += 1
        return True

    def accept_quest(self, qid: str) -> bool:
        # 接取/重新接取任务，放弃次数越多评分越低
        q = self.quests.get(qid)
        if q is None:
            return False
        q.abandoned = False
        q.progress = 0
        q.completed = False
        q.claimed = False
        return True

    def get_score(self, qid: str) -> float:
        q = self.quests.get(qid)
        if q is None:
            return 0.0
        return max(0.0, 1.0 - 0.1 * q.abandon_count)

    def auto_claim(self, qid: str) -> bool:
        # 完成后自动发放奖励到邮箱
        q = self.quests.get(qid)
        if q is None or not q.completed or q.claimed:
            return False
        q.claimed = True
        self.mailbox.append({"qid": qid, "reward": dict(q.reward)})
        return True

    def add_personal_contribution(self, pid: str, amount: int):
        # 个人贡献独立记录
        self.contributions[pid] = self.contributions.get(pid, 0) + amount

    def get_personal_contribution(self, pid: str) -> int:
        return self.contributions.get(pid, 0)
