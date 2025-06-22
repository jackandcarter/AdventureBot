using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using Evolution.Dungeon;

namespace Evolution.UI
{
    /// <summary>
    /// Basic visualization of a dungeon floor. Generates simple icons for each
    /// room and highlights the player's current location.
    /// </summary>
    public class MapUI : MonoBehaviour
    {
        [SerializeField] private RectTransform mapRoot;
        [SerializeField] private GameObject roomPrefab;
        [SerializeField] private Color exploredColor = Color.gray;
        [SerializeField] private Color currentColor = Color.yellow;

        private readonly List<GameObject> spawned = new();

        public void DrawFloor(FloorData floor, Vector2Int current)
        {
            Clear();
            if (floor == null || mapRoot == null || roomPrefab == null)
                return;
            foreach (var room in floor.Rooms)
            {
                var go = Instantiate(roomPrefab, mapRoot);
                var image = go.GetComponent<Image>();
                if (image != null)
                    image.color = room.Coord == current ? currentColor : exploredColor;
                go.transform.localPosition = new Vector3(room.Coord.x * 32f, room.Coord.y * 32f, 0f);
                spawned.Add(go);
            }
        }

        public void Clear()
        {
            foreach (var go in spawned)
                if (go != null)
                    Destroy(go);
            spawned.Clear();
        }
    }
}

