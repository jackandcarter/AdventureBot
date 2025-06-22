using System.Collections.Generic;
using UnityEngine;

namespace Evolution.Core
{
    /// <summary>
    /// Tracks active game sessions and provides basic persistence through
    /// <see cref="DatabaseClient"/>. This mirrors the Python SessionManager
    /// used by the Discord bot but is tailored for a local Unity game.
    /// </summary>
    public class SessionManager : MonoBehaviour
    {
        private readonly Dictionary<int, SessionData> sessions = new();
        private DatabaseClient db;

        public void Initialise(DatabaseClient client)
        {
            db = client;
        }

        public SessionData GetSession(int id)
        {
            sessions.TryGetValue(id, out var sess);
            return sess;
        }

        public void RegisterSession(SessionData data)
        {
            if (data == null) return;
            sessions[data.SessionId] = data;
        }

        public void SaveSession(SessionData data)
        {
            if (db == null || data == null) return;
            sessions[data.SessionId] = data;
            string json = JsonUtility.ToJson(data);
            db.Execute(
                "UPDATE sessions SET game_state=@state WHERE session_id=@id",
                cmd =>
                {
                    var pState = cmd.CreateParameter();
                    pState.ParameterName = "@state";
                    pState.Value = json;
                    cmd.Parameters.Add(pState);

                    var pId = cmd.CreateParameter();
                    pId.ParameterName = "@id";
                    pId.Value = data.SessionId;
                    cmd.Parameters.Add(pId);
                });
        }

        public SessionData LoadSession(int sessionId)
        {
            if (db == null) return null;
            string json = db.QueryScalar<string>(
                "SELECT game_state FROM sessions WHERE session_id=@id",
                cmd =>
                {
                    var p = cmd.CreateParameter();
                    p.ParameterName = "@id";
                    p.Value = sessionId;
                    cmd.Parameters.Add(p);
                });
            if (string.IsNullOrEmpty(json)) return null;
            var data = JsonUtility.FromJson<SessionData>(json);
            sessions[sessionId] = data;
            return data;
        }
    }

    [System.Serializable]
    public class SessionData
    {
        public int SessionId;
        public int OwnerId;
        public string Difficulty;
        public int CurrentFloor;
        public Vector2Int CurrentPosition;
        public Dungeon.DungeonData Dungeon;
        public List<int> Players = new();
    }
}
