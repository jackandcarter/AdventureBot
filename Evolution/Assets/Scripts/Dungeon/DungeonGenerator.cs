using System.Collections.Generic;
using UnityEngine;

namespace Evolution.Dungeon
{
    public enum RoomType
    {
        Safe,
        Monster,
        Locked,
        Shop,
        Treasure,
        Boss,
        StaircaseUp,
        StaircaseDown,
        Exit
    }

    [System.Serializable]
    public class RoomData
    {
        public Vector2Int Coord;
        public RoomType Type;
        public List<Vector2Int> Connections = new List<Vector2Int>();
    }

    [System.Serializable]
    public class FloorData
    {
        public int FloorNumber;
        public List<RoomData> Rooms = new List<RoomData>();
    }

    [System.Serializable]
    public class DungeonData
    {
        public List<FloorData> Floors = new List<FloorData>();
    }

    public class DungeonGenerator : MonoBehaviour
    {
        [SerializeField] private int width = 8;
        [SerializeField] private int height = 8;
        [SerializeField] private int floors = 1;
        [SerializeField] private int minRooms = 8;
        [SerializeField, Range(0f, 1f)] private float loopChance = 0.15f;
        [SerializeField, Range(0f, 1f)] private float straightBias = 0.6f;
        [SerializeField] private int lockedRoomsPerFloor = 1;
        [SerializeField] private int shopsPerFloor = 1;
        [SerializeField, Range(0f, 1f)] private float treasureChance = 0.2f;
        [SerializeField] private int minLockDistance = 5;
        [SerializeField] private int minStairDistance = 6;

        public DungeonData GenerateDungeon()
        {
            var data = new DungeonData();
            Vector2Int entry = Vector2Int.zero;
            for (int floor = 1; floor <= floors; floor++)
            {
                bool isLast = floor == floors;
                Vector2Int exit = ChooseFarCoordinate(width, height, minStairDistance, 0.7f);
                var floorData = GenerateFloor(floor, entry, exit, isLast);
                data.Floors.Add(floorData);
                entry = exit;
            }
            return data;
        }

        private FloorData GenerateFloor(int floorNumber, Vector2Int entry, Vector2Int exit, bool isLast)
        {
            var floor = new FloorData { FloorNumber = floorNumber };
            int attempts = 0;
            Dictionary<Vector2Int, HashSet<Vector2Int>> adj = null;
            List<Vector2Int> path = null;
            Vector2Int finalExit = exit;
            while (attempts < 50)
            {
                adj = CarvePerfectMaze(width, height, straightBias);
                AddRandomLoops(adj, loopChance);
                path = BFSPath(adj, entry, finalExit);
                if (path.Count >= minRooms)
                    break;
                finalExit = ChooseFarCoordinate(width, height, minStairDistance, 0.7f);
                attempts++;
            }

            var roomTypes = new Dictionary<Vector2Int, RoomType>();
            var interior = new List<Vector2Int>(path);
            if (interior.Count > 1) interior.RemoveAt(0);
            if (interior.Count > 0) interior.RemoveAt(interior.Count - 1);

            // locked rooms
            for (int i = 0; i < lockedRoomsPerFloor && interior.Count > 0; i++)
            {
                int idx = Random.Range(0, interior.Count);
                Vector2Int coord = interior[idx];
                if (ManhattanDistance(coord, entry) >= minLockDistance)
                {
                    roomTypes[coord] = RoomType.Locked;
                    interior.RemoveAt(idx);
                }
            }
            // shops
            for (int i = 0; i < shopsPerFloor && interior.Count > 0; i++)
            {
                int idx = Random.Range(0, interior.Count);
                Vector2Int coord = interior[idx];
                roomTypes[coord] = RoomType.Shop;
                interior.RemoveAt(idx);
            }

            foreach (var coord in interior)
            {
                if (Random.value < treasureChance)
                    roomTypes[coord] = RoomType.Treasure;
                else
                    roomTypes.TryAdd(coord, RoomType.Monster);
            }

            foreach (var cell in adj.Keys)
            {
                RoomType type = RoomType.Monster;
                if (cell == entry)
                    type = floorNumber == 1 ? RoomType.Safe : RoomType.StaircaseDown;
                else if (cell == finalExit)
                    type = isLast ? RoomType.Exit : RoomType.StaircaseUp;
                else if (roomTypes.TryGetValue(cell, out RoomType rt))
                    type = rt;

                var room = new RoomData { Coord = cell, Type = type };
                foreach (var nb in adj[cell])
                    room.Connections.Add(nb);
                floor.Rooms.Add(room);
            }

            return floor;
        }

