"""帮派日常与周常任务系统"""
import random
from dataclasses import dataclass, field

# 任务池：每日/每周从此随机抽取，保证类型多样
QUEST_POOL = [
    ("kill", "击杀怪物", "daily", 10, 1),
    ("collect", "采集资源", "daily", 20, 1),
    ("donate", "捐献物资", "daily", 5, 2),
    ("dungeon", "通关副本", "daily", 3, 3),
    ("escort", "护送商队", "daily", 2, 3),
    ("patrol", "帮派巡逻", "daily", 8, 1),
    ("boss", "讨伐首领", "weekly", 1, 5),
    ("war", "帮派战", "weekly", 3, 4),
]

BASE_REWARD = {"gold": 100, "exp": 50}


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
    difficulty: int = 1
    abandoned: bool = False
    abandon_count: int = 0


class GuildQuest:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.quests: dict[str, Quest] = {}
        self.weekly_progress: int = 0  # 累计完成的日常数量
        self.abandon_counts: dict[str, int] = {}  # 放弃次数，影响评分
        self.contributions: dict[str, int] = {}  # 个人贡献独立记录
        self.mailbox: list[dict] = []  # 自动发放的奖励

    def refresh_quests(self):
        # fix1: 只重置已完成和未开始的，保留进行中任务的进度
        for q in self.quests.values():
            if q.completed or q.progress == 0:
                if not q.abandoned:
                    q.progress = 0
                    q.completed = False
                    q.claimed = False

    def get_daily_quests(self) -> list:
        # fix2: 从任务池随机抽取，保证至少一个高难度保底
        pool = [p for p in QUEST_POOL if p[2] == "daily"]
        picked = self.rng.sample(pool, 3)
        if not any(p[4] >= 3 for p in picked):
            hard = [p for p in pool if p[4] >= 3]
            picked[0] = self.rng.choice(hard)
        return [
            Quest(f"d{i}", name, qtype, target=target, difficulty=diff,
                  reward=dict(BASE_REWARD))
            for i, (_, name, qtype, target, diff) in enumerate(picked)
        ]

    def update_progress(self, qid: str, amount: int):
        # fix3: 实时保存进度，断线重连可恢复
        q = self.quests.get(qid)
        if q is None or q.completed:
            return
        q.progress = min(q.target, q.progress + amount)
        if q.progress >= q.target:
            q.completed = True
            self.weekly_progress += 1
            self.auto_claim(qid)

    def get_reward(self, quest: Quest, guild_level: int) -> dict:
        # fix4: 按帮派等级和任务难度分级
        mult = guild_level * max(1, quest.difficulty)
        return {k: v * mult for k, v in (quest.reward or BASE_REWARD).items()}

    def get_weekly_bonus(self) -> dict:
        # fix5: 按完成日常数量累计，多劳多得
        n = self.weekly_progress
        if n <= 0:
            return {}
        return {"gold": 50 * n, "exp": 20 * n, "guild_fund": 10 * n}

    def abandon_quest(self, qid: str) -> bool:
        # fix6: 放弃后当天可重接，但记录放弃次数影响评分
        q = self.quests.get(qid)
        if q is None:
            return False
        q.abandoned = True
        q.progress = 0
        q.completed = False
        self.abandon_counts[qid] = self.abandon_counts.get(qid, 0) + 1
        q.abandon_count = self.abandon_counts[qid]
        return True

    def accept_quest(self, qid: str) -> bool:
        q = self.quests.get(qid)
        if q is None or not q.abandoned:
            return False
        q.abandoned = False
        return True

    def auto_claim(self, qid: str) -> bool:
        # fix7: 完成后自动发放奖励到邮箱
        q = self.quests.get(qid)
        if q is None or not q.completed or q.claimed:
            return False
        q.claimed = True
        self.mailbox.append({"qid": qid, "reward": dict(q.reward or BASE_REWARD)})
        return True

    def add_personal_contribution(self, pid: str, amount: int):
        # fix8: 个人贡献独立记录
        self.contributions[pid] = self.contributions.get(pid, 0) + amount

    def get_personal_contribution(self, pid: str) -> int:
        return self.contributions.get(pid, 0)
