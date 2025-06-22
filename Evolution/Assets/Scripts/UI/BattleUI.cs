using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using Evolution.Combat;

namespace Evolution.UI
{
    /// <summary>
    /// Displays ATB gauges for players and enemies during battle.
    /// </summary>
    public class BattleUI : MonoBehaviour
    {
        [SerializeField] private BattleManager battleManager;
        [SerializeField] private Slider enemyGauge;
        [SerializeField] private Slider playerGaugePrefab;
        [SerializeField] private Transform playerGaugeRoot;

        private readonly Dictionary<int, Slider> playerGauges = new();

        private void OnEnable()
        {
            if (battleManager != null)
                battleManager.OnUIUpdate += Refresh;
        }

        private void OnDisable()
        {
            if (battleManager != null)
                battleManager.OnUIUpdate -= Refresh;
        }

        public void SetBattleManager(BattleManager manager)
        {
            if (battleManager != null)
                battleManager.OnUIUpdate -= Refresh;
            battleManager = manager;
            if (battleManager != null)
                battleManager.OnUIUpdate += Refresh;
            Refresh();
        }

        private void Refresh()
        {
            if (battleManager == null || !battleManager.State.InBattle)
                return;

            var state = battleManager.State;
            if (enemyGauge != null)
            {
                enemyGauge.maxValue = state.EnemyMaxATB;
                enemyGauge.value = state.EnemyATB;
            }

            foreach (var kv in state.Players)
            {
                if (!playerGauges.TryGetValue(kv.Key, out Slider s))
                {
                    if (playerGaugePrefab != null && playerGaugeRoot != null)
                    {
                        s = Instantiate(playerGaugePrefab, playerGaugeRoot);
                        playerGauges[kv.Key] = s;
                    }
                }
                if (s != null)
                {
                    s.maxValue = kv.Value.ATBMax;
                    s.value = kv.Value.ATB;
                }
            }
        }
    }
}

