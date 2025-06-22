using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Evolution.Combat
{
    [Serializable]
    public class StatusEffect
    {
        public string EffectName;
        public int Remaining;
        public int DamagePerTurn;
        public int HealPerTurn;
        public float SpeedUp;
        public float SpeedDown;
    }

    [Serializable]
    public class Ability
    {
        public string Name;
        public int Damage;
        public int Heal;
        public StatusEffect Effect;
        public float Cooldown;
        public bool TargetSelf;
    }

    [Serializable]
    public class Combatant
    {
        public int Id;
        public int Hp;
        public int MaxHp;
        public float Speed;
        public float ATB;
        public float ATBMax = 5f;
        public Dictionary<string, float> Cooldowns = new();
        public List<StatusEffect> Effects = new();

        public float GetSpeedBonus()
        {
            float bonus = 0f;
            foreach (var se in Effects)
                bonus += se.SpeedUp - se.SpeedDown;
            return bonus;
        }

        public void TickStatus()
        {
            List<StatusEffect> next = new();
            foreach (var se in Effects)
            {
                if (se.DamagePerTurn > 0)
                    Hp = Mathf.Max(Hp - se.DamagePerTurn, 0);
                if (se.HealPerTurn > 0)
                    Hp = Mathf.Min(Hp + se.HealPerTurn, MaxHp);
                se.Remaining--;
                if (se.Remaining > 0)
                    next.Add(se);
            }
            Effects = next;
        }
    }

    [Serializable]
    public class BattleState
    {
        public Dictionary<int, Combatant> Players = new();
        public Combatant Enemy = new();
        public bool Paused;
        public bool InBattle;

        public Dictionary<int, float> PlayerSpeeds
        {
            get
            {
                var d = new Dictionary<int, float>();
                foreach (var kv in Players)
                    d[kv.Key] = kv.Value.Speed;
                return d;
            }
        }
        public Dictionary<int, float> PlayerATB
        {
            get
            {
                var d = new Dictionary<int, float>();
                foreach (var kv in Players)
                    d[kv.Key] = kv.Value.ATB;
                return d;
            }
            set
            {
                foreach (var kv in value)
                    if (Players.ContainsKey(kv.Key))
                        Players[kv.Key].ATB = kv.Value;
            }
        }
        public Dictionary<int, float> PlayerMaxATB
        {
            get
            {
                var d = new Dictionary<int, float>();
                foreach (var kv in Players)
                    d[kv.Key] = kv.Value.ATBMax;
                return d;
            }
        }
        public float EnemyATB { get { return Enemy.ATB; } set { Enemy.ATB = value; } }
        public float EnemyMaxATB { get { return Enemy.ATBMax; } set { Enemy.ATBMax = value; } }
        public float EnemySpeed { get { return Enemy.Speed; } set { Enemy.Speed = value; } }

        public float GetSpeedBonus(int playerId)
        {
            if (!Players.ContainsKey(playerId)) return 0f;
            return Players[playerId].GetSpeedBonus();
        }
        public float GetEnemySpeedBonus() => Enemy.GetSpeedBonus();
    }

    public class BattleManager : MonoBehaviour
    {
        public ATBManager AtbManager;
        public BattleState State = new();

        public event Action OnUIUpdate;

        private void Awake()
        {
            if (AtbManager == null)
                AtbManager = GetComponent<ATBManager>();
            if (AtbManager != null)
            {
                AtbManager.OnPlayerReady += HandlePlayerReady;
                AtbManager.OnEnemyReady += HandleEnemyReady;
                AtbManager.OnTick += () => OnUIUpdate?.Invoke();
            }
        }

        public void StartBattle(Combatant enemy, IEnumerable<Combatant> players)
        {
            State = new BattleState { InBattle = true, Enemy = enemy };
            foreach (var p in players)
                State.Players[p.Id] = p;
            if (AtbManager != null)
                AtbManager.StartATB(this, State);
        }

        public void EndBattle()
        {
            State.InBattle = false;
            if (AtbManager != null)
                AtbManager.StopATB();
        }

        private void HandlePlayerReady(int id)
        {
            StartCoroutine(PlayerTurn(id));
        }

        private void HandleEnemyReady()
        {
            StartCoroutine(EnemyTurn());
        }

        private IEnumerator PlayerTurn(int playerId)
        {
            State.Paused = true;
            var player = State.Players[playerId];
            player.TickStatus();
            OnUIUpdate?.Invoke();
            // waiting for external input in real game
            yield return null;
        }

        private IEnumerator EnemyTurn()
        {
            State.Paused = true;
            State.Enemy.TickStatus();
            ApplyEnemyAI();
            OnUIUpdate?.Invoke();
            yield return new WaitForSeconds(1f);
            State.Enemy.ATB = 0f;
            State.Paused = false;
        }

        private void ApplyEnemyAI()
        {
            var ability = ChooseEnemyAbility();
            if (ability == null)
                return;
            ApplyAbility(State.Enemy, State.Players[State.Players.Keys.First()], ability); // simple: target first player
        }

        private Ability ChooseEnemyAbility()
        {
            // stub random ability; extend as needed
            return null;
        }

        public void ApplyAbility(Combatant user, Combatant target, Ability ability)
        {
            if (ability == null) return;
            if (ability.Damage > 0)
            {
                target.Hp = Mathf.Max(target.Hp - ability.Damage, 0);
            }
            if (ability.Heal > 0)
            {
                if (ability.TargetSelf)
                    user.Hp = Mathf.Min(user.Hp + ability.Heal, user.MaxHp);
                else
                    target.Hp = Mathf.Min(target.Hp + ability.Heal, target.MaxHp);
            }
            if (ability.Effect != null && ability.Effect.Remaining > 0)
            {
                var effTarget = ability.TargetSelf ? user : target;
                effTarget.Effects.Add(ability.Effect);
            }
            if (OnUIUpdate != null)
                OnUIUpdate.Invoke();
        }
    }
}