        private Dictionary<Vector2Int, HashSet<Vector2Int>> CarvePerfectMaze(int w, int h, float bias)
        {
            var adj = new Dictionary<Vector2Int, HashSet<Vector2Int>>();
            for (int x = 0; x < w; x++)
                for (int y = 0; y < h; y++)
                    adj[new Vector2Int(x, y)] = new HashSet<Vector2Int>();

            var stack = new List<Vector2Int>();
            var visited = new HashSet<Vector2Int>();
            Vector2Int start = new Vector2Int(0, 0);
            visited.Add(start);
            stack.Add(start);
            while (stack.Count > 0)
            {
                var cur = stack[stack.Count - 1];
                var neighbors = new List<Vector2Int>();
                foreach (var dir in Directions)
                {
                    var nb = cur + dir;
                    if (nb.x >= 0 && nb.x < w && nb.y >= 0 && nb.y < h && !visited.Contains(nb))
                        neighbors.Add(nb);
                }
                if (neighbors.Count > 0)
                {
                    Vector2Int next = Vector2Int.zero;
                    if (stack.Count > 1 && Random.value < bias)
                    {
                        var prev = stack[stack.Count - 2];
                        var delta = cur - prev;
                        foreach (var nb in neighbors)
                        {
                            if (nb - cur == delta)
                            {
                                next = nb;
                                break;
                            }
                        }
                    }
                    if (next == Vector2Int.zero || !neighbors.Contains(next))
                        next = neighbors[Random.Range(0, neighbors.Count)];
                    visited.Add(next);
                    adj[cur].Add(next);
                    adj[next].Add(cur);
                    stack.Add(next);
                }
                else
                {
                    stack.RemoveAt(stack.Count - 1);
                }
            }
            return adj;
        }

        private void AddRandomLoops(Dictionary<Vector2Int, HashSet<Vector2Int>> adj, float chance)
        {
            foreach (var cell in new List<Vector2Int>(adj.Keys))
            {
                foreach (var dir in new[] { Vector2Int.right, Vector2Int.up })
                {
                    var nb = cell + dir;
                    if (adj.ContainsKey(nb) && !adj[cell].Contains(nb))
                    {
                        if (Random.value < chance)
                        {
                            adj[cell].Add(nb);
                            adj[nb].Add(cell);
                        }
                    }
                }
            }
        }

        private List<Vector2Int> BFSPath(Dictionary<Vector2Int, HashSet<Vector2Int>> adj, Vector2Int start, Vector2Int end)
        {
            var dq = new Queue<List<Vector2Int>>();
            dq.Enqueue(new List<Vector2Int> { start });
            var seen = new HashSet<Vector2Int> { start };
            while (dq.Count > 0)
            {
                var p = dq.Dequeue();
                var node = p[p.Count - 1];
                if (node == end)
                    return p;
                foreach (var nb in adj[node])
                {
                    if (!seen.Contains(nb))
                    {
                        seen.Add(nb);
                        var np = new List<Vector2Int>(p) { nb };
                        dq.Enqueue(np);
                    }
                }
            }
            return new List<Vector2Int> { start, end };
        }

        private static Vector2Int ChooseFarCoordinate(int w, int h, int minDist, float edgeBias)
        {
            var all = new List<Vector2Int>();
            for (int x = 0; x < w; x++)
                for (int y = 0; y < h; y++)
                    if (Mathf.Abs(x) + Mathf.Abs(y) >= minDist)
                        all.Add(new Vector2Int(x, y));
            if (all.Count == 0)
                return new Vector2Int(w - 1, h - 1);

            var outer = new List<Vector2Int>();
            foreach (var c in all)
            {
                if (c.x < w / 3 || c.x >= w - w / 3 || c.y < h / 3 || c.y >= h - h / 3)
                    outer.Add(c);
            }
            if (outer.Count > 0 && Random.value < edgeBias)
                return outer[Random.Range(0, outer.Count)];
            return all[Random.Range(0, all.Count)];
        }

        private static int ManhattanDistance(Vector2Int a, Vector2Int b)
        {
            return Mathf.Abs(a.x - b.x) + Mathf.Abs(a.y - b.y);
        }

        private static readonly Vector2Int[] Directions =
        {
            Vector2Int.right,
            Vector2Int.left,
            Vector2Int.up,
            Vector2Int.down
        };
    }
}
