using System;
using System.Data;
using MySql.Data.MySqlClient;
using UnityEngine;

namespace Evolution.Core
{
    /// <summary>
    /// Lightweight MySQL client used by the Unity front end.
    /// Wraps connection handling so other classes can persist session data.
    /// </summary>
    public class DatabaseClient
    {
        private readonly string connectionString;

        public DatabaseClient(string host, string user, string password, string database)
        {
            connectionString = $"Server={host};User ID={user};Password={password};Database={database};Pooling=true";
        }

        private MySqlConnection CreateConnection()
        {
            var conn = new MySqlConnection(connectionString);
            conn.Open();
            return conn;
        }

        public void Execute(string query, Action<IDbCommand> paramHandler)
        {
            using var conn = CreateConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = query;
            paramHandler?.Invoke(cmd);
            cmd.ExecuteNonQuery();
        }

        public T QueryScalar<T>(string query, Action<IDbCommand> paramHandler)
        {
            using var conn = CreateConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = query;
            paramHandler?.Invoke(cmd);
            object result = cmd.ExecuteScalar();
            if (result == null || result == DBNull.Value) return default;
            return (T)Convert.ChangeType(result, typeof(T));
        }

        public IDataReader Query(string query, Action<IDbCommand> paramHandler)
        {
            var conn = CreateConnection();
            var cmd = conn.CreateCommand();
            cmd.CommandText = query;
            paramHandler?.Invoke(cmd);
            // caller must dispose reader and connection
            return cmd.ExecuteReader(CommandBehavior.CloseConnection);
        }
    }
}
