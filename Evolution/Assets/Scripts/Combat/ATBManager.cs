using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Evolution.Combat
{
    public class ATBManager : MonoBehaviour
    {
        [SerializeField] private float tickSeconds = 0.5f;
        [SerializeField] private float updateInterval = 1f;

        private Coroutine tickRoutine;
        private BattleManager battle;
        private BattleState state;

        public event Action OnTick;
        public event Action<int> OnPlayerReady;
        public event Action OnEnemyReady;

        public void StartATB(BattleManager manager, BattleState battleState)
        {
            StopATB();
            battle = manager;
            state = battleState;
            tickRoutine = StartCoroutine(TickLoop());
        }

        public void StopATB()
        {
            if (tickRoutine != null)
            {
                StopCoroutine(tickRoutine);
                tickRoutine = null;
            }
        }

        private IEnumerator TickLoop()
        {
            float lastUpdate = Time.time;
            var notifiedPlayers = new Dictionary<int, bool>();
            var lastInts = new Dictionary<int, int>();
            int lastEnemy = 0;
            foreach (var kvp in state.PlayerSpeeds)
            {
                notifiedPlayers[kvp.Key] = false;
                lastInts[kvp.Key] = 0;
            }
            bool enemyNotified = false;

            while (state.InBattle)
            {
                yield return new WaitForSeconds(tickSeconds);
                if (state.Paused)
                    continue;

                float delta = tickSeconds;
                foreach (var kvp in state.PlayerSpeeds)
                {
                    int id = kvp.Key;
                    float maxVal = state.PlayerMaxATB[id];
                    if (state.PlayerATB[id] < maxVal)
                    {
                        float effective = kvp.Value + state.GetSpeedBonus(id);
                        state.PlayerATB[id] += effective * delta;
                        if (state.PlayerATB[id] >= maxVal)
                            state.PlayerATB[id] = maxVal;
                    }

                    if (state.PlayerATB[id] >= maxVal)
                    {
                        if (!notifiedPlayers[id])
                        {
                            notifiedPlayers[id] = true;
                            OnPlayerReady?.Invoke(id);
                        }
                    }
                    else
                    {
                        notifiedPlayers[id] = false;
                    }
                }

                if (state.EnemyATB < state.EnemyMaxATB)
                {
                    float eff = state.EnemySpeed + state.GetEnemySpeedBonus();
                    state.EnemyATB += eff * delta;
                    if (state.EnemyATB >= state.EnemyMaxATB)
                        state.EnemyATB = state.EnemyMaxATB;
                }

                if (state.EnemyATB >= state.EnemyMaxATB)
                {
                    if (!enemyNotified)
                    {
                        enemyNotified = true;
                        OnEnemyReady?.Invoke();
                    }
                }
                else
                {
                    enemyNotified = false;
                }

                bool trigger = false;
                foreach (var id in state.PlayerSpeeds.Keys)
                {
                    int cur = (int)state.PlayerATB[id];
                    if (cur != lastInts[id])
                    {
                        lastInts[id] = cur;
                        trigger = true;
                    }
                }
                int eCur = (int)state.EnemyATB;
                if (eCur != lastEnemy)
                {
                    lastEnemy = eCur;
                    trigger = true;
                }

                if (trigger || Time.time - lastUpdate >= updateInterval)
                {
                    OnTick?.Invoke();
                    lastUpdate = Time.time;
                }
            }
            tickRoutine = null;
        }
    }
}
