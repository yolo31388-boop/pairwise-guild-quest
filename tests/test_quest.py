"""帮派日常与周常任务系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from guild.quest import GuildQuest, Quest

class TestRefreshPreservesProgress:
    def test_refresh_keeps_in_progress_quests(self):
        gq = GuildQuest()
        gq.quests["q1"] = Quest("q1", "kill", "daily", progress=5, target=10)
        gq.refresh_quests()
        assert gq.quests["q1"].progress == 5  # bug1: 被清零

class TestDailyVariety:
    def test_daily_quests_vary(self):
        gq = GuildQuest(seed=42)
        q1 = gq.get_daily_quests()
        q2 = GuildQuest(seed=99).get_daily_quests()
        assert q1 != q2  # bug2: 一样

class TestProgressPersistence:
    def test_progress_is_saved(self):
        gq = GuildQuest()
        gq.quests["q1"] = Quest("q1", "kill", "daily", target=10)
        gq.update_progress("q1", 3)
        assert gq.quests["q1"].progress == 3  # bug3: 还是0

class TestRewardByLevel:
    def test_higher_guild_level_better_reward(self):
        gq = GuildQuest()
        q = Quest("q1", "kill", "daily", reward={"gold": 100})
        r1 = gq.get_reward(q, 1)
        r10 = gq.get_reward(q, 10)
        assert r10["gold"] > r1["gold"]  # bug4: 一样

class TestWeeklyBonus:
    def test_more_dailies_give_better_weekly_bonus(self):
        gq = GuildQuest()
        gq.weekly_progress = 1
        b1 = gq.get_weekly_bonus()
        gq.weekly_progress = 7
        b7 = gq.get_weekly_bonus()
        assert b7 != b1  # bug5: 都是空

class TestAbandonReaccept:
    def test_abandoned_quest_can_be_reaccepted(self):
        gq = GuildQuest()
        gq.quests["q1"] = Quest("q1", "kill", "daily")
        gq.abandon_quest("q1")
        # 应该能重新接取
        assert hasattr(gq, "accept_quest")
        assert gq.accept_quest("q1") == True  # bug6: 删了就没了

class TestAutoClaim:
    def test_completed_quest_auto_claimed(self):
        gq = GuildQuest()
        gq.quests["q1"] = Quest("q1", "kill", "daily", progress=10, target=10, completed=True)
        result = gq.auto_claim("q1")
        assert result == True  # bug7: False
        assert gq.quests["q1"].claimed == True

class TestPersonalContribution:
    def test_personal_contribution_tracked(self):
        gq = GuildQuest()
        # 应该有方法记录个人贡献
        assert hasattr(gq, "add_personal_contribution")
        gq.add_personal_contribution("p1", 50)
        assert gq.get_personal_contribution("p1") == 50  # bug8: 0
