using System;
using System.Collections.Generic;
using UnityEngine;
using Evolution.Dungeon;
using Evolution.Combat;

namespace Evolution.Core
{
    /// <summary>
    /// Top level orchestrator for dungeon exploration. Inspired by the
    /// Python GameMaster class, this version drives gameplay inside Unity
    /// and communicates with the backend through <see cref="DatabaseClient"/>.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        [SerializeField] private DungeonGenerator generator;
        [SerializeField] private BattleManager battleManager;
        [SerializeField] private SessionManager sessionManager;
        [SerializeField] private string difficulty = "Easy";

        public event Action<RoomData> OnRoomEntered;
        public event Action<DungeonData> OnDungeonLoaded;

        private SessionData currentSession;

        public void StartNewGame(int ownerId)
        {
            if (sessionManager == null || generator == null)
            {
                Debug.LogError("GameManager missing dependencies");
                return;
            }
            currentSession = new SessionData
            {
                SessionId = ownerId, // temporary id if no DB yet
                OwnerId = ownerId,
                Difficulty = difficulty,
                CurrentFloor = 1,
                CurrentPosition = Vector2Int.zero,
                Dungeon = generator.GenerateDungeon()
            };
            sessionManager.RegisterSession(currentSession);
            OnDungeonLoaded?.Invoke(currentSession.Dungeon);
            EnterRoom(currentSession.CurrentPosition);
        }

        public void LoadSession(int sessionId)
        {
            if (sessionManager == null) return;
            currentSession = sessionManager.LoadSession(sessionId);
            if (currentSession != null)
            {
                OnDungeonLoaded?.Invoke(currentSession.Dungeon);
                EnterRoom(currentSession.CurrentPosition);
            }
            else
            {
                Debug.LogWarning($"Session {sessionId} not found");
            }
        }

        public void Move(Vector2Int delta)
        {
            if (currentSession == null) return;
            Vector2Int next = currentSession.CurrentPosition + delta;
            var floor = currentSession.Dungeon.Floors[currentSession.CurrentFloor - 1];
            foreach (var room in floor.Rooms)
            {
                if (room.Coord == next)
                {
                    currentSession.CurrentPosition = next;
                    EnterRoom(next);
                    sessionManager.SaveSession(currentSession);
                    return;
                }
            }
            Debug.Log("Cannot move in that direction");
        }

        private void EnterRoom(Vector2Int coord)
        {
            var floor = currentSession.Dungeon.Floors[currentSession.CurrentFloor - 1];
            RoomData room = floor.Rooms.Find(r => r.Coord == coord);
            if (room == null) return;
            HandleRoom(room);
            OnRoomEntered?.Invoke(room);
        }

        private void HandleRoom(RoomData room)
        {
            switch (room.Type)
            {
                case RoomType.Monster:
                case RoomType.Boss:
                    if (battleManager != null)
                    {
                        var enemy = new Combatant { Id = 0, Hp = 10, MaxHp = 10, Speed = 1f };
                        var player = new Combatant { Id = currentSession.OwnerId, Hp = 10, MaxHp = 10, Speed = 1f };
                        battleManager.StartBattle(enemy, new List<Combatant> { player });
                    }
                    break;
                case RoomType.Locked:
                    Debug.Log("Encountered a locked door.");
                    break;
                case RoomType.Treasure:
                    Debug.Log("Found a treasure chest!");
                    break;
                case RoomType.StaircaseDown:
                    currentSession.CurrentFloor++;
                    currentSession.CurrentPosition = Vector2Int.zero;
                    OnDungeonLoaded?.Invoke(currentSession.Dungeon);
                    break;
                case RoomType.StaircaseUp:
                    currentSession.CurrentFloor = Math.Max(1, currentSession.CurrentFloor - 1);
                    currentSession.CurrentPosition = Vector2Int.zero;
                    OnDungeonLoaded?.Invoke(currentSession.Dungeon);
                    break;
            }
        }
    }
}
